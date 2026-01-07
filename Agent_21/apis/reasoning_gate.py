import json
import time
import spacy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# load spacy model
nlp = spacy.load("en_core_web_sm")

REASONING_TRIGGERS = {
    "why",
    "explain",
    "reason",
    "cause",
    "caused",
    "analysis",
    "analyze",
    "insight",
    "insights",
    "recommend",
    "recommendation",
    "predict",
    "prediction",
    "improve",
    "reduce",
    "increase",
    "how"
}


def classify_reasoning(query: str) -> dict:
    start_time = time.time()
    doc = nlp(query.lower())

    # Linguistic reasoning detection
    for token in doc:
        if token.lemma_ in REASONING_TRIGGERS:
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "should_reason": "YES",
                "confidence": 0.9,
                "response_time_ms": latency
            }

    # Causal / interrogative structure
    if "?" in query and any(tok.dep_ in {"advmod", "mark"} for tok in doc):
        latency = round((time.time() - start_time) * 1000, 2)
        return {
            "should_reason": "YES",
            "confidence": 0.75,
            "response_time_ms": latency
        }

    latency = round((time.time() - start_time) * 1000, 2)
    return {
        "should_reason": "NO",
        "confidence": 0.8,
        "response_time_ms": latency
    }


@csrf_exempt
def reasoning_gate_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        payload = json.loads(request.body)
        query = payload.get("query", "").strip()

        if not query:
            return JsonResponse(
                {"error": "user_query is required"},
                status=400
            )

        result = classify_reasoning(query)
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON input"},
            status=400
        )

