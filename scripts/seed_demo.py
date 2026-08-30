import asyncio
import uuid
import datetime
from app.schemas.models import NormalizedTransaction
from app.services.risk_service import process_transaction
from app.database import connect_to_mongo, close_mongo_connection

async def seed_demo():
    print("Connecting to database...")
    await connect_to_mongo()
    
    import random
    
    print("Seeding 10 demo transactions with random data...")
    txs = []
    
    countries = ["IN", "US", "UK", "SG", "AE"]
    methods = ["UPI", "CARD", "NETBANKING", "WALLET"]
    
    def random_ip():
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    
    # 5 Safe Transactions
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
        
    # 3 Medium Risk Transactions (Elevated Amount)
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
        
    # 2 High Risk Transactions (High Amount, Location Mismatch, High Velocity)
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
        case = await process_transaction(tx)
        print(f"Processed TX {tx.transaction_id} -> Risk Level: {case.risk_level}")
        
    print("Demo seeding complete.")
    await close_mongo_connection()

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
    asyncio.run(seed_demo())
