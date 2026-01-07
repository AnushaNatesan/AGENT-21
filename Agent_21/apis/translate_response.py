import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from deep_translator import GoogleTranslator


@csrf_exempt
def translate_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)

        response_text = data.get("response", "").strip()
        target_language = data.get("language", "").strip()

        if not response_text:
            return JsonResponse(
                {"error": "response is required"},
                status=400
            )

        if not target_language:
            return JsonResponse(
                {"error": "language is required"},
                status=400
            )

        # If target language is English, no translation needed
        if target_language == "en":
            return JsonResponse({
                "original_response": response_text,
                "translated_response": response_text,
                "target_language": "en",
                "was_translated": False
            })

        # Translate response back to target language
        translated = GoogleTranslator(
            source="en",
            target=target_language
        ).translate(response_text)

        return JsonResponse({
            "original_response": response_text,
            "translated_response": translated,
            "target_language": target_language,
            "was_translated": True
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
