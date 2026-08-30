from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.models import RiskCase, CaseDecisionUpdate
from app.services.risk_service import get_case, update_case_decision
from app.database import get_database

router = APIRouter()

@router.get("/")
async def list_cases():
    db = get_database()
    cases = await db.cases.find().sort("created_at", -1).to_list(100)
    
    # Safely return cases without strict Pydantic validation to prevent crashes from old schema data
    safe_cases = []
    for c in cases:
        if "_id" in c:
            c["_id"] = str(c["_id"])
        safe_cases.append(c)
        
    return safe_cases

@router.get("/{case_id}", response_model=RiskCase)
async def read_case(case_id: str):
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/{case_id}")
async def make_decision(case_id: str, update: CaseDecisionUpdate):
    success = await update_case_decision(case_id, update.decision.value, update.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Case not found or not updated")
    return {"status": "success", "message": "Decision saved."}
