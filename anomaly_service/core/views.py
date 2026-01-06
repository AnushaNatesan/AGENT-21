import base64
import json
from xmlrpc import client
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase import create_client, Client
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
import requests
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

from PIL import Image # Ensure pillow is installed: pip install pillow
from django.core.mail import EmailMessage
from email.mime.image import MIMEImage
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from django.core.mail import get_connection
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw, ImageFont
import qrcode
import os
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

pipe.enable_attention_slicing()
pipe.enable_vae_slicing()
# --- Configuration ---
SUPABASE_URL = "<SUPABASE_URL>"
SUPABASE_KEY = "<SUPABASE_APIKEY>"


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


    
def fetch_supabase_last_row(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {
        "select": "*",
        "order": "product_id.desc",
        "limit": 1
    }
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        return data[0] if data else None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None

def fetch_latest_price_for_product(product_id):
    url = f"{SUPABASE_URL}/rest/v1/pricing_history"
    params = {
        "select": "*",
        "product_id": f"eq.{product_id}",
        "order": "pricing_id.desc",
        "limit": 1
    }
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        return data[0] if data else None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def generate_background(prompt):
    return pipe(
        prompt=prompt,
        num_inference_steps=30,
        guidance_scale=7.5
    ).images[0]


def add_overlay_elements(
    img,
    product_name,
    brand,
    price,
    logo_path=None,
    qr_url=None,
    brand_color=(20, 20, 20)
):

    draw = ImageDraw.Draw(img)

    # fonts (change path if needed)
    title_font = ImageFont.truetype("arialbd.ttf", 80)
    subtitle_font = ImageFont.truetype("arial.ttf", 50)
    price_font = ImageFont.truetype("arialbd.ttf", 65)
    small_font = ImageFont.truetype("arial.ttf", 40)

    w, h = img.size

    # brand color wash
    color_layer = Image.new("RGBA", img.size, brand_color + (90,))
    img.paste(color_layer, (0, 0), color_layer)

    # Product title
    draw.text((100, 80), product_name, fill="white", font=title_font)

    # brand subtitle
    draw.text((100, 180), f"by {brand}", fill="white", font=subtitle_font)

    # CTA
    draw.text((100, h - 200), "Shop Now", fill="white", font=small_font)


    # logo
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((220, 220))
        img.paste(logo, (w - 300, h - 300), logo)

    # QR code
    if qr_url:
        qr = qrcode.make(qr_url)
        qr = qr.resize((220, 220))
        img.paste(qr, (80, h - 340))

    return img



def automate_ad():

    product = fetch_supabase_last_row("products")
    if not product:
        print("No product found.")
        return

    product_id = product["product_id"]
    latest_price_row = fetch_latest_price_for_product(product_id)
    latest_price = latest_price_row["price"] if latest_price_row else 999

    base_prompt = (
        f"Luxury commercial advertising poster background for {product['product_name']} "
        f"in category {product['sub_category']} for brand {product['brand']}. "
        f"Product hero lighting, studio photography, black or dark premium background, "
        f"glow edges, reflections, cinematic shadows, minimal layout space for typography, "
        f"high contrast, 4k, ultra photorealistic product advertisement background."
    ) 

    try:
        # ---- generate three formats ----
        sizes = {
            "square": (1024, 1024),
            "portrait": (1024, 1350),
            "landscape": (1350, 1024)
        }

        for name, size in sizes.items():
            bg = generate_background(base_prompt)
            bg = bg.resize(size)

            final = add_overlay_elements(
                bg,
                product["product_name"],
                product["brand"],
                latest_price,
                logo_path=f"logos/{product['brand']}.png",
                qr_url=f"https://yourshop.com/product/{product_id}",
                brand_color=(0, 0, 0)
            )

            out = f"ad_{product_id}_{name}.png"
            final.save(out)
            print(f"✅ generated {out}")

        advertise(product_id)

    except Exception as e:
        print(f"❌ local image error: {e}")


def advertise(id):
    root = MIMEMultipart('related')
    root['Subject'] = "Our New Product Just Launched! This Price Just For You"
    root['From'] = "<AGENT_MAIL>"
    root['To'] = "<CUSTOMER_MAILS>"

    html = """
    <html>
      <body style="margin:0;padding:0;">
        <img src="cid:heroimage" style="display:block;">
      </body>
    </html>
    """

    html_part = MIMEText(html, 'html')
    root.attach(html_part)

    file_path = f"ad_{id}_square.png"

    with open(file_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", "<heroimage>")
        img.add_header("Content-Disposition", "inline", filename="image.jpg")
        root.attach(img)

    # send raw MIME directly via Django backend
    connection = get_connection()
    connection.open()
    connection.connection.sendmail(
        "<AGENT_MAIL>",
        ["<CUSTOMER MAILS>"],
        root.as_string(),
    )
    connection.close()

def send_html_email(subject, text_body, html_body, to):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email="<AGENT_MAIL>",
        to=to
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()

def create_email_template(content_html, header_color="#FF6B6B"):
    """Create a responsive email template with modern styling"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f5f5f5;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, {header_color} 0%, {header_color}dd 100%);
                padding: 30px;
                text-align: center;
                color: white;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px;
                color: #333333;
                line-height: 1.6;
            }}
            .details-box {{
                background-color: #f8f9fa;
                border-left: 4px solid {header_color};
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .detail-item {{
                display: flex;
                padding: 8px 0;
                border-bottom: 1px solid #e9ecef;
            }}
            .detail-item:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: 600;
                color: #495057;
                min-width: 140px;
            }}
            .detail-value {{
                color: #212529;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
                border-top: 1px solid #e9ecef;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: {header_color};
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
                font-weight: 500;
            }}
            .icon {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            {content_html}
        </div>
    </body>
    </html>
    """





def fetch_supabase(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()

def update_anomaly(anomalies):
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    rows=[]
    if(anomalies):
        for a in anomalies:
            row = {
                "type": a['type'],
                "description": a['an_desc']
            }
            rows.append(row)
        supabase.table("Anomaly").insert(rows).execute()

def send_html_email(subject, text_fallback, html_content, recipients, image_path=None):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_fallback,   # text fallback
        to=recipients
    )

    msg.attach_alternative(html_content, "text/html")

    # inline image support (optional)
    if image_path:
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<image1>")
            img.add_header("Content-Disposition", "inline", filename="image1.jpg")
            msg.attach(img)

    msg.send()
    
def notify(action,all_actions):
    # Admin notification
    subject = f"⚠ Anomaly detected: {action['type']}"
    
    # Build details HTML
    details_html = ""
    for k, v in action.items():
        if k != "message":
            details_html += f"""
            <div class="detail-item">
                <span class="detail-label">{k.replace('_', ' ').title()}:</span>
                <span class="detail-value">{v}</span>
            </div>
            """
    
    admin_content = f"""
        <div class="header">
            <div class="icon">⚠️</div>
            <h1>Anomaly Detected</h1>
        </div>
        <div class="content">
            <p style="font-size: 16px; color: #212529;">{action["message"]}</p>
            <div class="details-box">
                <h3 style="margin-top: 0; color: #495057;">Details</h3>
                {details_html}
            </div>
        </div>
        <div class="footer">
            <p>This is an automated alert from your monitoring system.</p>
            <p style="margin: 5px 0;">© {2025} Your Company. All rights reserved.</p>
        </div>
    """
    
    admin_html = create_email_template(admin_content, "#FF6B6B")
    
    # Send admin email
    send_html_email(
        subject,
        action["message"],  # Plain text fallback
        admin_html,
        ["<BUSINESS_OWNER_MAIL>"]
    )
    
    # Customer notifications
    if action['type'] == 'delivery_anomaly':
        subject = f"🚚 Delivery Delay Alert for Order {action['order_id']}"
        add_cont = ''
        if "weather_risk_anomaly" in [a['type'] for a in all_actions] and action['weather_id'] == [next(a['weather_id'] for a in all_actions if a['type'] == 'weather_risk_anomaly')]:
            add_cont = f"🚨 Delay in Delivery caused due to bad weather"
        day_count = action['delay'] if 'delay' in action else 'N/A'
        customer_content = f"""
            <div class="header" style="background: linear-gradient(135deg, #FFA726 0%, #FF9800 100%);">
                <div class="icon">🚚</div>
                <h1>Delivery Delay Notice</h1>
            </div>
            <div class="content">
                <p style="font-size: 16px;">Dear Customer,</p>
                <p>We regret to inform you that your delivery is experiencing an unexpected delay.</p>
                <p><strong style="color: #FF6B6B;">{add_cont}</strong></p>
                <div class="details-box">
                    <div class="detail-item">
                        <span class="detail-label">Order ID:</span>
                        <span class="detail-value"><strong>{action['order_id']}</strong></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Delivery ID:</span>
                        <span class="detail-value">{action['delivery_id']}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Delay Duration:</span>
                        <span class="detail-value" style="color: #FF6B6B; font-weight: 600;">{day_count} days</span>
                    </div>
                </div>
                
                <p>We sincerely apologize for the inconvenience and are working diligently to resolve this issue as quickly as possible.</p>
                <p style="margin-top: 24px;">Thank you for your understanding.</p>
                <p style="margin-top: 20px; color: #495057;"><strong>Best regards,</strong><br>Customer Service Team</p>
            </div>
            <div class="footer">
                <p>Need assistance? Contact our support team.</p>
                <p style="margin: 5px 0;">© {2025} Your Company. All rights reserved.</p>
            </div>
        """
        
        customer_html = create_email_template(customer_content, "#FFA726")
        plain_text = f"Dear Customer,\n\nWe regret to inform you that your delivery with ID {action['delivery_id']} is experiencing an abnormal delay. We apologize for the inconvenience caused and are working to resolve this issue promptly.\n\nThank you for your understanding.\n\nBest regards,\nCustomer Service Team"
        
        send_html_email(
            subject,
            plain_text,
            customer_html,
            ["<CUSTOMER_MAILS>"]
        )
        
    elif action['type'] == 'price_change_anomaly':
        subject = f"💰 Price Update for Product {action['product_id']}"
        price_change_percent = action['price_change'] * 100
        change_direction = "increased" if price_change_percent > 0 else "decreased"
        change_color = "#FF6B6B" if price_change_percent > 0 else "#4CAF50"
        
        customer_content = f"""
            <div class="header" style="background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);">
                <div class="icon">💰</div>
                <h1>Price Update Notification</h1>
            </div>
            <div class="content">
                <p style="font-size: 16px;">Dear Customer,</p>
                <p>We would like to inform you of a price change for one of our products.</p>
                
                <div class="details-box">
                    <div class="detail-item">
                        <span class="detail-label">Product ID:</span>
                        <span class="detail-value"><strong>{action['product_id']}</strong></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Price Change:</span>
                        <span class="detail-value" style="color: {change_color}; font-weight: 600; font-size: 18px;">
                            {price_change_percent:+.2f}%
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value">Price has {change_direction}</span>
                    </div>
                </div>
                
                <p>Please visit our website for complete and updated pricing details.</p>
                <p style="margin-top: 24px;">Thank you for your continued support.</p>
                <p style="margin-top: 20px; color: #495057;"><strong>Best regards,</strong><br>Customer Service Team</p>
            </div>
            <div class="footer">
                <p>Questions about pricing? Contact our sales team.</p>
                <p style="margin: 5px 0;">© {2025} Your Company. All rights reserved.</p>
            </div>
        """
        
        customer_html = create_email_template(customer_content, "#42A5F5")
        plain_text = f"Dear Customer,\n\nWe would like to inform you that there has been a price change for the product with ID {action['product_id']}. The price has changed by {price_change_percent:.2f}%. Please check our website for the updated pricing details.\n\nThank you for your continued support.\n\nBest regards,\nCustomer Service Team"
        
        send_html_email(
            subject,
            plain_text,
            customer_html,
           ["<CUSTOMER_MAILS>"]
        )
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
                "message": msg,
                "an_desc" : f"Sudden revenue change detected for product with product id:{int(r['product_id'])} on {r['calculated_for']}. {anomaly_type.upper()}!."
            })
    update_anomaly(anomalies)

    return anomalies



