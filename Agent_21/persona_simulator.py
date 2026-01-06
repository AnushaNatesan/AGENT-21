from .supabase_client import fetch_table
from .gemini_service import model
import json


def run_persona(prompt):
    response = model.generate_content(prompt)
    return response.text


def run_war_room_simulation(question):

    # fetch tables once
    weather = fetch_table("weather_conditions")
    factory = fetch_table("factory_performance")
    revenue = fetch_table("revenue_stats")
    deliveries = fetch_table("deliveries")
    products = fetch_table("products")

    shared_context = f"""
BUSINESS DATABASE CONTEXT

WEATHER:
{json.dumps(weather)}

FACTORY PERFORMANCE:
{json.dumps(factory)}

REVENUE:
{json.dumps(revenue)}

DELIVERIES:
{json.dumps(deliveries)}

PRODUCTS:
{json.dumps(products)}
"""

    # ---------- PERSONA 1: Chief Risk Officer ----------
    cro_prompt = f"""
You are the CHIEF RISK OFFICER.

User scenario:
{question}

{shared_context}

TASK: produce a RISK MAP.
Output:
- systemic risks
- regional risks
- severity 1–5
- time sensitivity
"""

    cro_output = run_persona(cro_prompt)

    # ---------- PERSONA 2: Logistics Head ----------
    logistics_prompt = f"""
You are the HEAD OF LOGISTICS.

User scenario:
{question}

{shared_context}

Your focus:
- deliveries at risk
- weather impact on transit
- hubs affected
- rerouting suggestions
"""

    logistics_output = run_persona(logistics_prompt)

    # ---------- PERSONA 3: Factory Ops ----------
    factory_prompt = f"""
You are HEAD OF FACTORY OPERATIONS.

User scenario:
{question}

{shared_context}

Your focus:
- production bottlenecks
- backlog escalation risk
- resource constraints
- contingency manufacturing plan
"""

    factory_output = run_persona(factory_prompt)

    # ---------- PERSONA 4: Chief Revenue Officer ----------
    revenue_prompt = f"""
You are CHIEF REVENUE OFFICER.

User scenario:
{question}

{shared_context}

Your focus:
- revenue risk
- market share impact
- product categories impacted
- margin impact
- short-term vs long-term outlook
"""

    revenue_output = run_persona(revenue_prompt)

    # ---------- PERSONA 5: Customer Experience ----------
    cx_prompt = f"""
You are HEAD OF CUSTOMER EXPERIENCE.

User scenario:
{question}

{shared_context}

Your focus:
- cancellations
- customer sentiment
- refund likelihood
- proactive communication strategy
"""

    cx_output = run_persona(cx_prompt)

    # ---------- FINAL COORDINATOR ----------
    final_prompt = f"""
You are the EXECUTIVE COORDINATOR.

Combine these analyst reports:

Chief Risk Officer:
{cro_output}

Logistics Head:
{logistics_output}

Factory Operations:
{factory_output}

Chief Revenue Officer:
{revenue_output}

Customer Experience Head:
{cx_output}

Produce final output STRICTLY in JSON:

{{
 "executive_summary": "...",
 "key_risks": ["..."],
 "products_at_risk": ["..."],
 "delivery_impact": "...",
 "factory_bottlenecks": "...",
 "financial_forecast": "...",
 "customer_impact": "...",
 "mitigation_plan": [
    "...",
 ],
 "recommended_automations": [
    "..."
 ]
}}
"""

    final = run_persona(final_prompt)

    return final
