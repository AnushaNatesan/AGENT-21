import requests

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

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
