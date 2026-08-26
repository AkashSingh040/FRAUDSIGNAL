from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class CaseStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    REVIEW = "REVIEW"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"

class ActionDecision(str, Enum):
    APPROVE = "APPROVE"
    MONITOR = "MONITOR"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCK = "BLOCK"

# --- Transaction ---
class DeviceInfo(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None

class NormalizedTransaction(BaseModel):
    transaction_id: str
    merchant_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    timestamp: str
    payment_method: str
    device: Optional[DeviceInfo] = None
    metadata: Optional[Dict[str, Any]] = None

# --- Risk ---
class RiskSignal(BaseModel):
    signal_id: str
    title: str
    severity: str
    description: str
    evidence: Dict[str, Any]
    source: str  # observed, derived, model
    confidence: float

class RiskAssessment(BaseModel):
    risk_score: int
    risk_level: RiskLevel
    fraud_probability: Optional[float] = None
    signals: List[RiskSignal]
    decision: ActionDecision
    model_version: Optional[str] = None

# --- Investigation ---
class InvestigationReport(BaseModel):
    summary: str
    risk_assessment: str
    evidence: List[str]
    reasoning: List[str]
    uncertainties: List[str]
    recommended_action: ActionDecision
    confidence: float

# --- Case ---
class RiskCase(BaseModel):
    case_id: str
    transaction_id: str
    merchant_id: str
    customer_id: str
    risk_score: int
    risk_level: RiskLevel
    signals: List[RiskSignal]
    evidence: Dict[str, Any]
    investigation: Optional[InvestigationReport] = None
    status: CaseStatus = CaseStatus.OPEN
    recommended_action: Optional[ActionDecision] = None
    final_decision: Optional[ActionDecision] = None
    decision_reason: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str

class CaseDecisionUpdate(BaseModel):
    decision: ActionDecision
    reason: str
