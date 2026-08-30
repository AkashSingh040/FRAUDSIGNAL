from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.schemas.models import NormalizedTransaction, RiskCase
from app.services.risk_service import process_transaction
from app.risk.model_loader import model_loader

router = APIRouter()

@router.post("/score", response_model=RiskCase)
async def score_transaction(tx: NormalizedTransaction):
    """
    Ingest a normalized transaction, run it through the risk engine, 
    generate signals, run AI investigation, and return the created RiskCase.
    """
    try:
        case = await process_transaction(tx)
        return case
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_model_status():
    """
    Returns the status of the ML model.
    """
    return model_loader.get_status()

async def run_seed_background():
    import random
    import uuid
    import datetime
    
    txs = []
    countries = ["IN", "US", "UK", "SG", "AE"]
    methods = ["UPI", "CARD", "NETBANKING", "WALLET"]
    
    def random_ip():
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    
    # 5 Safe
    for _ in range(5):
        txs.append(
            NormalizedTransaction(
                transaction_id=f"pay_{uuid.uuid4().hex[:14]}",
                merchant_id=f"M_{random.randint(1000, 9999)}",
                customer_id=f"C_{random.randint(10000, 99999)}",
                amount=random.randint(50, 4500),
                timestamp=datetime.datetime.utcnow().isoformat(),
                payment_method=random.choice(methods),
                device={"ip_address": random_ip(), "device_id": f"DEV_{uuid.uuid4().hex[:8]}"},
                metadata={"expected_country": "IN", "ip_country": "IN"}
            )
        )
        
    # 3 Medium
    for _ in range(3):
        txs.append(
            NormalizedTransaction(
                transaction_id=f"pay_{uuid.uuid4().hex[:14]}",
                merchant_id=f"M_{random.randint(1000, 9999)}",
                customer_id=f"C_{random.randint(10000, 99999)}",
                amount=random.randint(12000, 48000),
                timestamp=datetime.datetime.utcnow().isoformat(),
                payment_method=random.choice(methods),
                device={"ip_address": random_ip(), "device_id": f"DEV_{uuid.uuid4().hex[:8]}"},
                metadata={"expected_country": "IN", "ip_country": "IN"}
            )
        )
        
    # 2 High
    for _ in range(2):
        txs.append(
            NormalizedTransaction(
                transaction_id=f"pay_{uuid.uuid4().hex[:14]}",
                merchant_id=f"M_{random.randint(1000, 9999)}",
                customer_id=f"C_{random.randint(10000, 99999)}",
                amount=random.randint(52000, 95000),
                timestamp=datetime.datetime.utcnow().isoformat(),
                payment_method=random.choice(methods),
                device={"ip_address": random_ip(), "device_id": f"DEV_{uuid.uuid4().hex[:8]}"},
                metadata={
                    "expected_country": "IN", 
                    "ip_country": random.choice(["US", "UK", "RU", "NG"]),
                    "is_high_velocity": True,
                    "tx_count_1h": random.randint(7, 15)
                }
            )
        )
        
    for tx in txs:
        try:
            await process_transaction(tx)
        except Exception as e:
            print(f"Error seeding tx {tx.transaction_id}: {e}")

@router.post("/seed")
async def seed_demo_data(background_tasks: BackgroundTasks):
    """
    Trigger the background generation of 10 random transactions 
    bypassing Razorpay webhook for demo purposes.
    """
    background_tasks.add_task(run_seed_background)
    return {"message": "Seeding started in background. Cases will appear shortly.", "count": 10}
