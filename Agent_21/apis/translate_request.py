import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException


@csrf_exempt
def translate_to_english(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()

        if not query:
            return JsonResponse(
                {"error": "query is required"},
                status=400
            )

        # 🔹 Detect language using langdetect
        try:
            detected_language = detect(query)
        except LangDetectException:
            detected_language = "unknown"

        # 🔹 Translate only if not English
        if detected_language != "en":
            translated = GoogleTranslator(
                source="auto",
                target="en"
            ).translate(query)
            was_translated = True
        else:
            translated = query
            was_translated = False

        return JsonResponse({
            "original_query": query,
            "translated_query": translated,
            "detected_language": detected_language,
            "was_translated": was_translated
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
