import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import bcrypt
import requests
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password

# Advanced Features Imports
from App.self_healing_sql import execute_self_healing_query
from App.agentic_boardroom import convene_boardroom, get_boardroom_history
from App.digital_twin import run_simulation, get_simulation_history, compare_scenarios
from App.audit_trail import (
    log_agent_cycle, verify_audit_integrity, get_audit_cycles,
    search_audit_trail, generate_audit_report, get_cycle_details
)
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


# Constants
SUPABASE_URL = "https://ubvcncqceakcmosxjkpx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidmNuY3FjZWFrY21vc3hqa3B4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc0NTAyODAsImV4cCI6MjA4MzAyNjI4MH0.k4HrBg0-s424zl1-em8Nj4vDLPRtFb6Ad8UxBIZM1m0"

REST_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Create a robust requests session for better connection handling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount("https://", adapter)
session.mount("http://", adapter)

@csrf_exempt
def boardroom_ui(request):
    return render(request, "war_room.html")

def fetch_supabase(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        res = session.get(url, headers=REST_HEADERS, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Supabase Error ({table}): {str(e)}")
        return []

# Helper for product images since they aren't in the DB
def get_product_image(product):
    name = (product.get("product_name") or "").lower()
    cat = (product.get("category") or "").lower()
    sub = (product.get("sub_category") or "").lower()
    
    # Precise Keyword Mapping
    if "phone" in name or "mobile" in cat:
        return "https://images.unsplash.com/photo-1598327105666-5b89351aff97?q=80&w=800" # iPhone/Phone
    if "tablet" in name or "ipad" in name:
        return "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=800" # Tablet
    if any(k in name for k in ["laptop", "ultrabook", "macbook", "pro", "air"]) and "tablet" not in name:
        return "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=800" # Laptop
    if "watch" in name or "wearable" in cat:
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=800" # Smartwatch
    if any(k in name for k in ["buds", "headset", "earphones", "audio", "sound"]):
        return "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800" # Headphones
    if "camera" in name:
        return "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?q=80&w=800" # Camera
    if "tv" in name or "television" in name:
        return "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?q=80&w=800" # TV
    if "console" in name or "playstation" in name or "xbox" in name:
        return "https://images.unsplash.com/photo-1486401899868-0e435ed85128?q=80&w=800" # Gaming
    
    # Category fallbacks
    mapping = {
        "electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?q=80&w=800",
        "fitness": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800",
        "fashion": "https://images.unsplash.com/photo-1445205170230-053b830c6050?q=80&w=800",
        "home appliances": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=800",
    }
    
    return mapping.get(cat, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=800")


def dashboard(request):
    """Serve the Agent-21 Sovereign Dashboard (Admin/Analyst)."""
    return render(request, 'dashboard.html')

def market_survey(request):
    """Serve the Market Intelligence Platform."""
    return render(request, 'Market_Survey.html')

def customer_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "") # NO STRIP on password

        # Fetch user from Supabase
        url = f"{SUPABASE_URL}/rest/v1/customers?email=eq.{email}&select=*"
        try:
            res = session.get(url, headers=REST_HEADERS, timeout=10)
            users = res.json()
        except Exception as e:
            messages.error(request, f"System error: {str(e)}")
            return render(request, "customer_login.html")

        if not users:
            messages.error(request, "Invalid credentials")
            return render(request, "customer_login.html")

        customer = users[0]
        stored_hash = customer["password"]

        try:
            # ✅ Verify hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                request.session["customer_id"] = customer["customer_id"]
                request.session["username"] = customer["username"]
                request.session.save()
                return redirect("/customer/dashboard/")
            
            # Fallback for plain text
            if password == stored_hash:
                request.session["customer_id"] = customer["customer_id"]
                request.session["username"] = customer["username"]
                request.session.save()
                return redirect("/customer/dashboard/")
                
            messages.error(request, "Incorrect password")
        except Exception:
            # Handle cases where stored_hash might not be valid bcrypt (plain text)
            if password == stored_hash:
                request.session["customer_id"] = customer["customer_id"]
                request.session["username"] = customer["username"]
                request.session.save()
                return redirect("/customer/dashboard/")
            messages.error(request, "Authentication failed")

    return render(request, "customer_login.html")

def customer_signup(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", email.split('@')[0]).strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "Email and password are required")
            return render(request, "customer_signup.html")

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert into Supabase
        data = {
            "email": email,
            "username": username,
            "password": hashed_pw
        }
        
        try:
            res = requests.post(f"{SUPABASE_URL}/rest/v1/customers", headers=REST_HEADERS, json=data)
            if res.status_code == 201 or res.status_code == 200:
                messages.success(request, "Account created successfully! Please login.")
                return redirect("/customer/login/")
            else:
                messages.error(request, f"Signup failed: {res.text}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'customer_signup.html')

def customer_dashboard(request):
    if "customer_id" not in request.session:
        return redirect("/customer/login/")

    customer_id = request.session["customer_id"]

    # Fetch customer details from Supabase
    url = f"{SUPABASE_URL}/rest/v1/customers?customer_id=eq.{customer_id}&select=*"
    res = requests.get(url, headers=REST_HEADERS)
    customer = res.json()[0]

    context = {
        "customer": customer,
        "initials": customer["username"][:2].upper(),
    }

    return render(request, "customer_dashboard.html", context)


# headers = {
#     "apikey": SUPABASE_KEY,
#     "Authorization": f"Bearer {SUPABASE_KEY}",
#     "Content-Type": "application/json"
# }


def fetch_supabase(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.get(url, headers=REST_HEADERS)
    res.raise_for_status()
    return res.json()

# ---------- ML ANOMALY DETECTION ----------

# --------- REVENUE OUTLIERS ----------
def detect_revenue_anomalies_ml():
    rows = fetch_supabase("revenue_stats")
    if not rows:
        return []

    # revenue values
    revenue = np.array([float(r["total_revenue"]) for r in rows]).reshape(-1, 1)

    # isolation forest
    model = IsolationForest(contamination="auto", random_state=42)
    preds = model.fit_predict(revenue)

    # use central tendency from normal points only
    normal_values = [float(rows[i]["total_revenue"]) for i, p in enumerate(preds) if p == 1]

    if not normal_values:
        return []  # fallback safety

    center = np.median(normal_values)

    anomalies = []

    for i, p in enumerate(preds):
        if p == -1:
            r = rows[i]
            value = float(r["total_revenue"])

            if value > center:
                anomaly_type = "revenue_spike"
                msg = "Unusual spike in revenue detected"
            else:
                anomaly_type = "revenue_drop"
                msg = "Unusual drop in revenue detected"

            anomalies.append({
                "type": anomaly_type,
                "stats_id": r["stats_id"],
                "product_id": r["product_id"],
                "total_revenue": r["total_revenue"],
                "calculated_for": r["calculated_for"],
                "center_reference": center,
                "message": msg
            })

    return anomalies



# --------- DELIVERY DELAY (MAD ROBUST) ----------
def detect_delivery_delay_anomalies_mad():
    deliveries = fetch_supabase("deliveries")

    delays = []
    valid = []

    for d in deliveries:
        if d.get("actual_delivery_date"):
            delay = (
                pd.to_datetime(d["actual_delivery_date"]) -
                pd.to_datetime(d["promised_delivery_date"])
            ).days
            delays.append(delay)
            valid.append(d)

    if len(delays) < 5:
        return []

    series = pd.Series(delays)

    median = series.median()
    mad = (np.abs(series - median)).median()

    if mad == 0 or np.isnan(mad):
        return []

    modified_z = 0.6745 * (series - median) / mad

    anomalies = []
    for d, mz, delay in zip(valid, modified_z, delays):
        if abs(mz) >= 3.5:
            anomalies.append({
                "type": "delivery_delay",
                "delivery_id": d["delivery_id"],
                "order_id": d["order_id"],
                "delay_days": int(delay),
                "modified_z": float(mz),
                "message": "Abnormal delivery delay detected"
            })

    return anomalies


# --------- PRICE CHANGE ANOMALIES ----------
def detect_price_change_anomalies():
    history = fetch_supabase("pricing_history")

    df = pd.DataFrame(history).sort_values(["product_id", "start_date"])

    df["pct_change"] = df.groupby("product_id")["price"].pct_change()

    outliers = df[df["pct_change"].abs() > 0.35]

    return [
        {
            "type": "price_spike",
            "pricing_id": row["pricing_id"],
            "product_id": row["product_id"],
            "pct_change": float(row["pct_change"]),
            "message": "Sudden abnormal price change detected"
        }
        for _, row in outliers.iterrows()
    ]


# --------- SENTIMENT DRIFT ----------
def detect_sentiment_drift():
    sentiments = fetch_supabase("review_sentiments")

    scores = [float(s["sentiment_score"]) for s in sentiments]

    if len(scores) < 10:
        return []

    series = pd.Series(scores)

    rolling = series.rolling(window=10).mean()
    drift = np.gradient(rolling)

    anomalies = []
    for i, d in enumerate(drift):
        if abs(d) > 0.25:
            anomalies.append({
                "type": "sentiment_drift",
                "sentiment_id": sentiments[i]["sentiment_id"],
                "drift": float(d),
                "message": "Customer sentiment is drifting unusually"
            })

    return anomalies


# --------- FACTORY ----------
import numpy as np

def detect_factory_throughput_anomalies():
    rows = fetch_supabase("factory_performance")
    if not rows:
        return []

    throughputs = np.array([r["throughput_percentage"] for r in rows], dtype=float)
    backlogs = np.array([r["backlog_units"] for r in rows], dtype=float)

    # --- Data-driven thresholds (Z-score style) ---
    # k controls sensitivity: 2 = conservative, 3 = very strict, 1.5 = sensitive
    k = 2.0

    thr_mean = throughputs.mean()
    thr_std = throughputs.std(ddof=1) if len(throughputs) > 1 else 0
    backlog_mean = backlogs.mean()
    backlog_std = backlogs.std(ddof=1) if len(backlogs) > 1 else 0

    # fallback if std≈0 (flat data)
    if thr_std == 0:
        throughput_low_threshold = thr_mean * 0.9
    else:
        throughput_low_threshold = thr_mean - k * thr_std

    if backlog_std == 0:
        backlog_high_threshold = backlog_mean * 1.1
    else:
        backlog_high_threshold = backlog_mean + k * backlog_std

    anomalies = []
    for r in rows:
        low_throughput = r["throughput_percentage"] < throughput_low_threshold
        high_backlog = r["backlog_units"] > backlog_high_threshold

        if low_throughput or high_backlog:
            anomalies.append({
                "type": "factory_issue",
                "factory_id": r["factory_id"],
                "throughput": r["throughput_percentage"],
                "backlog": r["backlog_units"],
                "message": "Factory throughput low or backlog high (data-driven thresholds)",
                "units_produced": r["units_produced"],
                "derived_thresholds": {
                    "throughput_low_threshold": throughput_low_threshold,
                    "backlog_high_threshold": backlog_high_threshold,
                }
            })

    return anomalies


# --------- WEATHER ----------
import numpy as np

def detect_weather_risk():
    weather = fetch_supabase("weather_conditions")
    if not weather:
        return []

    severities = np.array([float(r["severity_level"]) for r in weather])

    # Quartiles
    q1 = np.percentile(severities, 25)
    q3 = np.percentile(severities, 75)
    iqr = q3 - q1

    # Data-driven high-risk threshold
    high_severity_threshold = q3 + 1.5 * iqr

    # Fallback if data is flat
    if iqr == 0:
        high_severity_threshold = q3  # everything above typical upper range

    return [
        {
            "type": "weather_risk",
            "weather_id": r["weather_id"],
            "location": r["observed_location"],
            "severity": r["severity_level"],
            "weather_type": r["weather_type"],
            "observation_at": r["observed_at"],
            "message": "Weather risk likely to impact logistics (data-driven threshold)",
            "derived_threshold": high_severity_threshold
        }
        for r in weather
        if r["severity_level"] >= high_severity_threshold
    ]

def business_insights(request):
    return render(request, "business_dashboard.html")

# --------- MARKET SHARE ----------
def detect_market_share_sudden_change():
    stats = fetch_supabase("revenue_stats")
    if not stats:
        return []

    df = pd.DataFrame(stats).sort_values(by=["product_id", "calculated_for"])

    df["rev_change"] = df.groupby("product_id")["revenue_share_percent"].diff()
    df["unit_change"] = df.groupby("product_id")["unit_share_percent"].diff()

    df["rev_std"] = df.groupby("product_id")["rev_change"].transform("std")
    df["unit_std"] = df.groupby("product_id")["unit_change"].transform("std")

    anomalies = df[
        (abs(df["rev_change"]) > 2 * df["rev_std"]) |
        (abs(df["unit_change"]) > 2 * df["unit_std"])
    ]

    return [
        {
            "type": "market_share_change",
            "product_id": int(row["product_id"]),
            "rev_change": float(row["rev_change"]) if row["rev_change"] is not None else None,
            "unit_change": float(row["unit_change"]) if row["unit_change"] is not None else None,
            "message": "Sudden market share change detected"
        }
        for _, row in anomalies.iterrows()
    ]


# --------- INVENTORY ----------
def detect_inventory_anomalies_ml():
    products = fetch_supabase("products")
    if not products:
        return []

    stocks = np.array([float(p.get("current_stock", 0)) for p in products])

    q1 = np.percentile(stocks, 25)
    q3 = np.percentile(stocks, 75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    anomalies = []

    for p in products:
        s = float(p.get("current_stock", 0))

        if s < 0:
            reason = "negative_stock"
        elif s == 0:
            reason = "stockout"
        elif s < lower or s > upper:
            reason = "iqr_outlier"
        else:
            continue

        anomalies.append({
            "type": "inventory_anomaly",
            "product_id": p["product_id"],
            "current_stock": s,
            "reason": reason,
            "message": "Inventory level anomaly detected"
        })

    return anomalies

# ---------- PROACTIVE AGENT USING ML ----------

def notify(action):
    subject = f"⚠ Anomaly detected: {action['type']}"
    message = action["message"]+"\n\nDetails:\n"
    for k, v in action.items():
        if k != "message":
            message += f"- {k}: {v}\n"

    send_mail(
        subject,
        message,
        "saymyname.hacksym@gmail.com",
        ["vishwajithcodes@gmail.com"],
        fail_silently=False
    )
def run_ml_proactive_agent():

    revenue_anoms = detect_revenue_anomalies_ml()
    delivery_anoms = detect_delivery_delay_anomalies_mad()
    inventory_anoms = detect_inventory_anomalies_ml()
    price_change_anoms = detect_price_change_anomalies()
    sentiment_drift_anoms = detect_sentiment_drift()
    factory_throughput_anoms = detect_factory_throughput_anomalies()
    weather_risk_anoms = detect_weather_risk()
    market_share_change_anoms = detect_market_share_sudden_change()

    actions = []

    for r in revenue_anoms:
        actions.append({
            "type": r['type'],
            "message": "ML detected unusual revenue",
            "value": r["total_revenue"],
            "day": r["calculated_for"],
            "product_id": r["product_id"]
        })

    for o in delivery_anoms:
        actions.append({
            "type": "delivery_anomaly",
            "message": "ML detected abnormal order delay",
            "order_id": o["order_id"],
            "customer_id": o["customer_id"],
            "delivery_id" : o["delivery_id"],   
            "delay": str((pd.to_datetime(o["actual_delivery_date"]) - pd.to_datetime(o["promised_delivery_date"])).days),
        })

    for i in inventory_anoms:
        actions.append({
            "type": "inventory_anomaly",
            "message": "ML detected abnormal inventory level",
            "product_id": i["product_id"],
            "stock": i["current_stock"]
        })
    

    for p in price_change_anoms:
        actions.append({
            "type": "price_change_anomaly",
            "message": "Significant price change detected",
            "product_id": p["product_id"],
            "price_change": p["price"]
        })
    for s in sentiment_drift_anoms:
        actions.append({
            "type": "sentiment_drift_anomaly",
            "message": "Customer sentiment drift detected",
            "sentiment_id": s["sentiment_id"],
            "review_id": s["review_id"],
            "sentiment_score": s["sentiment_score"],
            "detected_issues": s['detected_issues'],
        })
    for f in factory_throughput_anoms:
        actions.append({
            "type": "factory_throughput_anomaly",
            "message": "Factory throughput anomaly detected",
            "factory_id": f["factory_id"],
            "produced_units": f["units_produced"],
            "throughput_percentage": f["throughput"],
            "backlog_units": f["backlog"]
        })

    for w in weather_risk_anoms:
        actions.append({
            "type": "weather_risk_anomaly",
            "message": "Severe weather condition detected",
            "location": w["location"],
            "severity_level": w["severity"],
            "description": w["weather_type"]+" observed on "+w["observation_at"]
        })
    
    for m in market_share_change_anoms:
        actions.append({
            "type": "market_share_change_anomaly",
            "message": "Sudden market share change detected",
            "product_id": m["product_id"],
            "calculated_for": m["calculated_for"],
            "revenue_share_percent": m["revenue_share_percent"],
            "unit_share_percent": m["unit_share_percent"]
        })
    return actions


# ---------- CUSTOMER PORTAL API ----------

@csrf_exempt
def get_customer_products(request):
    try:
        products = fetch_supabase("products")
        pricing = fetch_supabase("pricing_history")
        
        if not products:
            return JsonResponse({"products": []})

        # Map latest price
        price_map = {}
        # Sort by start_date so later ones overwrite earlier ones
        pricing.sort(key=lambda x: x.get('start_date', ''))
        for p in pricing:
            price_map[p['product_id']] = p['price']

        cleaned = []
        for p in products:
            cleaned.append({
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "brand": p["brand"],
                "category": p["category"],
                "price": price_map.get(p["product_id"], "N/A"),
                "image_url": get_product_image(p), 
            })

        return JsonResponse({"products": cleaned})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_similar_products(request, product_id):
    try:
        products = fetch_supabase("products")
        pricing = fetch_supabase("pricing_history")
        
        base = next((p for p in products if p["product_id"] == product_id), None)
        
        if not base:
            return JsonResponse({"products": []})

        pricing.sort(key=lambda x: x.get('start_date', ''))
        price_map = {p['product_id']: p['price'] for p in pricing}
        category = base["category"]
        
        similar = []
        for p in products:
            if p["category"] == category and p["product_id"] != product_id:
                similar.append({
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "brand": p["brand"],
                    "price": price_map.get(p["product_id"], "N/A"),
                    "image_url": get_product_image(p),
                })
        
        return JsonResponse({"products": similar[:4]})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        
        if product_id is None:
            return JsonResponse({"error": "Product ID required"}, status=400)
        
        product_id = str(product_id)
        
        # Initialize cart as dict {id: quantity}
        if "cart" not in request.session or not isinstance(request.session["cart"], dict):
            request.session["cart"] = {}
        
        cart = request.session["cart"]
        cart[product_id] = cart.get(product_id, 0) + 1
        request.session["cart"] = cart
        request.session.modified = True
        request.session.modified = True
        request.session.save()
        
        return JsonResponse({
            "status": "ok", 
            "cart_count": sum(cart.values())
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def manage_wishlist(request):
    if "wishlist" not in request.session:
        request.session["wishlist"] = []
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            action = data.get("action", "toggle")
            
            wishlist = request.session["wishlist"]
            if action == "toggle":
                if product_id in wishlist:
                    wishlist.remove(product_id)
                else:
                    wishlist.append(product_id)
            elif action == "remove":
                if product_id in wishlist: wishlist.remove(product_id)
            
            request.session["wishlist"] = wishlist
            request.session.modified = True
            request.session.save()
            return JsonResponse({"status": "ok", "wishlist": wishlist})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"wishlist": request.session["wishlist"]})

@csrf_exempt
def get_wishlist_details(request):
    wishlist_ids = request.session.get("wishlist", [])
    if not wishlist_ids:
        return JsonResponse({"products": []})
        
    try:
        products = fetch_supabase("products")
        pricing = fetch_supabase("pricing_history")
        pricing.sort(key=lambda x: x.get('start_date', ''))
        price_map = {p['product_id']: p['price'] for p in pricing}
        
        items = []
        for pid in wishlist_ids:
            p = next((item for item in products if item["product_id"] == int(pid)), None)
            if p:
                items.append({
                    "product_id": pid,
                    "product_name": p["product_name"],
                    "brand": p["brand"],
                    "price": price_map.get(p["product_id"], 0),
                    "image_url": p.get("image_url") if p.get("image_url") else get_product_image(p)
                })
        return JsonResponse({"products": items})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def manage_settings(request):
    customer = request.session.get("customer")
    if not customer:
        return JsonResponse({"error": "Unauthorized"}, status=401)
        
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Update session customer data (in a real app, update DB)
            customer["username"] = data.get("username", customer["username"])
            customer["email"] = data.get("email", customer["email"])
            request.session["customer"] = customer
            request.session.modified = True
            request.session.save()
            return JsonResponse({"status": "ok", "customer": customer})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"customer": customer})

@csrf_exempt
def get_cart_details(request):
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    
    if not cart:
        return JsonResponse({"products": [], "total": 0})
    
    try:
        products = fetch_supabase("products")
        pricing = fetch_supabase("pricing_history")
        
        # Map latest price
        pricing.sort(key=lambda x: x.get('start_date', ''))
        price_map = {p['product_id']: p['price'] for p in pricing}
        
        cart_items = []
        total = 0
        for pid_str, qty in cart.items():
            try:
                pid = int(pid_str)
            except (ValueError, TypeError):
                continue
                
            p = next((item for item in products if item["product_id"] == pid), None)
            if p:
                price = price_map.get(pid) or 0
                item_total = price * qty
                total += item_total
                cart_items.append({
                    "product_id": pid,
                    "product_name": p["product_name"],
                    "brand": p["brand"],
                    "price": price,
                    "quantity": qty,
                    "item_total": item_total,
                    "image_url": p.get("image_url") if p.get("image_url") else get_product_image(p)
                })
        
        return JsonResponse({"products": cart_items, "total": total})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def remove_from_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        product_id = str(data.get("product_id"))
        
        cart = request.session.get("cart", {})
        if not isinstance(cart, dict):
            cart = {}
        if product_id in cart:
            del cart[product_id]
            request.session["cart"] = cart
            request.session.save()
            
        return JsonResponse({"status": "ok", "cart_count": sum(cart.values())})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def confirm_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict) or not cart:
        return JsonResponse({"error": "Cart is empty"}, status=400)
    
    if "order_history" not in request.session:
        request.session["order_history"] = []
    
    order_id = len(request.session["order_history"]) + 1001
    
    # Enrich order with tracking data
    order = {
        "order_id": order_id,
        "items": cart,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Processing",
        "total": 0, # Calculate later
        "estimated_delivery": (time.time() + (86400 * 3)), # 3 days from now
        "tracking_timeline": [
            {"status": "Confirmed", "time": time.strftime("%H:%M, %d %b"), "location": "System", "description": "Order successfully placed."}
        ]
    }
    
    # Calculate total for history
    try:
        products = fetch_supabase("products")
        pricing = fetch_supabase("pricing_history")
        pricing.sort(key=lambda x: x.get('start_date', ''))
        price_map = {p['product_id']: p['price'] for p in pricing}
        
        total = 0
        item_details = []
        for pid_str, qty in cart.items():
            pid = int(pid_str)
            p = next((item for item in products if item["product_id"] == pid), None)
            if p:
                price = price_map.get(pid) or 0
                total += price * qty
                item_details.append({"name": p["product_name"], "qty": qty})
        
        order["total"] = total
        order["summary"] = ", ".join([f"{i['qty']}x {i['name']}" for i in item_details[:2]])
        if len(item_details) > 2: order["summary"] += "..."
    except:
        pass

    request.session["order_history"].append(order)
    request.session["cart"] = {}
    request.session.modified = True
    request.session.save()
    
    return JsonResponse({"status": "ok", "order_id": order_id})

@csrf_exempt
def get_order_history(request):
    history = request.session.get("order_history", [])
    
    # For demo purposes, let's add some mock historical orders if history is empty
    if not history:
        history = [
            {
                "order_id": 982,
                "date": "2026-01-02 14:20:00",
                "status": "Delivered",
                "total": 699.00,
                "summary": "1x Aurora TV 55",
                "tracking_timeline": [
                    {"status": "Delivered", "time": "18:00, 04 Jan", "location": "Home Office", "description": "Package handed to resident."},
                    {"status": "Out for Delivery", "time": "09:00, 04 Jan", "location": "Local Hub", "description": "On its way."},
                    {"status": "Dispatched", "time": "11:30, 03 Jan", "location": "Warehouse", "description": "Package left the facility."}
                ]
            },
            {
                "order_id": 985,
                "date": "2026-01-04 10:15:00",
                "status": "Delayed",
                "total": 1249.00,
                "summary": "1x MacBook Pro M3",
                "delay_reason": "High demand and global logistics congestion at Singapore transit hub.",
                "rca": "Our Agent-21 AI detected a surge in demand for M3 chips globally, causing a 48h bottleneck in specialized electronic shipping lanes.",
                "tracking_timeline": [
                    {"status": "Delayed", "time": "08:00, 05 Jan", "location": "Singapore Hub", "description": "Held at customs due to high volume."},
                    {"status": "Dispatched", "time": "22:00, 04 Jan", "location": "International Export", "description": "In transit."}
                ]
            }
        ]
        request.session["order_history"] = history
        request.session.save()

    return JsonResponse({"orders": history[::-1]}) # Newest first

@csrf_exempt
def get_order_tracking(request, order_id):
    history = request.session.get("order_history", [])
    order = next((o for o in history if str(o["order_id"]) == str(order_id)), None)
    
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)
        
    return JsonResponse(order)

@csrf_exempt
def event_trigger(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    actions = run_ml_proactive_agent()

    return JsonResponse({
        "status": "ok",
        "actions": actions
    })

def business_insights(request):
    """Serve the Business Insights Dashboard."""
    return render(request, 'business_dashboard.html')

@csrf_exempt
def get_business_data(request):
    """API to fetch structured data for business visualizations."""
    try:
        revenue_stats = fetch_supabase("revenue_stats")
        products = fetch_supabase("products")
        
        # Merge product names with stats
        product_map = {p['product_id']: p for p in products}
        
        enriched_stats = []
        for s in revenue_stats:
            pid = s.get('product_id')
            # Handle possible string/int mismatch
            try: pid = int(pid) 
            except: pass
            
            p_info = product_map.get(pid, {})
            enriched_stats.append({
                **s,
                "product_name": p_info.get('product_name', 'Unknown'),
                "category": p_info.get('category', 'Miscellaneous'),
                "total_revenue": float(s.get('total_revenue', 0)),
                "image_url": get_product_image(p_info)
            })
            
        return JsonResponse({
            "revenue_stats": enriched_stats,
            "products": products
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========================================
# ADVANCED FEATURES API ENDPOINTS
# ========================================

# 1. SELF-HEALING SQL RE-SENSING
@csrf_exempt
def api_self_healing_sql(request):
    """Execute SQL with autonomous self-healing"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        
        if not query:
            return JsonResponse({"error": "Query required"}, status=400)
        
        # Execute with self-healing
        result = execute_self_healing_query(query)
        
        # Log to audit trail
        log_agent_cycle(
            sense={'query': query, 'endpoint': 'self_healing_sql'},
            think={'healing_attempts': result.get('attempts', 0), 'healing_log': result.get('healing_log', [])},
            act={'success': result['success'], 'data_count': len(result.get('data', []))}
        )
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 2. AGENTIC BOARDROOM (Multi-Agent Negotiation)
@csrf_exempt
def api_convene_boardroom(request):
    """Convene the agentic boardroom for strategic decision making"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        situation = data.get('situation', {})
        
        if not situation:
            return JsonResponse({"error": "Situation required"}, status=400)
        
        # Convene boardroom
        session = convene_boardroom(situation)
        
        # Log to audit trail
        log_agent_cycle(
            sense={'situation': situation},
            think={
                'logistics_analysis': session['logistics_analysis'],
                'finance_analysis': session['finance_analysis'],
                'executive_decision': session['executive_decision']
            },
            act={'decision': session['executive_decision'].get('decision'), 'session_id': session['session_id']}
        )
        
        return JsonResponse(session)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_boardroom_history(request):
    """Get boardroom session history"""
    try:
        limit = int(request.GET.get('limit', 10))
        history = get_boardroom_history(limit)
        return JsonResponse({"sessions": history})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 3. DIGITAL TWIN (What-If Simulator)
@csrf_exempt
def api_run_simulation(request):
    """Run a what-if scenario simulation"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        scenario = data.get('scenario', {})
        duration_days = data.get('duration_days', 30)
        
        if not scenario:
            return JsonResponse({"error": "Scenario required"}, status=400)
        
        # Run simulation
        result = run_simulation(scenario, duration_days)
        
        # Log to audit trail
        log_agent_cycle(
            sense={'scenario': scenario, 'duration_days': duration_days},
            think={
                'predictions': result.get('predicted_state'),
                'impact_analysis': result.get('impact_analysis'),
                'risk_level': result.get('risk_level')
            },
            act={'simulation_id': result['simulation_id'], 'recommendations': result.get('recommendations', [])}
        )
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_simulation_history(request):
    """Get simulation history"""
    try:
        limit = int(request.GET.get('limit', 10))
        history = get_simulation_history(limit)
        return JsonResponse({"simulations": history})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_compare_scenarios(request):
    """Compare multiple scenarios"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        scenarios = data.get('scenarios', [])
        
        if not scenarios or not isinstance(scenarios, list):
            return JsonResponse({"error": "Scenarios array required"}, status=400)
        
        comparison = compare_scenarios(scenarios)
        return JsonResponse(comparison)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 4. IMMUTABLE AUDIT TRAIL
@csrf_exempt
def api_verify_audit_integrity(request):
    """Verify the integrity of the audit trail"""
    try:
        integrity = verify_audit_integrity()
        return JsonResponse(integrity)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_get_audit_cycles(request):
    """Get recent audit cycles"""
    try:
        limit = int(request.GET.get('limit', 50))
        cycles = get_audit_cycles(limit)
        return JsonResponse({"cycles": cycles, "total": len(cycles)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_search_audit_trail(request):
    """Search the audit trail"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body)
        filters = data.get('filters', {})
        
        results = search_audit_trail(filters)
        return JsonResponse({"results": results, "count": len(results)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_generate_audit_report(request):
    """Generate comprehensive audit report"""
    try:
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        
        report = generate_audit_report(start_time, end_time)
        return JsonResponse(report)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_get_cycle_details(request, cycle_id):
    """Get details of a specific audit cycle"""
    try:
        cycle = get_cycle_details(cycle_id)
        
        if cycle:
            return JsonResponse(cycle)
        else:
            return JsonResponse({"error": "Cycle not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

