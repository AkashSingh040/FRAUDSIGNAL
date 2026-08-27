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

import hmac
import hashlib
import os
import json
import logging
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

@router.post("/webhook")
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Actual Razorpay webhook endpoint.
    Verifies `x-razorpay-signature` against RAZORPAY_WEBHOOK_SECRET.
    """
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    if not signature or not webhook_secret:
        logger.warning("Missing signature or webhook secret.")
        raise HTTPException(status_code=400, detail="Missing signature or secret")

    # Verify signature
    expected_sig = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        logger.warning("Invalid Razorpay signature.")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed payload")
        
    event_type = payload.get("event", "")
    
    # 1. Acknowledge order.created but do not process as payment
    if event_type == "order.created":
        logger.info("Received order.created. Acknowledging safely.")
        return {"status": "ok"}
        
    # 2. Process actual payment events
    # We ignore payment.authorized because payment.captured fires immediately after for auto-capture.
    # Processing both results in duplicate cases on the dashboard.
    if event_type in ["payment.captured", "payment.failed"]:
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        if payment_data:
            # Base metadata mapped from Razorpay
            tx_metadata = {
                "razorpay_event": event_type,
                "order_id": payment_data.get("order_id"),
                "payment_status": payment_data.get("status"),
                "card_network": payment_data.get("card", {}).get("network"),
                "card_type": payment_data.get("card", {}).get("type"),
                "card_brand": payment_data.get("card", {}).get("issuer"),
                "email_domain": payment_data.get("email", "").split("@")[-1] if "@" in payment_data.get("email", "") else "missing"
            }
            
            # Extract additional nested entities safely if they exist
            if payment_data.get("wallet"):
                tx_metadata["wallet"] = payment_data.get("wallet")
            if payment_data.get("bank"):
                tx_metadata["bank"] = payment_data.get("bank")
            if payment_data.get("vpa"):
                tx_metadata["vpa"] = payment_data.get("vpa")
            
            # Merge any custom 'notes' passed in the Razorpay transaction
            notes = payment_data.get("notes", {})
            if isinstance(notes, dict):
                tx_metadata.update(notes)

            # Build a unique ID for idempotency
            # By using the raw payment_id, MongoDB's unique index will block duplicates 
            # and our DuplicateKeyError try/except will safely ignore them!
            payment_id = payment_data.get("id")
            import time
            unique_tx_id = payment_id if payment_id else f"unknown_{event_type}_{int(time.time())}"

            try:
                # Map Razorpay's schema to FraudSignal's NormalizedTransaction
                # Fallbacks guarantee we don't pass `None` which would crash Pydantic validation
                tx = NormalizedTransaction(
                    transaction_id=unique_tx_id,
                    merchant_id="live_merchant",
                    customer_id=payment_data.get("email") or payment_data.get("contact") or "unknown_customer",
                    amount=(payment_data.get("amount") or 0) / 100, # Razorpay sends paise
                    currency=payment_data.get("currency") or "INR",
                    timestamp=str(payment_data.get("created_at")) if payment_data.get("created_at") else datetime.datetime.utcnow().isoformat(),
                    payment_method=payment_data.get("method") or "unknown",
                    device={"ip_address": payment_data.get("ip") or "0.0.0.0"},
                    metadata=tx_metadata
                )
            except Exception as e:
                logger.error(f"Validation Error creating NormalizedTransaction: {e}")
                raise HTTPException(status_code=400, detail="Invalid payload schema mapping")
            
            # Wrapper to handle DuplicateKeyError for Idempotency
            async def safe_process_transaction(transaction: NormalizedTransaction):
                try:
                    logger.info(f"Processing webhook event: {event_type} for Payment ID: {payment_id}")
                    await process_transaction(transaction)
                    logger.info(f"Fraud processing completed for {payment_id}")
                except DuplicateKeyError:
                    logger.warning(f"Duplicate transaction ignored: {transaction.transaction_id}")
                except Exception as e:
                    logger.error(f"Error processing transaction: {str(e)}")

            # Fire and forget processing so we respond to Razorpay within 200ms
            background_tasks.add_task(safe_process_transaction, tx)
            
    return {"status": "ok"}
