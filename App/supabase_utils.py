import requests

SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"


HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def fetch_supabase(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    return requests.get(url, headers=HEADERS).json()

def update_product_image(product_id, image_url):
    url = f"{SUPABASE_URL}/rest/v1/products?product_id=eq.{product_id}"
    requests.patch(url, headers=HEADERS, json={"image_url": image_url})
