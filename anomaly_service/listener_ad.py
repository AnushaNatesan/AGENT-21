import os
import asyncio
import django
from supabase import create_async_client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anomaly_service.settings")
django.setup()

from core.views import automate_ad,advertise

SUPABASE_URL = "<ENTER_SUPABASE_URL>"
SUPABASE_KEY = "<ENTER_SUPABASE_APIKEY>"


# ---------- real async worker ----------
async def handle_change(payload):
    print("🔔 Supabase event received")
    print("📨 Payload:", payload)

        # offload heavy sync function
    product = await asyncio.to_thread(automate_ad)

    print("\nProduct Details")
    print(product)

            # also offload notification functions
    #await asyncio.to_thread(notify, product)


    print("---------------------------------------------------\n")



# ---------- callback expected by supabase client (MUST BE SYNC) ----------
def on_db_change(payload):
    # schedule async task without blocking realtime loop
    asyncio.create_task(handle_change(payload))


async def main():
    client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)

    print("👂 Subscribing to realtime database changes…")

    tables = [
        "products"
    ]

    for t in tables:
        (
            await client.channel(f"{t}_changes")
            .on_postgres_changes(
                event="INSERT",
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

