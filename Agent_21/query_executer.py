import json
import time
import requests
import numpy as np
import pandas as pd
from supabase import create_client
from django.http import JsonResponse
from django.utils import timezone
from sklearn.ensemble import IsolationForest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .agent_brain import AgentBrain

# Initialize Agent Brain
agent_brain = AgentBrain()

# ===== CONFIGURATION =====
SUPABASE_URL = "https://izfvsrkgpdpkxmhqyfip.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6ZnZzcmtncGRwa3htaHF5ZmlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTc5NzMsImV4cCI6MjA4MzAzMzk3M30.7l90E0rIZeeB0hRst8ca18ZQmQBumQXlOaJEQxWFql0"

# Initialize Supabase Client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Headers for REST fallback
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------- SENSING LAYER (UTILITIES) ----------

def fetch_supabase(table):
    """Fetches full table data for ML context."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()

def auto_simulate_anomaly():
    """Injects test anomalies across all 5 business pillars."""
    print("🤖 AUTO-SIMULATOR: Injecting multi-pillar anomalies...")
    
    try:
        # 1. REVENUE: Unusual Drop (Product #3)
        supabase.table('revenue_stats').insert({
            "product_id": 3, "total_revenue": 50.0, "stats_id": 9999,
            "calculated_for": str(timezone.now().date())
        }).execute()

        # 2. LOGISTICS: Weather Risk (Hurricane/High Severity)
        # This will be flagged by your IQR-based weather risk detector
        supabase.table('weather_conditions').insert({
            "weather_id": 9999,
            "observed_location": "Primary Distribution Hub",
            "weather_type": "Hurricane Warning",
            "severity_level": 9.5, # High severity to trigger anomaly
            "observed_at": str(timezone.now())
        }).execute()

        # 3. FACTORY: Throughput Drop & Backlog Spike
        # This triggers the 'factory_issue' anomaly detection
        supabase.table('factory_performance').insert({
            "factory_id": 9999,
            "throughput_percentage": 15.0, # Critically low
            "backlog_units": 5000,         # High backlog
            "units_produced": 120,
            "recorded_at": str(timezone.now())
        }).execute()

        # 4. INVENTORY: Negative Stock
        supabase.table('products').update({"current_stock": -5}).eq('product_id', 3).execute()

    except Exception as e:
        print(f"⚠️ Auto-simulation failed: {e}")

# ---------- REASONING ENGINE (ML ANOMALY DETECTION) ----------

def detect_revenue_anomalies_ml():
    """Identifies revenue spikes or drops using Isolation Forest."""
    rows = fetch_supabase("revenue_stats")
    if not rows: return []
    
    revenue = np.array([float(r["total_revenue"]) for r in rows]).reshape(-1, 1)
    model = IsolationForest(contamination="auto", random_state=42)
    preds = model.fit_predict(revenue)
    
    normal_values = [float(rows[i]["total_revenue"]) for i, p in enumerate(preds) if p == 1]
    center = np.median(normal_values) if normal_values else 0
    
    anomalies = []
    for i, p in enumerate(preds):
        if p == -1:
            r = rows[i]
            val = float(r["total_revenue"])
            msg = "Unusual spike in revenue detected" if val > center else "Unusual drop in revenue detected"
            anomalies.append({
                "type": "revenue_anomaly",
                "stats_id": r["stats_id"],
                "value": val,
                "message": msg
            })
    return anomalies

def run_ml_proactive_agent():
    """Consolidates all detected anomalies into alerts."""
    actions = []
    actions.extend(detect_revenue_anomalies_ml())
    return actions

# ---------- ACTION LAYER (AUTOMATED ENDPOINTS) ----------

@csrf_exempt
@require_POST
def agent_intelligence_view(request):
    """
    Fully Automated: Inject -> Sense -> Think -> Reset.
    """
    print("\n" + "="*70 + "\n🚀 AUTOMATED AGENT CYCLE STARTED\n" + "="*70)
    try:
        # 1. AUTO-SET: Inject the anomaly for the demo
        auto_simulate_anomaly()

        # 2. SENSE: Execute the user's query
        data = json.loads(request.body)
        sql_query = data.get('query', '').strip().rstrip(';')
        
        start_time = time.time()
        response = supabase.rpc('execute_any_query', {'sql_text': sql_query}).execute()
        execution_time = round((time.time() - start_time) * 1000, 2)

        # 3. THINK: Run ML Reasoning (Flags the 50.0 value)
        anomalies = run_ml_proactive_agent()

        # 4. REASON: LLM analysis of the top anomaly if available
        reasoning_summary = "No significant anomalies to analyze."
        if anomalies:
            # Fetch context for the first anomaly (as an example)
            # In a real scenario, the agent would decide what context to fetch
            context = {
                "recent_weather": fetch_supabase("weather_conditions")[:5],
                "factory_status": fetch_supabase("factory_performance")[:5]
            }
            analysis = agent_brain.reason_about_anomaly(anomalies[0], context=context)
            reasoning_summary = analysis if isinstance(analysis, dict) else {"message": analysis}

        # 5. AUTO-RESET: Cleanup demo records immediately
        print("🧹 AUTO-RESET: Cleaning up demo records...")
        supabase.table('revenue_stats').delete().eq('stats_id', 9999).execute()
        
        return JsonResponse({
            "success": True,
            "demo_mode": "Auto-Simulation Active",
            "query_results": response.data,
            "active_anomalies": anomalies,
            "agent_reasoning": reasoning_summary,
            "execution_time_ms": execution_time,
            "message": "Sensing, Reasoning, and Auto-Cleanup complete."
        })
    except Exception as e:
        # Emergency Cleanup on failure
        supabase.table('revenue_stats').delete().eq('stats_id', 9999).execute()
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def agent_rca_view(request):
    """
    Agentic Root Cause Analysis (RCA)
    Perform deep analysis on a specific anomaly using LLM tools.
    """
    try:
        data = json.loads(request.body)
        anomaly = data.get('anomaly')
        
        # Step 1: Agent decides what info it needs
        # For now, we fetch some basic context
        context = {
            "weather": fetch_supabase("weather_conditions"),
            "factory": fetch_supabase("factory_performance"),
            "revenue": fetch_supabase("revenue_stats")
        }
        
        # Step 2: Reason
        analysis = agent_brain.reason_about_anomaly(anomaly, context=context)
        
        return JsonResponse({
            "success": True,
            "anomaly": anomaly,
            "analysis": analysis
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def reset_environment(request):
    """Restores all tables to a healthy baseline."""
    try:
        supabase.table('revenue_stats').delete().eq('stats_id', 9999).execute()
        supabase.table('weather_conditions').delete().eq('weather_id', 9999).execute()
        supabase.table('factory_performance').delete().eq('factory_id', 9999).execute()
        supabase.table('products').update({"current_stock": 50}).eq('product_id', 3).execute()
        
        return JsonResponse({"success": True, "message": "Full system reset complete."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)