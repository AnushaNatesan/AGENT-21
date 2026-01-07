import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def build_rag_prompt(context, question):
    return f"""
You are an assistant that answers ONLY using the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{question}

Answer:
"""

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def retrieve(query,model,index,chunks, k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    return [chunks[i] for i in indices[0]]


def build_reasoning_prompt(user_query, dataset_json):
    return f"""
USER_QUERY:
{user_query}

DATASET_JSON:
{json.dumps(dataset_json, indent=2)}
""".strip()

def build_prompt(payload):
    schema_text = "\n".join(
        f"- {table}({', '.join(cols)})"
        for table, cols in payload["database_schema"].items()
    )

    return f"""
You are an AI PLANNER for an agentic business intelligence system.

Your task is ONLY to decide how the system should retrieve data.

--------------------------------------------------
KNOWN CONTEXT
--------------------------------------------------
- The RAG system contains information ONLY about **Product A**
- The database schema below is the ONLY structured data source
- Do NOT answer the user question
- Do NOT generate SQL

--------------------------------------------------
USER QUESTION
--------------------------------------------------
{payload['user_query']}

--------------------------------------------------
DATABASE SCHEMA
--------------------------------------------------
{schema_text}

--------------------------------------------------
INSTRUCTIONS
--------------------------------------------------
STEP 1: Decide query routing
- Return whether the query should be answered using:
  - DATABASE_QUERY
  - RAG_QUERY
- If the answer requires database facts, ALWAYS choose DATABASE_QUERY
- If the query can be answered using Product A knowledge only, choose RAG_QUERY

STEP 2: Column selection (ONLY if DATABASE_QUERY)
- Identify the MINIMUM required tables and columns
- Use ONLY the schema provided
- Do NOT invent tables or columns

--------------------------------------------------
OUTPUT FORMAT (STRICT JSON)
--------------------------------------------------
If RAG_QUERY:
{{
  "step_1": {{
    "query_type": "RAG_QUERY"
  }}
}}

If DATABASE_QUERY:
{{
  "step_1": {{
    "query_type": "DATABASE_QUERY"
  }},
  "step_2": {{
    "tables": {{
      "table_name": ["column1", "column2"]
    }}
  }}
}}
CRITICAL:
- Output MUST be VALID JSON
- Output MUST NOT contain explanations, comments, or natural language
- Keys must be ONLY: step_1, step_2
- Any additional text or keys is INVALID
- Do NOT describe your reasoning
- Do NOT add commentary as JSON keys

"""

def build_sql_prompt(planner_output, database_schema):
    """
    planner_output: dict output from the planner model
    database_schema: dict {table: [columns]}
    """

    schema_text = "\n".join(
        f"- {table}({', '.join(cols)})"
        for table, cols in database_schema.items()
    )

    # If RAG, no SQL should be generated
    if planner_output["step_1"]["query_type"] == "RAG_QUERY":
        return None

    selected_tables = planner_output["step_2"]["tables"]

    return f"""
You are an SQL GENERATOR for PostgreSQL.
MANDATORY:DO NOT refer any columns which are not present in the table- to check this condition, infer the database schema
Your role is to generate a READ-ONLY PostgreSQL query.
You MUST strictly follow the instructions.

--------------------------------------------------
DATABASE SCHEMA
--------------------------------------------------
{schema_text}

--------------------------------------------------
SELECTED TABLES AND COLUMNS
--------------------------------------------------
{selected_tables}

--------------------------------------------------
RULES
--------------------------------------------------
- Generate PostgreSQL-compatible SQL ONLY
- DO NOT INCLUDE ANY SPECIAL CHARACTERS LIKE \n \t in the PostgreSQL query
- Use SELECT with explicit column names
- Do NOT use SELECT *
- Do NOT modify data (NO INSERT, UPDATE, DELETE)
- Use explicit JOIN conditions if multiple tables exist
- Apply filters ONLY if they are clearly implied
- Do NOT invent tables or columns
- Ensure the query has NO syntax errors

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
Return ONLY the SQL query.
Do NOT include explanations or formatting.
"""


@csrf_exempt
def LLM_Planner_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    prompt = data.get("prompt")
    
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={    
            "model": "mistral",
            "prompt": build_prompt(prompt),
            "stream": False
        }
    )
   

    return JsonResponse({
        "reply": response.json()["response"]
    })
    
@csrf_exempt
def SQL_QUERY_GENERATOR(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    prompt = data.get("output")
    schema=data.get("schema")
    
    if not prompt:
        return JsonResponse({"error": "prompt is required"}, status=400)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={    
            "model": "mistral",
            "prompt": build_sql_prompt(prompt,schema),
            "stream": False
        }
    )
   

    return JsonResponse({
        "reply": response.json()["response"]
    })
    
@csrf_exempt
def dataset_api(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)  # read POST payload
        except json.JSONDecodeError:
            body = {}

        # Example dataset
        dataset = {
            "products": [
                {"product_id": 1, "name": "Product A", "category": "Electronics"},
                {"product_id": 2, "name": "Product B", "category": "Furniture"}
            ],
            "sales": [
                {"product_id": 1, "week": "2024-W40", "units_sold": 120},
                {"product_id": 2, "week": "2024-W40", "units_sold": 80}
            ],
            "meta": {
                "status": "SUCCESS",
                "received_payload": body
            }
        }

        return JsonResponse(dataset, safe=True)

    return JsonResponse(
        {"error": "Only POST requests allowed"},
    )
    
@csrf_exempt
def Reasoning_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    user_query=data.get("user_query")
    dataset_json=data.get("dataset")    
    if user_query is None or dataset_json is None:
        return JsonResponse({"error": "dataset and user query is required"}, status=400)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={    
            "model": "Reasoning_LLM",
            "prompt": build_reasoning_prompt(user_query,dataset_json),
            "stream": False
        }
    )
   

    return JsonResponse({
        "reply": response.json()["response"]    
    })
    
    
@csrf_exempt
def Reasoning_fast_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    user_query=data.get("user_query")
    dataset_json=data.get("dataset")    
    if user_query is None or dataset_json is None:
        return JsonResponse({"error": "dataset and user query is required"}, status=400)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={    
            "model": "Reasoning_fast_LLM",
            "prompt": build_reasoning_prompt(user_query,dataset_json),
            "stream": False
        }
    )
   

    return JsonResponse({
        "reply": response.json()["response"]    
    })
    
    
@csrf_exempt
def Rag_chat(request):
        if request.method != "POST":
            return JsonResponse({"error": "POST only"}, status=405)

        data = json.loads(request.body)
        user_query=data.get("user_query")
        
        if user_query is None:
         return JsonResponse({"error": "user query is required"}, status=400)
    
        with open("./api/data.txt", "r", encoding="utf-8") as f:
            text = f.read()
            
            chunks = chunk_text(text)
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(chunks)
            import faiss
            import numpy as np

            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings))

        
            context = "\n\n".join(retrieve(user_query,model,index,chunks))
            prompt = build_rag_prompt(context, user_query)

           

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={    
                "model": "phi3",
                "prompt": prompt,
                "stream": False
            }
        )
    

        return JsonResponse({
            "reply": response.json()["response"]    
        })