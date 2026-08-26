import requests
import uuid
import time
from typing import Dict, Any

class RazorpayService:
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.auth = (self.key_id, self.key_secret) if self.key_id and self.key_secret else None
        
    def create_order(self, amount: int, currency: str = "INR", receipt: str = None) -> Dict[str, Any]:
        """Creates a Razorpay order or a dummy one if no keys are provided."""
        if not self.auth:
            return {
                "id": f"order_{uuid.uuid4().hex[:14]}",
                "entity": "order",
                "amount": amount,
                "amount_paid": 0,
                "amount_due": amount,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "attempts": 0,
                "created_at": int(time.time())
            }
            
        url = "https://api.razorpay.com/v1/orders"
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt
        }
        resp = requests.post(url, auth=self.auth, json=data)
        return resp.json()

    def generate_dummy_webhook_payload(self, event_type: str = "payment.captured", amount: int = 50000) -> Dict[str, Any]:
        """Generates dummy Razorpay webhook data for localhost testing."""
        return {
            "entity": "event",
            "account_id": "acc_dummy123",
            "event": event_type,
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4().hex[:14]}",
                        "entity": "payment",
                        "amount": amount,
                        "currency": "INR",
                        "status": "captured",
                        "order_id": f"order_{uuid.uuid4().hex[:14]}",
                        "invoice_id": None,
                        "international": False,
                        "method": "card",
                        "amount_refunded": 0,
                        "refund_status": None,
                        "captured": True,
                        "description": "Dummy transaction for testing",
                        "card_id": f"card_{uuid.uuid4().hex[:14]}",
                        "card": {
                            "id": f"card_{uuid.uuid4().hex[:14]}",
                            "entity": "card",
                            "name": "Test User",
                            "last4": "1111",
                            "network": "Visa",
                            "type": "credit",
                            "issuer": "HDFC",
                            "international": False,
                            "emi": False,
                            "sub_type": "consumer"
                        },
                        "bank": None,
                        "wallet": None,
                        "vpa": None,
                        "email": "test@example.com",
                        "contact": "+919999999999",
                        "fee": 100,
                        "tax": 18,
                        "error_code": None,
                        "error_description": None,
                        "created_at": int(time.time())
                    }
                }
            },
            "created_at": int(time.time())
        }

razorpay_service = RazorpayService("", "") # Will be initialized correctly in the router if needed
