import hmac
import hashlib
import json
import os
import urllib.request
import urllib.error
import time
from dotenv import load_dotenv

load_dotenv()

# We will fire this directly to your live Render server!
RENDER_URL = "https://fraudsignal-api.onrender.com/api/v1/razorpay/webhook"
SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

if not SECRET:
    print("❌ Could not find RAZORPAY_WEBHOOK_SECRET in .env")
    exit(1)

def send_mock_webhook():
    print("--- Forcing a mock 'payment.captured' webhook directly to Render...")
    print(f"--- Target: {RENDER_URL}")
    print(f"--- Using Secret: {SECRET}")

    # 1. Create a perfectly structured Razorpay Webhook Payload
    payload_dict = {
        "entity": "event",
        "account_id": "acc_12345",
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_mock_{int(time.time())}",
                    "entity": "payment",
                    "amount": 99900,
                    "currency": "INR",
                    "status": "captured",
                    "method": "card",
                    "order_id": f"order_mock_{int(time.time())}",
                    "description": "Mocked Black-Box Test",
                    "amount_refunded": 0,
                    "refund_status": None,
                    "email": "hacker_test@fraudsignal.com",
                    "contact": "+919876543210",
                    "notes": {
                        "V1": 1,
                        "V3": 999,
                        "V5": 999,
                        "V10": 999,
                        "test_reason": "Forcing ML Model Execution"
                    },
                    "fee": 2000,
                    "tax": 0,
                    "error_code": None,
                    "error_description": None,
                    "error_source": None,
                    "error_step": None,
                    "error_reason": None,
                    "bank": None,
                    "wallet": None,
                    "vpa": None,
                    "card": {
                        "id": "card_12345",
                        "entity": "card",
                        "name": "Test User",
                        "last4": "1111",
                        "network": "Visa",
                        "type": "credit",
                        "issuer": "UTIB",
                        "international": False,
                        "emi": False,
                        "sub_type": "consumer"
                    },
                    "created_at": int(time.time())
                }
            }
        },
        "created_at": int(time.time())
    }

    # 2. Serialize to exact JSON string (no spaces, like Razorpay)
    body = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')

    # 3. Cryptographically sign the body using HMAC SHA256
    signature = hmac.new(SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()

    # 4. Fire the HTTP POST Request
    req = urllib.request.Request(RENDER_URL, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('x-razorpay-signature', signature)
    
    try:
        response = urllib.request.urlopen(req)
        status = response.getcode()
        resp_body = response.read().decode('utf-8')
        
        print("\n--- Webhook delivered successfully!")
        print(f"   HTTP Status: {status}")
        print(f"   Response: {resp_body}")
        
        print("\n--- Next Steps:")
        print("1. Your ML model is running on Render right now!")
        print("2. Wait 5-10 seconds for Groq to write the investigation.")
        print("3. Check your Vercel Dashboard, you should see a High Risk case!")
        
    except urllib.error.HTTPError as e:
        print("\n--- Webhook delivery failed!")
        print(f"   HTTP Status: {e.code}")
        print(f"   Response: {e.read().decode('utf-8')}")
        print("   If you see 400 Invalid Signature, the secret on Render does not match the script.")

if __name__ == "__main__":
    send_mock_webhook()
