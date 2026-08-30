import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.schemas.models import NormalizedTransaction, RiskAssessment, RiskCase, CaseStatus
from app.risk.rules import evaluate_risk
from app.risk.model_loader import model_loader
from app.services.llm_service import llm_service
from app.database import get_database

async def process_transaction(tx: NormalizedTransaction) -> RiskCase:
    db = get_database()
    
    # 1. Save Transaction
    tx_dict = tx.model_dump()
    await db.transactions.insert_one(tx_dict)
    
    # 2. Get Model Probability
    prob = model_loader.predict(tx_dict)
    
    # 3. Compute real velocity and historical profile from DB
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    
    # We MUST avoid data leakage by explicitly excluding the current transaction
    # even though it was just inserted into the DB in step 1.
    velocity_count = await db.transactions.count_documents({
        "customer_id": tx.customer_id,
        "timestamp": {"$gte": one_hour_ago},
        "transaction_id": {"$ne": tx.transaction_id}
    })
    
    # Get historical profile (avg amount, known devices)
    pipeline = [
        {"$match": {"customer_id": tx.customer_id, "transaction_id": {"$ne": tx.transaction_id}}},
        {"$group": {
            "_id": "$customer_id",
            "avg_amount": {"$avg": "$amount"},
            "devices": {"$addToSet": "$device.device_id"}
        }}
    ]
    cursor = db.transactions.aggregate(pipeline)
    hist_stats = await cursor.to_list(1)
    
    historical_data = None
    if hist_stats:
        historical_data = {
            "avg_amount": hist_stats[0].get("avg_amount"),
            "known_devices": hist_stats[0].get("devices", [])
        }
    
    # 4. Evaluate Risk (Rules + Model + Historical Context)
    assessment = evaluate_risk(tx, prob, velocity_count=velocity_count, historical_data=historical_data)
    
    # 4. Save Signals
    for sig in assessment["signals"]:
        sig_dict = sig.model_dump()
        sig_dict["transaction_id"] = tx.transaction_id
        await db.risk_signals.insert_one(sig_dict)
        
    # 5. Generate Investigation if suspicious (score >= 30 OR any HIGH signal present)
    investigation = None
    has_high_signal = any(s.severity == "HIGH" for s in assessment["signals"])
    if assessment["risk_score"] >= 30 or has_high_signal:
        case_context = {
            "transaction": tx_dict,
            "risk_score": assessment["risk_score"],
            "risk_level": assessment["risk_level"],
            "signals": [s.model_dump() for s in assessment["signals"]]
        }
        investigation_report = await llm_service.investigate(case_context)
        investigation = investigation_report
        
    # 6. Create Case
    case = RiskCase(
        case_id=str(uuid.uuid4()),
        transaction_id=tx.transaction_id,
        merchant_id=tx.merchant_id,
        customer_id=tx.customer_id,
        risk_score=assessment["risk_score"],
        risk_level=assessment["risk_level"],
        signals=assessment["signals"],
        evidence={"observed_amount": tx.amount, "model_prob": prob},
        investigation=investigation,
        status=CaseStatus.OPEN if (assessment["risk_score"] >= 30 or has_high_signal) else CaseStatus.RESOLVED,
        recommended_action=investigation.recommended_action if investigation else None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    
    case_dict = case.model_dump()
    await db.cases.insert_one(case_dict)
    
    return case

async def get_case(case_id: str) -> Optional[RiskCase]:
    db = get_database()
    case_dict = await db.cases.find_one({"case_id": case_id})
    if case_dict:
        return RiskCase(**case_dict)
    return None

async def update_case_decision(case_id: str, decision: str, reason: str) -> bool:
    db = get_database()
    result = await db.cases.update_one(
        {"case_id": case_id},
        {"$set": {
            "final_decision": decision,
            "decision_reason": reason,
            "status": CaseStatus.RESOLVED.value,
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    return result.modified_count > 0
