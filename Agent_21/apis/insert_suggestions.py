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
SUPABASE_URL = <URL>
SUPABASE_KEY = <KEY>

# Initialize client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_and_parse_json(json_str):
    """
    Clean JSON string and parse it
    Handles: \n, \t, \r, escaped quotes, and + signs before numbers
    """
    cleaned = json_str.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
    cleaned = cleaned.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', ' ')
    cleaned = cleaned.replace('\\"', '"')
    cleaned = re.sub(r':\s*\+(\d+(?:\.\d+)?)', r': \1', cleaned)
    cleaned = re.sub(r'"\s*:\s*\+', '": ', cleaned)
    
    # Remove extra spaces 
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
        print(f"Raw request body received (first 500 chars):")
        print(raw_body[:500])
        
        # Parse the outer JSON
        request_data = json.loads(raw_body)
        
        # determine which format we're dealing with
        if "query" in request_data:
            print("Detected 'query' format")
            #  JSON string inside "query" field
            query_str = request_data["query"]
            print(f"Query string to clean (first 500 chars):")
            print(query_str[:500])
            
            # Clean and parse the inner JSON
            suggestion_data = clean_and_parse_json(query_str)
            
        elif "diagnosis" in request_data:
            print("Detected direct JSON format")
            suggestion_data = request_data
            
        else:
            return JsonResponse({
                "success": False,
                "error": "Request must contain either 'query' or 'diagnosis' field"
            }, status=400)
        
        print(f"Successfully parsed suggestion data:")
        print(json.dumps(suggestion_data, indent=2))
        
        # Insert into table
        response = supabase.table('suggestion_logs').insert({
            "suggestion_data": suggestion_data
        }).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0]['id']
            print(f"Success! Inserted with ID: {inserted_id}")
            return JsonResponse({
                "success": True,
                "id": inserted_id,
                "message": "Suggestion inserted successfully"
            })
        else:
            print("Insert failed - no data returned")
            return JsonResponse({
                "success": False,
                "error": "Failed to insert data"
            }, status=500)
            
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        print(f"Error at position: {e.pos}")
        try:
            if 'cleaned' in locals():
                start = max(0, e.pos - 100)
                end = min(len(cleaned), e.pos + 100)
                print(f"Problem area in cleaned string: ...{cleaned[start:end]}...")
                print(f"Character at error: '{cleaned[e.pos:e.pos+20]}'")
        except:
            pass
            
        return JsonResponse({
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }, status=400)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "error": f"Server error: {str(e)}"

        }, status=500)
