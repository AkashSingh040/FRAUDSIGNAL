import os
import time
import random
import razorpay
from dotenv import load_dotenv

# Load keys from the backend .env if running locally
load_dotenv(dotenv_path="backend/.env")

KEY_ID     = os.getenv("RAZORPAY_KEY_ID",     "YOUR_TEST_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_TEST_KEY_SECRET")

if KEY_ID == "YOUR_TEST_KEY_ID":
    print("⚠️  Error: Set your Razorpay Test Keys in backend/.env")
    exit(1)

print("Authenticating with Razorpay...")
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

# ---------------------------------------------------------------------------
# NOTE: We use client.order.create() — NOT payment_link.create().
# Payment Links are capped at 30 in Razorpay test mode.
# Orders have no such limit and trigger the same payment.captured webhook.
# ---------------------------------------------------------------------------

COUNT = 10
print(f"\nCreating {COUNT} Razorpay Orders (no test-mode limit)...")
print("Complete any order in the Razorpay Dashboard to fire a payment.captured webhook.\n")

dashboard_url = f"https://dashboard.razorpay.com/app/orders"

for i in range(1, COUNT + 1):
    profile = random.choice(["SAFE", "SAFE", "SAFE", "MEDIUM", "HIGH"])

    if profile == "SAFE":
        amount = random.randint(10000, 49999)   # < ₹500 (paise)
        notes = {
            "risk_profile": "SAFE",
            "expected_country": "IN",
            "ip_country": "IN",
            "card_bin": "555555",
        }
    elif profile == "MEDIUM":
        amount = random.randint(1200000, 1250000)  # ~₹12,000
        notes = {
            "risk_profile": "MEDIUM",
            "expected_country": "IN",
            "ip_country": "IN",
            "card_bin": "444444",
        }
    else:  # HIGH
        amount = random.randint(5000000, 5100000)  # ~₹50,000
        notes = {
            "risk_profile": "HIGH",
            "expected_country": "US",
            "ip_country": "RU",   # Geographic mismatch → fires LOCATION_MISMATCH signal
            "card_bin": "444444",
        }

    try:
        order = client.order.create({
            "amount":   amount,
            "currency": "INR",
            "notes":    notes,
        })
        order_id = order.get("id", "N/A")
        print(f"[{i:02d}/{COUNT}] {profile:<6} | ₹{amount/100:>10,.2f} | Order: {order_id}")
        time.sleep(0.5)   # stay within rate limits

    except Exception as e:
        print(f"[{i:02d}/{COUNT}] ❌ Failed to create order: {e}")

print(f"""
✅  Done! {COUNT} Orders created.

👉  Next Steps:
    1. Open the Razorpay Dashboard → Orders:
       {dashboard_url}

    2. Click any order → "Generate Payment Link" (or pay via test checkout).

    3. Use a Razorpay Test Card to complete the payment:
       Card : 4111 1111 1111 1111
       CVV  : 123   Expiry: 12/29

    4. Razorpay fires a payment.captured webhook to your server.

    5. The ML fraud pipeline runs and the case appears in your Dashboard.
""")
