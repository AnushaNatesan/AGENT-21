# # views_scenario.py
# from django.shortcuts import render
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# import json

# @csrf_exempt
# def scenario_simulator(request):
#     # 👉 GET → open the War Room UI
#     if request.method == "GET":
#         return render(request, "war_room.html")

#     # 👉 POST → API call from JS
#     if request.method == "POST":
#         data = json.loads(request.body)
#         question = data.get("question", "")

#         # TEMP mock response (replace with agent logic later)
#         return JsonResponse({
#             "war_room_report": "<discussion>[CEO]: We need to act fast</discussion>"
#         })

#     return JsonResponse({"error": "Invalid request"}, status=400)
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .supabase_client import fetch_table
from .gemini_service import model
import json

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def scenario_simulator(request):
    try:
        question = request.data.get("question")

        if not question:
            return Response({"error": "Question required"}, status=400)

        # 1) fetch database tables
        weather = fetch_table("weather_conditions")
        factory = fetch_table("factory_performance")
        revenue = fetch_table("revenue_stats")
        deliveries = fetch_table("deliveries")
        products = fetch_table("products")

        # 2) structured long-context prompt
        prompt = f"""
    You are running an EXECUTIVE WAR ROOM SCENARIO SIMULATION.

    User Scenario:
    {question}

    You are given the full company database:

    WEATHER:
    {json.dumps(weather)}

    FACTORY PERFORMANCE:
    {json.dumps(factory)}

    REVENUE AND MARKET SHARE:
    {json.dumps(revenue)}

    DELIVERIES:
    {json.dumps(deliveries)}

    PRODUCTS:
    {json.dumps(products)}

    SIMULATE A PANEL DISCUSSION between the following personas:

    1) Chief Risk Officer
    2) Head of Logistics
    3) Head of Factory Operations
    4) Chief Revenue Officer
    5) Head of Customer Experience

    Each persona must:
    - speak in very very short and concise sentences, max character limit 50
    - reference data when relevant
    - disagree and collaborate naturally
    - propose actions from their perspective

    AFTER THE DISCUSSION, produce a final structured report.

    OUTPUT FORMAT (IMPORTANT):

    <discussion>
    [Chief Risk Officer]: ...
    [Head of Logistics]: ...
    [Head of Factory Operations]: ...
    [Chief Revenue Officer]: ...
    [Customer Experience Head]: ...
    </discussion>

    <final_report_json>
    {{
     "executive_summary": "...",
     "top_risks": ["..."],
     "affected_products": ["..."],
     "delivery_impact": "...",
     "revenue_impact": "...",
     "factory_impact": "...",
     "customer_impact": "...",
     "mitigation_plan": ["..."],
     "automations_to_trigger": ["..."]
    }}
    </final_report_json>
    """

        result = model.generate_content(prompt)

        return Response({
            "status": "simulated",
            "scenario_question": question,
            "simulation": result.text
        })
    except Exception as e:
        print(f"Scenario Simulator Error: {str(e)}")
        return Response({"error": str(e)}, status=500)
