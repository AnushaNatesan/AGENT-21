import requests
import time

# =========================
# CONFIG
# =========================
SERP_API_KEY = "b16c64bd9806b4d13ab5cb855591ab097891721817eb86c927f421ce1eb34dfe"
SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

BLOCKED_DOMAINS = [
    "amazon",
    "flipkart",
    "pinterest",
    "aliexpress",
    "ebay",
    "googleusercontent",
    "shutterstock",
]


# =========================
# SUPABASE HELPERS
# =========================
def fetch_products():
    url = f"{SUPABASE_URL}/rest/v1/products?select=*"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def update_product_image(product_id, image_url):
    url = f"{SUPABASE_URL}/rest/v1/products?product_id=eq.{product_id}"
    r = requests.patch(url, headers=HEADERS, json={"image_url": image_url})
    print("DB UPDATE:", r.status_code)
    return r.status_code in (200, 204)


# =========================
# SERPAPI IMAGE SEARCH
# =========================
def fetch_product_image(product_name):
    params = {
        "engine": "google_images",
        "q": f"{product_name} product photo white background",
        "api_key": SERP_API_KEY,
        "num": 10,
        "safe": "active",
    }

    print("🔍 Searching image for:", product_name)
    r = requests.get("https://serpapi.com/search", params=params, timeout=15)
    r.raise_for_status()

    images = r.json().get("images_results", [])

    for img in images:
        url = img.get("original")
        if url and not any(b in url.lower() for b in BLOCKED_DOMAINS):
            return url

    return None


# =========================
# IMAGE DOWNLOAD + UPLOAD
# =========================
def upload_to_supabase(image_url, filename):
    try:
        print("⬇️ Downloading:", image_url)

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/*",
        }

        resp = requests.get(image_url, headers=headers, timeout=10)
        resp.raise_for_status()
        img_data = resp.content

    except Exception as e:
        print("❌ Image download failed:", e)
        return None

    upload_url = (
        f"{SUPABASE_URL}/storage/v1/object/product-images/{filename}"
    )

    upload_headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "image/jpeg",
    }

    r = requests.post(upload_url, headers=upload_headers, data=img_data)

    print("☁️ Supabase upload:", r.status_code)

    if r.status_code not in (200, 201):
        return None

    return f"{SUPABASE_URL}/storage/v1/object/public/product-images/{filename}"


# =========================
# MAIN RUNNER
# =========================
def run_image_import():
    products = fetch_products()
    print(f"📦 Total products: {len(products)}")

    for p in products:
        print("\n➡️ Processing product:", p)

        if p.get("image_url"):
            print("⏭️ Image already exists")
            continue

        product_name = (
            p.get("product_name")
            or p.get("name")
            or p.get("title")
            or f"Product {p['product_id']}"
        )

        image_url = fetch_product_image(product_name)
        print("🖼️ Image found:", image_url)

        if not image_url:
            print("❌ No usable image found")
            continue

        public_url = upload_to_supabase(
            image_url, f"{p['product_id']}.jpg"
        )

        if not public_url:
            print("❌ Upload failed")
            continue

        update_product_image(p["product_id"], public_url)
        print("✅ Image saved:", public_url)

        time.sleep(1)  # prevent rate limiting


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_image_import()
