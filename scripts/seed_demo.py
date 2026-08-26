import asyncio
import uuid
import datetime
from app.schemas.models import NormalizedTransaction
from app.services.risk_service import process_transaction
from app.database import connect_to_mongo, close_mongo_connection

async def seed_demo():
    print("Connecting to database...")
    await connect_to_mongo()
    
    print("Seeding demo transactions...")
    txs = [
        NormalizedTransaction(
            transaction_id=str(uuid.uuid4()),
            merchant_id="M_1001",
            customer_id="C_2001",
            amount=450,
            timestamp=datetime.datetime.utcnow().isoformat(),
            payment_method="UPI",
            device={"ip_address": "192.168.1.1", "device_id": "DEV_A"},
            metadata={"expected_country": "IN", "ip_country": "IN"}
        ),
        NormalizedTransaction(
            transaction_id=str(uuid.uuid4()),
            merchant_id="M_1002",
            customer_id="C_2002",
            amount=48500,
            timestamp=datetime.datetime.utcnow().isoformat(),
            payment_method="CARD",
            device={"ip_address": "45.22.11.9", "device_id": "DEV_B"},
            metadata={
                "expected_country": "IN", 
                "ip_country": "US",
                "is_high_velocity": True,
                "tx_count_1h": 7
            }
        )
    ]
    
    for tx in txs:
        case = await process_transaction(tx)
        print(f"Processed TX {tx.transaction_id} -> Risk Level: {case.risk_level}")
        
    print("Demo seeding complete.")
    await close_mongo_connection()

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
    asyncio.run(seed_demo())
