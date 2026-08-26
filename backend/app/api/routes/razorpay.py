from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Dict, Any
from app.services.razorpay_service import razorpay_service
from app.schemas.models import NormalizedTransaction
from app.services.risk_service import process_transaction
import datetime

router = APIRouter()

@router.post("/simulate-webhook")
async def simulate_webhook(amount: int = 50000, event_type: str = "payment.captured"):
    """
    Generate a dummy Razorpay webhook payload and process it 
    through the risk engine for localhost testing.
    """
    try:
        # Generate dummy data
        payload = razorpay_service.generate_dummy_webhook_payload(event_type, amount)
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        if not payment_data:
            raise ValueError("Invalid payload structure generated.")

        # Normalize the Razorpay payment object into our NormalizedTransaction
        tx = NormalizedTransaction(
            transaction_id=payment_data.get("id"),
            merchant_id="dummy_merchant",
            customer_id=payment_data.get("email", "unknown_customer"),
            amount=payment_data.get("amount", 0) / 100, # Assuming Razorpay amount is in paise
            currency=payment_data.get("currency", "INR"),
            timestamp=datetime.datetime.utcnow().isoformat(),
            payment_method=payment_data.get("method", "unknown"),
            device={"ip_address": "127.0.0.1", "device_id": "SIM_DEV"},
            metadata={
                "card_network": payment_data.get("card", {}).get("network"),
                "card_type": payment_data.get("card", {}).get("type"),
                "is_dummy": True
            }
        )
        
        # Process asynchronously (or synchronously for the demo)
        case = await process_transaction(tx)
        
        return {
            "status": "success", 
            "message": "Simulated webhook processed.", 
            "case_id": case.case_id,
            "risk_score": case.risk_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """
    Actual Razorpay webhook endpoint (stub).
    In production, you'd verify `x-razorpay-signature` here.
    """
    payload = await request.json()
    # Signature verification logic goes here...
    
    # Normally, we'd enqueue this or process it similarly to simulate_webhook
    return {"status": "ok"}
