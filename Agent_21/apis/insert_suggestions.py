"""
Simple API to insert JSON into suggestion_logs table
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from supabase import create_client
import os

# Supabase config
SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"

# Initialize client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_and_parse_json(json_str):
    """
    Clean JSON string and parse it
    Handles: \n, \t, \r, escaped quotes, and + signs before numbers
    """
    # First, replace newlines and tabs with spaces
    cleaned = json_str.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
    
    # Handle escaped versions too (just in case)
    cleaned = cleaned.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', ' ')
    
    # Handle escaped quotes - replace \" with "
    cleaned = cleaned.replace('\\"', '"')
    
    # FIX THE MAIN ISSUE: Remove + signs before numbers (e.g., +10 → 10)
    # This regex finds patterns like ": +10" or ":  +5.5" and removes the +
    cleaned = re.sub(r':\s*\+(\d+(?:\.\d+)?)', r': \1', cleaned)
    
    # Also fix any stray + signs at the beginning of number values
    cleaned = re.sub(r'"\s*:\s*\+', '": ', cleaned)
    
    # Remove extra spaces (clean up)
    cleaned = ' '.join(cleaned.split())
    
    # Parse the cleaned JSON
    return json.loads(cleaned)

@csrf_exempt
def insert_suggestion(request):
    """
    POST /api/suggestions/insert/
    
    Accepts two formats:
    
    Format 1 (with 'query' wrapper):
    {
        "query": "{\"diagnosis\": \"...\", \"recommended_actions\": {...}, \"confidence\": 90}"
    }
    
    Format 2 (direct JSON):
    {
        "diagnosis": "...",
        "recommended_actions": {...},
        "confidence": 90
    }
    """
    
    if request.method != 'POST':
        return JsonResponse({
            "success": False,
            "error": "Only POST method allowed"
        }, status=405)
    
    try:
        # Get the raw request body
        raw_body = request.body.decode('utf-8')
        print(f"📝 Raw request body received (first 500 chars):")
        print(raw_body[:500])
        
        # Parse the outer JSON
        request_data = json.loads(raw_body)
        
        # Determine which format we're dealing with
        if "query" in request_data:
            print("📝 Detected 'query' format")
            # Format 1: JSON string inside "query" field
            query_str = request_data["query"]
            print(f"📝 Query string to clean (first 500 chars):")
            print(query_str[:500])
            
            # Clean and parse the inner JSON
            suggestion_data = clean_and_parse_json(query_str)
            
        elif "diagnosis" in request_data:
            print("📝 Detected direct JSON format")
            # Format 2: Direct JSON object
            suggestion_data = request_data
            
        else:
            return JsonResponse({
                "success": False,
                "error": "Request must contain either 'query' or 'diagnosis' field"
            }, status=400)
        
        print(f"✅ Successfully parsed suggestion data:")
        print(json.dumps(suggestion_data, indent=2))
        
        # Insert into table
        response = supabase.table('suggestion_logs').insert({
            "suggestion_data": suggestion_data
        }).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0]['id']
            print(f"✅ Success! Inserted with ID: {inserted_id}")
            return JsonResponse({
                "success": True,
                "id": inserted_id,
                "message": "Suggestion inserted successfully"
            })
        else:
            print("❌ Insert failed - no data returned")
            return JsonResponse({
                "success": False,
                "error": "Failed to insert data"
            }, status=500)
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {str(e)}")
        print(f"❌ Error at position: {e.pos}")
        
        # Try to show more context for debugging
        try:
            if 'cleaned' in locals():
                start = max(0, e.pos - 100)
                end = min(len(cleaned), e.pos + 100)
                print(f"❌ Problem area in cleaned string: ...{cleaned[start:end]}...")
                print(f"❌ Character at error: '{cleaned[e.pos:e.pos+20]}'")
        except:
            pass
            
        return JsonResponse({
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }, status=400)
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, status=500)