# --------- DELIVERY DELAY (MAD ROBUST) ----------
def detect_delivery_delay_anomalies_mad():
    deliveries = fetch_supabase("deliveries")

    delays = []
    valid = []
    anomalies = []

    # --- Step 1: Handle explicit delayed status and collect delays ---
    for d in deliveries:

        # 1A: explicit status delayed -> anomaly regardless of MAD
        if d.get("delivery_status") == "delayed":
            anomalies.append({
                "type": "delivery_delay",
                "delivery_id": d["delivery_id"],
                "order_id": d["order_id"],
                "delay_days": None,
                "message": "Abnormal delivery delay detected",
                "weather_id": d.get("weather_id"),
                "an_desc": f"Abnormal delivery delay detected for order with order id: {d['order_id']} (status marked delayed)."
            })

        # 1B: compute numeric delay only if both dates exist
        if d.get("actual_delivery_date") and d.get("promised_delivery_date"):
            delay = (
                pd.to_datetime(d["actual_delivery_date"]) -
                pd.to_datetime(d["promised_delivery_date"])
            ).days

            delays.append(delay)
            valid.append((d, delay))

    # --- No valid delays to compute MAD on ---
    if not delays:
        update_anomaly(anomalies)
        return anomalies

    # --- Step 2: MAD-based anomaly detection ---
    series = pd.Series(delays)

    median = series.median()
    mad = (np.abs(series - median)).median()

    # If MAD is zero, skip z-score logic but still return status-based anomalies
    if mad and not np.isnan(mad) and mad != 0:
        modified_z = 0.6745 * (series - median) / mad

        for (d, delay), mz in zip(valid, modified_z):
            if abs(mz) >= 3.5:
                anomalies.append({
                    "type": "delivery_delay",
                    "delivery_id": d["delivery_id"],
                    "order_id": d["order_id"],
                    "delay_days": int(delay),
                    "message": "Abnormal delivery delay detected",
                    "weather_id": d.get("weather_id"),
                    "an_desc": f"Abnormal delivery delay detected for order with order id: {d['order_id']} with a delay of {int(delay)} days."
                })

    # --- Final update & return ---
    update_anomaly(anomalies)
    return anomalies



