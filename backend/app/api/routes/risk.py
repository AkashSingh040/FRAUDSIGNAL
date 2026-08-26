from fastapi import APIRouter, HTTPException
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
