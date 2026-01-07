import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai


# Configure Gemini
genai.configure(api_key="API_KEY")

model = genai.GenerativeModel("models/gemini-2.5-flash")

@csrf_exempt
def market_survey(request):
    """
    POST API
    Input: Product details JSON
    Output: Market research JSON
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        product_data = json.loads(request.body)

        prompt = f"""
You are a professional market research analyst.

Perform web-based market research for the following product.
Analyze demand, competitors, pricing, risks, and success probability.

Product details:
{json.dumps(product_data, indent=2)}
Do NOT include markdown, comments, or explanations.
Respond ONLY in valid JSON with this structure:

{{
  "market_overview": {{
    "demand_level": "",
    "growth_trend": "",
    "customer_interest_score": 0.0
  }},
  "competitor_analysis": [
    {{
      "brand": "",
      "price_range": "",
      "strengths": [],
      "weaknesses": []
    }}
  ],
  "pricing_insights": {{
    "recommended_price": "",
    "competitive_positioning": ""
  }},
  "success_probability": {{
    "estimated_success_rate": 0.0,
    "confidence_level": "",
    "reasoning": ""
  }},
  "risks": [],
  "recommendations": []
}}
"""

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 5000
            }
        )
        print("Gemini response:", response.text)
        cleaned = response.text.strip().strip("```json").strip("```")
        research_json = json.loads(cleaned)

        return JsonResponse({
            "status": "success",
            "research": research_json
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON from Gemini"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

