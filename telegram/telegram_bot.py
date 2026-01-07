from telegram import Update
import json
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import requests

BOT_TOKEN = "8432197235:AAHTg4ieuQM0lrjEDmPj0NkXll0xP6du8ZY"

# This function is called whenever user sends a message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text

    # Call your API
    api_response = requests.post(
        "http://localhost:3000/agent/query",
        json={
  "user_query": user_query,
  "rag_status": "has data about Product A",
  "database_schema": {
    "products": [
      "product_id",
      "product_name",
      "category",
      "sub_category",
      "brand",
      "lifecycle_stage",
      "is_active",
      "current_stock",
      "safety_stock_level",
      "weight_kg",
      "dimensions_cm",
      "fragile",
      "shelf_life_days",
      "min_order_qty",
      "max_order_qty",
      "reorder_priority",
      "requires_cold_chain",
      "hazardous",
      "launch_date",
      "discontinued_date"
    ],
    "pricing_history": [
      "pricing_id",
      "product_id",
      "price",
      "currency",
      "start_date",
      "end_date"
    ],
    "customers": [
      "customer_id",
      "name",
      "email",
      "is_vip",
      "customer_segment"
    ],
    "product_reviews": [
      "review_id",
      "product_id",
      "customer_id",
      "rating",
      "review_text",
      "is_verified_purchase",
      "review_date"
    ],
    "review_sentiments": [
      "sentiment_id",
      "review_id",
      "sentiment_score",
      "sentiment_label",
      "detected_issues",
      "analyzed_at"
    ],
    "weather_conditions": [
      "weather_id",
      "observed_location",
      "weather_type",
      "severity_level",
      "observed_at"
    ],
    "deliveries": [
      "delivery_id",
      "order_id",
      "delivery_status",
      "delivery_priority",
      "address_of_delivery",
      "location_zone",
      "weather_impact_score",
      "promised_delivery_date",
      "actual_delivery_date",
      "last_updated"
    ],
    "factory_performance": [
      "factory_id",
      "factory_name",
      "location_zone",
      "max_daily_capacity",
      "performance_date",
      "units_produced",
      "throughput_percentage",
      "backlog_units",
      "strike_flag",
      "holiday_flag",
      "recorded_at"
    ],
    "revenue_analytics": [
      "analytics_id",
      "period_start_date",
      "period_type",
      "gross_revenue",
      "net_revenue",
      "total_tax",
      "target_revenue",
      "attainment_percentage",
      "top_performing_category",
      "anomaly_detected",
      "recorded_at"
    ],
    "revenue_stats": [
      "stats_id",
      "product_id",
      "total_units_sold",
      "total_revenue",
      "total_refunds",
      "revenue_share_percent",
      "unit_share_percent",
      "period",
      "calculated_for",
      "created_at"
    ],
    "agent_logs": [
      "log_id",
      "event_type",
      "thought_process",
      "action_taken",
      "pii_masked",
      "created_at"
    ]
  }
}
    )

    # Extract API output
    result = (api_response.json())["answer"]
    cleaned = result.strip().strip('"')

    # 2️⃣ Remove markdown fences
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # 3️⃣ Parse JSON
    data = json.loads(cleaned)

    # 4️⃣ Extract answer
    answers = data["answer"]

    print(answers)
    
    # or .json()["answer"]

    # Send reply back to user
    await update.message.reply_text(answers)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
