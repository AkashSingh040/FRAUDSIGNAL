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
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Actual Razorpay webhook endpoint.
    In production, verify `x-razorpay-signature` against RAZORPAY_WEBHOOK_SECRET.
    """
    payload = await request.json()
    
    # Typically we check the event type, e.g. "payment.captured" or "payment.authorized"
    event_type = payload.get("event", "")
    
    if event_type.startswith("payment.") or event_type.startswith("order."):
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        if payment_data:
            # Base metadata mapped from Razorpay
            tx_metadata = {
                "card_network": payment_data.get("card", {}).get("network"),
                "card_type": payment_data.get("card", {}).get("type"),
                "card_brand": payment_data.get("card", {}).get("issuer"),
                "email_domain": payment_data.get("email", "").split("@")[-1] if "@" in payment_data.get("email", "") else "missing"
            }
            
            # Merge any custom 'notes' passed in the Razorpay transaction
            # This allows merchants (or our testing script) to pass IP location, velocity flags, etc.
            notes = payment_data.get("notes", {})
            if isinstance(notes, dict):
                tx_metadata.update(notes)

            # Map Razorpay's schema to FraudSignal's NormalizedTransaction
            tx = NormalizedTransaction(
                transaction_id=payment_data.get("id"),
                merchant_id="live_merchant",
                customer_id=payment_data.get("email", payment_data.get("contact", "unknown")),
                amount=payment_data.get("amount", 0) / 100, # Razorpay sends paise
                currency=payment_data.get("currency", "INR"),
                timestamp=datetime.datetime.utcnow().isoformat(),
                payment_method=payment_data.get("method", "unknown"),
                device={"ip_address": payment_data.get("ip", "0.0.0.0")},
                metadata=tx_metadata
            )
            
            # Fire and forget processing so we respond to Razorpay within 200ms
            background_tasks.add_task(process_transaction, tx)
            
    return {"status": "ok"}
