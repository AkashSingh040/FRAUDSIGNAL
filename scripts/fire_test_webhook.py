import os
import time
import razorpay
from dotenv import load_dotenv

# Load keys from the backend .env if running locally
load_dotenv(dotenv_path="backend/.env")

# Fallback keys (replace if you aren't using a .env file)
KEY_ID = os.getenv("RAZORPAY_KEY_ID", "YOUR_TEST_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_TEST_KEY_SECRET")

if KEY_ID == "YOUR_TEST_KEY_ID":
    print("⚠️ Error: Please set your Razorpay Test Keys in this script or in backend/.env")
    exit(1)

print("Authenticating with Razorpay...")
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

import random

print("Creating 10 real Razorpay Orders to trigger 'order.created' webhooks...")
print("IMPORTANT: This script only creates Orders. This verifies webhook connectivity.")
print("To test the full ML fraud pipeline, you must complete a payment on these orders")
print("using the Razorpay Dashboard or your frontend integration with a Razorpay Test Card.")

for i in range(1, 11):
    # Determine risk profile randomly
    profile = random.choice(["SAFE", "SAFE", "SAFE", "MEDIUM", "HIGH"])
    
    amount = 50000 + random.randint(100, 5000) # Default safe amount (500 INR)
    notes = {}
    
    if profile == "SAFE":
        notes = {
            "expected_country": "IN",
            "ip_country": "IN",
            "card_bin": 5555,
            "tx_count_1h": 1,
            "V1": 0, "V3": 0
        }
    elif profile == "MEDIUM":
        amount = 1200000 + random.randint(1000, 50000) # ~12,000 INR
        notes = {
            "is_high_velocity": True,
            "tx_count_1h": 6,
            "expected_country": "IN",
            "ip_country": "IN",
            "card_bin": 4444,
            "V1": 1, "V3": 10
        }
    elif profile == "HIGH":
        amount = 5000000 + random.randint(10000, 100000) # ~50,000 INR
        notes = {
            "is_high_velocity": True,
            "tx_count_1h": 15,
            "expected_country": "US",
            "ip_country": "RU", # Location mismatch
            "card_bin": 4444,
            "V1": 1, "V3": 999, "V5": 999
        }

    # Creating a Payment Link instead of an Order.
    # This allows you to open a URL in your browser and make a test payment without needing a frontend!
    payment_link = client.payment_link.create({
        "amount": amount,
        "currency": "INR",
        "description": f"{profile} Risk Profile Test",
        "customer": {
            "name": "Test User",
            "email": "suspicious@hacker.com" if profile == "HIGH" else "safe@user.com",
            "contact": "+919876543210"
        },
        "notes": notes,
        "callback_url": "https://google.com",
        "callback_method": "get"
    })
    
    link_url = payment_link.get('short_url')
    print(f"[{i}/10] {profile} Risk | Amount: {amount/100} INR")
    print(f"       🔗 Pay here: {link_url}")
    time.sleep(1.5) # Sleep briefly to avoid hitting rate limits

print("\n✅ Success! 10 Payment Links created on Razorpay.")
print("\n👉 Next Steps:")
print("1. Click any of the URLs above.")
print("2. It will open a real Razorpay Test Checkout page in your browser.")
print("3. Enter a Razorpay Test Card (e.g., Card: 4111 1111 1111 1111, CVV: 123, Expiry: 12/29).")
print("4. When you complete the payment, Razorpay's servers will instantly fire the 'payment.captured' webhook.")
print("5. Your Render server will receive it, run the ML model, and the case will appear in your Vercel Dashboard!")
