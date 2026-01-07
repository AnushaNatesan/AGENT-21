from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from supabase import create_client

SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"
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
