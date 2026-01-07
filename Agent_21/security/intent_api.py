"""
Endpoint for classifying query intent
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import time
from .ai_intent_classifier import get_intent_classifier
@csrf_exempt
@require_POST
def classify_intent(request):
    """
    POST /api/intent/classify/
    
    Request Body (JSON):
    {
        "query": "Show me all customer details"
    }
    
    Response (JSON):
    {
        "decision": "ALLOW|BLOCK|REVIEW",
        "category": "business_query|bulk_data_extraction|pii_access|jailbreak|sql_injection",
        "confidence": 0.85,
        "reason": "Closer to dangerous intent: 'show me all customer data'"
    }
    """
    
    print("\n" + "="*70)
    print("AI INTENT CLASSIFIER")
    print("="*70)
    
    start_time = time.time()
    
    try:
        # Parse request
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        print(f"Query: {query[:100]}..." if len(query) > 100 else f"📝 Query: {query}")
        
        if not query:
            return JsonResponse({
                "decision": "BLOCK",
                "category": "empty_query",
                "confidence": 1.0,
                "reason": "Empty query submitted",
                "error": "No query provided"
            }, status=400)
        
        # Get intent guard (singleton)
        guard = get_intent_classifier()
        
        # Classify intent
        result = guard.classify(query)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        
        # Console logging
        print(f"Decision: {result['decision']}")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Reason: {result['reason'][:100]}...")
        print(f"Time: {execution_time}ms")
        print("="*70)
        
        # Prepare response (only essential fields)
        response_data = {
            "decision": result["decision"],
            "category": result["category"],
            "confidence": float(result["confidence"]),
            "reason": result["reason"],
            "response_time_ms": execution_time
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        print(" Invalid JSON")
        return JsonResponse({
            "decision": "BLOCK",
            "category": "invalid_request",
            "confidence": 1.0,
            "reason": "Invalid JSON format",
            "error": "Invalid JSON in request body"
        }, status=400)
        
    except Exception as e:
        print(f"Classification error: {str(e)}")
        return JsonResponse({
            "decision": "REVIEW",
            "category": "classification_error",
            "confidence": 0.0,
            "reason": f"Error during classification: {str(e)}",
            "error": str(e)

        }, status=500)