# --------- PRICE CHANGE ANOMALIES ----------
def detect_price_change_anomalies():
    history = fetch_supabase("pricing_history")

    df = pd.DataFrame(history).sort_values(["product_id", "start_date"])

    df["pct_change"] = df.groupby("product_id")["price"].pct_change()

    outliers = df[df["pct_change"].abs() > 0.35]
    anomalies = []
    for _, row in outliers.iterrows():
        anomalies.append({
            "type": "price_spike",
            "pricing_id": row["pricing_id"],
            "product_id": row["product_id"],
            "pct_change": float(row["pct_change"]),
            "message": "Sudden abnormal price change detected",
            "an_desc" : f"Sudden abnormal price change detected for product with product id:{row['product_id']} with a price change of {float(row['pct_change'])*100:.2f}%."
        })
    update_anomaly(anomalies)

    return anomalies

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
                "message": "Customer sentiment is drifting unusually",
                "an_desc" : f"Customer sentiment is drifting unusually with a drift value of {float(d)} at sentiment id {sentiments[i]['sentiment_id']}."
            })
    update_anomaly(anomalies)
    return anomalies


# --------- FACTORY ----------


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
                },
                "an_desc" : f"Factory throughput low or backlog high for factory with id:{r['factory_id']}."
            })
    update_anomaly(anomalies)
    return anomalies


