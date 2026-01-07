import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase import create_client

# Supabase client 
SUPABASE_URL = <URL>
SUPABASE_KEY = <KEY>
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@csrf_exempt
def insert_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)

        product_name = data.get("product_name")
        category = data.get("category")
        sub_category = data.get("sub_category")
        brand = data.get("brand")

        # ---------------- VALIDATION ----------------
        if not product_name:
            return JsonResponse(
                {"error": "product_name is required"},
                status=400
            )

        # ---------------- DELETE IF EXISTS ----------------
        supabase.table("products") \
            .delete() \
            .eq("product_id", 38) \
            .execute()

        # ---------------- INSERT NEW ROW ----------------
        response = supabase.table("products").insert({
            "product_id" : 38,
            "product_name": product_name,
            "category": category,
            "sub_category": sub_category,
            "brand": brand
        }).execute()

        return JsonResponse({
            "status": "success",
            "product_id": response.data[0]["product_id"],
            "message": "Product replaced successfully"
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

