import os
import asyncio
from django.http import JsonResponse
import requests
import json
from supabase import create_async_client

def build_suggestor_prompt(anomaly_type: str, anomaly_description: str) -> str:
    """
    Builds the input prompt for the Business Reasoning & Control LLM.
    Returns a JSON string to be sent as the user message.
    """

    prompt = {
        "anomaly_type": anomaly_type,
        "anomaly_description": anomaly_description
    }
    return json.dumps(prompt)

SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "sb_publishable_mXdogYpuflKU5JDneBpQNw_fJfZZjlH"


 
# ---------- real async worker ----------
async def handle_change(payload):
    print("🔔 Supabase event received")
    print("📨 Payload:", payload)
    SQL_Query='SELECT * FROM "Anomaly" ORDER BY anomaly_id DESC LIMIT 1;'

    
    response = requests.post(
        "http://172.16.4.215:8000/api/query/",
        json={    
            "query": SQL_Query,
        }
    )
    print(response)
    res=response.json()
    print(res["data"][0]["type"])
    print(res["data"][0]["description"])
    a_type=res["data"][0]["type"]
    a_description=res["data"][0]["description"]
    
    Suggestor_response = requests.post(
        "http://localhost:11434/api/generate",
        json={    
            "model": "Suggestor",
            "prompt": build_suggestor_prompt(a_type,a_description),
            "stream": False
        }
    )
    
    print(Suggestor_response.json()['response'])
    deliver_response = requests.post(
        "http://172.16.4.215:8000/api/suggestions/insert/",
        json={    
            "query": Suggestor_response.json()['response'],
        }
    )   
    print(deliver_response.json())
    
    print("---------------------------------------------------\n") 



# ---------- callback expected by supabase client (MUST BE SYNC) ----------
def on_db_change(payload):
    # schedule async task without blocking realtime loop
    asyncio.create_task(handle_change(payload))


async def main():
    client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    print("👂 Subscribing to realtime database changes…")

    tables = [
        "Anomaly"
    ]

    for t in tables:
        (
            await client.channel(f"{t}_changes")
            .on_postgres_changes(
                event="*",
                schema="public",
                table=t,
                callback=on_db_change,
            )
            .subscribe()
        )

    print("✅ Listener successfully connected. Waiting for events…")

    await asyncio.Future()


if __name__ == "__main__":
    try:
        # (Windows fix) — ensure compatible policy
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Listener stopped manually")
