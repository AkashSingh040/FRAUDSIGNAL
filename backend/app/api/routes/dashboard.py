from fastapi import APIRouter
from app.database import get_database

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary():
    db = get_database()
    
    total_tx = await db.transactions.count_documents({})
    cases = await db.cases.find().to_list(None)
    
    high_risk = sum(1 for c in cases if c.get("risk_level") == "HIGH")
    medium_risk = sum(1 for c in cases if c.get("risk_level") == "MEDIUM")
    open_inv = sum(1 for c in cases if c.get("status") in ["OPEN", "INVESTIGATING", "REVIEW"])
    confirmed_fraud = sum(1 for c in cases if c.get("status") == "CONFIRMED_FRAUD" or c.get("final_decision") == "BLOCK")
    
    avg_score = sum(c.get("risk_score", 0) for c in cases) / len(cases) if cases else 0
    fraud_rate = (confirmed_fraud / total_tx) * 100 if total_tx > 0 else 0
    
    return {
        "total_transactions": total_tx,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "open_investigations": open_inv,
        "confirmed_fraud": confirmed_fraud,
        "average_risk_score": round(avg_score, 1),
        "fraud_rate": round(fraud_rate, 2)
    }