# --------- WEATHER ----------


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
    anomalies=[]
    for r in weather:
        if r["severity_level"] >= high_severity_threshold:
            anomalies.append({
                "type": "weather_risk",
                "weather_id": r["weather_id"],
                "location": r["observed_location"],
                "severity": r["severity_level"],
                "weather_type": r["weather_type"],
                "observation_at": r["observed_at"],
                "message": "Weather risk likely to impact logistics (data-driven threshold)",
                "derived_threshold": high_severity_threshold,
                "an_desc" : f"Weather risk likely to impact logistics at location {r['observed_location']} with severity {r['severity_level']}."
            })
    update_anomaly(anomalies)
    return anomalies



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

    amm = df[
        (abs(df["rev_change"]) > 2 * df["rev_std"]) |
        (abs(df["unit_change"]) > 2 * df["unit_std"])
    ]
    anomalies=[]
    for _, row in amm.iterrows():
        anomalies.append({
            "type": "market_share_change",
            "product_id": int(row["product_id"]),
            "calculated_for": row["calculated_for"],
            "revenue_share_percent": row["revenue_share_percent"],
            "unit_share_percent": row["unit_share_percent"],
            "message": "Sudden market share change detected",
            "an_desc" : f"Sudden market share change detected for product with product id:{int(row['product_id'])} on {row['calculated_for']} due to revenue share change of {float(row['rev_change']) if row['rev_change'] is not None else 'N/A'} and unit share change of {float(row['unit_change']) if row['unit_change'] is not None else 'N/A'}."
        })
    update_anomaly(anomalies)
    return anomalies


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
            "message": "Inventory level anomaly detected",
            "an_desc" : f"Inventory level anomaly detected for product with product id:{p['product_id']} due to {reason}."
        })
    update_anomaly(anomalies)
    return anomalies

# ---------- PROACTIVE AGENT USING ML ----------


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
            "delivery_id" : o["delivery_id"],   
            "weather_id": o["weather_id"],
            
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
            "price_change": p["pct_change"]
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
            "weather_id": w["weather_id"],
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


# ---------- ENDPOINT TRIGGERED BY DATABASE EVENT ----------

@csrf_exempt
def event_trigger(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    actions = run_ml_proactive_agent()

    return JsonResponse({
        "status": "ok",
        "actions": actions
    })

