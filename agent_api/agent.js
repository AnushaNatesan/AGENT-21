import express from "express";
import cors from "cors";
import fetch from "node-fetch";

function extractPlannerJSON(raw) {
  try {
    // Case 1: planner returned JSON directly
    const parsed = JSON.parse(raw);
    if (parsed.step_1) return parsed;

    // Case 2: planner wrapped JSON as a string
    if (parsed.reply) {
      const inner = JSON.parse(parsed.reply);
      return inner;
    }

    throw new Error("Planner output missing step_1");
  } catch (err) {
    console.error("❌ Planner JSON invalid:", raw);
    throw new Error("Planner returned invalid JSON");
  }
}


const app = express();

/* ─────────────────────────────
   MIDDLEWARE
───────────────────────────── */

app.use(cors({
  origin: "*",
  methods: ["POST"],
  allowedHeaders: ["Content-Type"]
}));

app.use(express.json());

/* ─────────────────────────────
   MAIN AGENT ENDPOINT
───────────────────────────── */

app.post("/agent/query", async (req, res) => {
  try {
    const { user_query, database_schema, rag_status } = req.body;

    console.log("📥 Incoming Request:", {
      user_query,
      database_schema,
      rag_status
    });

    if (!user_query || !database_schema) {
      return res.status(400).json({ error: "user_query and database_schema are required" });
    }

    /* ─────────────────────────────
       1️⃣ REASONING GATE
    ───────────────────────────── */

    console.log("➡️ Calling Reasoning Gate...");

    const rgRes = await fetch("<IP_FOR_APIENDPOINT>/api/reasoning_gate/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: user_query })
    });

    console.log("⬅️ Reasoning Gate Status:", rgRes.status);

    const rgRaw = await rgRes.text();
    console.log("🧠 Reasoning Gate Raw Response:", rgRaw);

    const rgData = JSON.parse(rgRaw);
    console.log("🧠 Reasoning Gate Parsed:", rgData);

    /* ─────────────────────────────
       2️⃣ PLANNER
    ───────────────────────────── */

    console.log("➡️ Calling Planner...");

    const plannerRes = await fetch("http://localhost:8000/planner/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: {
          user_query,
          rag_status,
          database_schema
        }
      })
    });

    console.log("⬅️ Planner Status:", plannerRes.status);

      const plannerRaw = await plannerRes.text();
    console.log("📋 Planner Raw:", plannerRaw);

    const plan = extractPlannerJSON(plannerRaw);
    console.log("📋 Planner Parsed:", plan);

    /* ─────────────────────────────
       3️⃣ RAG PATH
    ───────────────────────────── */

    if (plan.step_1.query_type === "RAG_QUERY") {
      console.log("📘 Routing to RAG...");

      const ragRes = await fetch("http://localhost:8000/rag/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_query })
      });

      console.log("⬅️ RAG Status:", ragRes.status);

      const ragRaw = await ragRes.text();
      console.log("📘 RAG Raw Response:", ragRaw);

      const ragData = JSON.parse(ragRaw);
      console.log("📘 RAG Parsed:", ragData);

      return res.json({
        mode: "RAG",
        answer: ragData.reply
      });
    }

    /* ─────────────────────────────
       4️⃣ SQL GENERATOR
    ───────────────────────────── */

    console.log("➡️ Calling SQL Generator...");

    const sqlGenRes = await fetch("http://localhost:8000/sql_generator/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        output:plan,
        schema:database_schema
      })
    });

    console.log("⬅️ SQL Generator Status:", sqlGenRes.status);

    const sqlRaw = await sqlGenRes.json();
    console.log("🧾 SQL Generator Raw Response:", sqlRaw);
    console.log(typeof sqlRaw);
    const sql_query = sqlRaw.reply;
    console.log("🧾 SQL Query:", sql_query);

    if (!sql_query) {
      console.log("⚠️ No SQL query generated");

      return res.json({
        mode: "DATABASE",
        sql_query: null,
        dataset: null,
        answer: null,
        reasoning: rgData.should_reason
      });
    }

    /* ─────────────────────────────
       5️⃣ DATABASE QUERY
    ───────────────────────────── */

    console.log("➡️ Executing Database Query...");

    const dataRes = await fetch("<IP_FOR_APIENDPOINT>/api/query/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: sql_query })
    });

    console.log("⬅️ Database Status:", dataRes.status);

    const dataRaw = await dataRes.text();
    console.log("🗄️ Database Raw Response:", dataRaw);

    const dataset = JSON.parse(dataRaw);
    console.log("🗄️ Database Parsed Dataset:", dataset);

    /* ─────────────────────────────
       6️⃣ REASONING
    ───────────────────────────── */

    const reasoningEndpoint =
      rgData.should_reason === "YES"
        ? "http://localhost:8000/reasoning/"
        : "http://localhost:8000/reasoning_fast/";

    console.log("➡️ Calling Reasoning Model:", reasoningEndpoint);

    const reasoningRes = await fetch(reasoningEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_query,
        dataset
      })
    });

    console.log("⬅️ Reasoning Status:", reasoningRes.status);

    const reasoningRaw = await reasoningRes.text();
    console.log("🧠 Reasoning Raw Response:", reasoningRaw);

    const reasoningData = JSON.parse(reasoningRaw);
    console.log("🧠 Reasoning Parsed:", reasoningData);

    /* ─────────────────────────────
       7️⃣ FINAL RESPONSE
    ───────────────────────────── */

    console.log("✅ Final Agent Response Ready");

    return res.json({
      mode: "DATABASE",
      sql_query,
      dataset,
      answer: reasoningData.reply,
      reasoning: rgData.should_reason
    });

  } catch (err) {
    console.error("❌ AGENT ERROR:", err);

    return res.status(500).json({
      error: "Agent failed",
      message: err.message
    });
  }
});

/* ─────────────────────────────
   SERVER
───────────────────────────── */

app.listen(3000, () => {
  console.log("🚀 Agent API running on http://localhost:3000");
});

