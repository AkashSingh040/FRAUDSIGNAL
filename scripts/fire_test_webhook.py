"""
fire_test_webhook.py
--------------------
Uses a new set of Razorpay keys (from scripts/ans.env) to generate Payment Links.
These links are printed out so you can manually pay them.
Razorpay will then fire the webhook to your backend URL (which you must configure in the Razorpay dashboard).
"""

import os
import random
import time
import razorpay
from dotenv import load_dotenv

# Load keys from scripts/.env
load_dotenv(dotenv_path="scripts/.env", override=True)

KEY_ID     = os.getenv("RAZORPAY_KEY_ID",     "YOUR_NEW_TEST_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_NEW_TEST_KEY_SECRET")

COUNT = 2   # number of test payment links to generate

if KEY_ID == "YOUR_NEW_TEST_KEY_ID":
    print("⚠️  Error: Set your new Razorpay Test Keys in scripts/.env")
    exit(1)

print("Authenticating with Razorpay...")
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

# ── Risk profiles ────────────────────────────────────────────────────────────
PROFILES = {
    "SAFE": {
        "amount_range": (10000, 49900),   # paise  (~₹100 – ₹499)
        "email":  "safe@user.com",
        "ip":     "103.21.244.10",         # India IP
        "notes": {
            "risk_profile":     "SAFE",
            "expected_country": "IN",
            "ip_country":       "IN",
            "card_bin":         "555555",
        },
    },
    "MEDIUM": {
        "amount_range": (1200000, 1250000),  # ~₹12,000
        "email":  "medium@user.com",
        "ip":     "103.21.244.20",           # India IP
        "notes": {
            "risk_profile":     "MEDIUM",
            "expected_country": "IN",
            "ip_country":       "IN",
            "card_bin":         "444444",
        },
    },
    "HIGH": {
        "amount_range": (5000000, 5100000),  # ~₹50,000
        "email":  "suspicious@hacker.com",
        "ip":     "95.142.47.100",           # Russian IP — mismatch with expected US
        "notes": {
            "risk_profile":     "HIGH",
            "expected_country": "US",
            "ip_country":       "RU",        # triggers LOCATION_MISMATCH signal
            "card_bin":         "444444",
        },
    },
}

print(f"\n🚀  Generating {COUNT} Payment Links...\n")

for i in range(1, COUNT + 1):
    profile_name = random.choice(["SAFE", "SAFE", "SAFE", "MEDIUM", "HIGH"])
    cfg          = PROFILES[profile_name]
    amount       = random.randint(*cfg["amount_range"])

    try:
        payment_link = client.payment_link.create({
            "amount": amount,
            "currency": "INR",
            "accept_partial": False,
            "description": f"Test Transaction - {profile_name} Risk",
            "customer": {
                "name": cfg["email"].split("@")[0],
                "email": cfg["email"],
                "contact": "+919876543210"
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False,
            "notes": cfg["notes"]
        })
        
        pl_url = payment_link.get("short_url", "N/A")
        print(f"[{i:02d}/{COUNT}] {profile_name:<6} | ₹{amount/100:>10,.2f} | Link: {pl_url}")
        
    except Exception as e:
        print(f"[{i:02d}/{COUNT}] ❌ Failed to create Payment Link: {e}")
        
    time.sleep(0.5)

print(f"""
✅  Done! {COUNT} Payment Links generated.

👉  Next Steps:
    1. Click on the generated links above and pay using a test card.
    2. Since you are using a new Razorpay account, make sure you have 
       configured the webhook in your Razorpay Dashboard to point to your 
       Render backend (`https://fraudsignal-api.onrender.com/api/v1/razorpay/webhook`).
    3. Ensure the `RAZORPAY_WEBHOOK_SECRET` in your backend `.env` matches 
       the one set in your new Razorpay account dashboard.
""")
