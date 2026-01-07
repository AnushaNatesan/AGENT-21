from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from supabase import create_client

SUPABASE_URL = <URL>
SUPABASE_KEY = <KEY>
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@csrf_exempt
def insert_agent_log(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)

    supabase.table("agent_logs").insert({
        "user_id": data.get("user_id"),
        "user_query": data.get("user_query"),
        "thought_process": data.get("thought_process"),
        "action_taken": data.get("action_taken")
    }).execute()

    return JsonResponse({"status": "success"})

