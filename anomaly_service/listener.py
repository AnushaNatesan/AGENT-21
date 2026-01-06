import os
import asyncio
import django
from supabase import create_async_client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anomaly_service.settings")
django.setup()

from core.views import run_ml_proactive_agent, notify

SUPABASE_URL = "<ENTER_SUPABASE_URL>"
SUPABASE_KEY = "<ENTER_SUPABASE_API_KEY>"


# ---------- real async worker ----------
async def handle_change(payload):
    print("🔔 Supabase event received")
    print("📨 Payload:", payload)

        # offload heavy sync function
    actions = await asyncio.to_thread(run_ml_proactive_agent)

    print("\n🚨 Anomaly actions:")
    for a in actions:
        print(a)

            # also offload notification functions
        await asyncio.to_thread(notify, a, actions)


    print("---------------------------------------------------\n")



# ---------- callback expected by supabase client (MUST BE SYNC) ----------
def on_db_change(payload):
    # schedule async task without blocking realtime loop
    asyncio.create_task(handle_change(payload))


async def main():
    client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    print("👂 Subscribing to realtime database changes…")

    tables = [
        "deliveries",
        "revenue_stats",
        "products",
        "factory_performance",
        "review_sentiments",
        "product_reviews",
        "weather_conditions",
        "pricing_history",
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

