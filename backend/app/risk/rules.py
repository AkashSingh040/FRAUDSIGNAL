from typing import List, Dict, Any
from app.schemas.models import NormalizedTransaction, RiskSignal
import uuid

def generate_signals(tx: NormalizedTransaction) -> List[RiskSignal]:
    signals = []
    
    # 1. Amount Anomaly
    if tx.amount > 50000:
        signals.append(RiskSignal(
            signal_id="UNUSUAL_AMOUNT",
            title="Unusually high transaction amount",
            severity="HIGH",
            description=f"Transaction amount of {tx.amount} exceeds the normal threshold.",
            evidence={"observed_amount": tx.amount, "threshold": 50000},
            source="observed",
            confidence=0.9
        ))
    elif tx.amount > 10000:
        signals.append(RiskSignal(
            signal_id="ELEVATED_AMOUNT",
            title="Elevated transaction amount",
            severity="MEDIUM",
            description=f"Transaction amount of {tx.amount} is slightly elevated.",
            evidence={"observed_amount": tx.amount},
            source="observed",
            confidence=0.7
        ))

    # 2. Velocity / Behavior Simulation (Normally relies on DB history)
    # For hackathon simulator, we read metadata hints if provided, else dummy
    if tx.metadata and tx.metadata.get("is_high_velocity"):
        signals.append(RiskSignal(
            signal_id="HIGH_VELOCITY",
            title="High transaction velocity",
            severity="HIGH",
            description="Multiple transactions detected in a short time frame.",
            evidence={"transactions_last_hour": tx.metadata.get("tx_count_1h", 5)},
            source="derived",
            confidence=0.85
        ))
        
    # 3. Device / Location
    if tx.device and tx.device.ip_address and tx.metadata and tx.metadata.get("expected_country"):
        if tx.metadata.get("ip_country") != tx.metadata.get("expected_country"):
            signals.append(RiskSignal(
                signal_id="LOCATION_MISMATCH",
                title="Geographic location mismatch",
                severity="HIGH",
                description="IP address location does not match expected customer location.",
                evidence={
                    "ip_address": tx.device.ip_address, 
                    "ip_country": tx.metadata.get("ip_country"),
                    "expected": tx.metadata.get("expected_country")
                },
                source="derived",
                confidence=0.95
            ))

    return signals

def evaluate_risk(tx: NormalizedTransaction, model_prob: float = None) -> Dict[str, Any]:
    signals = generate_signals(tx)
    
    # Calculate base risk from rules
    score = 0
    for s in signals:
        if s.severity == "HIGH":
            score += 30
        elif s.severity == "MEDIUM":
            score += 15
        elif s.severity == "LOW":
            score += 5
            
    # Integrate ML Model if available
    if model_prob is not None:
        from app.risk.model_loader import model_loader
        optimal_thresh = model_loader.optimal_threshold
        
        # Calculate model contribution (scale probability based on the threshold)
        # If probability == threshold, model_score is 50.
        # If probability = 1, model_score is 100.
        if model_prob >= optimal_thresh:
            # Scale from 50 to 100
            model_score = 50 + int(((model_prob - optimal_thresh) / (1.0 - optimal_thresh)) * 50)
        else:
            # Scale from 0 to 50
            model_score = int((model_prob / optimal_thresh) * 50)
            
        # Weighting: 60% ML, 40% Rules
        final_score = int((model_score * 0.6) + (min(score, 100) * 0.4))
        
        # Add model signal
        if model_prob >= optimal_thresh:
            signals.append(RiskSignal(
                signal_id="MODEL_HIGH_FRAUD_PROB",
                title="Model indicates high fraud probability",
                severity="HIGH",
                description=f"The ML model probability ({model_prob:.3f}) exceeded the optimal risk threshold ({optimal_thresh:.3f}).",
                evidence={"model_probability": round(model_prob, 3), "threshold": round(optimal_thresh, 3)},
                source="model",
                confidence=0.85
            ))
    else:
        # Rules only
        final_score = min(score, 100)

    # Determine level and decision
    if final_score >= 70:
        level = "HIGH"
        decision = "BLOCK" if final_score >= 90 else "MANUAL_REVIEW"
    elif final_score >= 30:
        level = "MEDIUM"
        decision = "MONITOR"
    else:
        level = "LOW"
        decision = "APPROVE"

    return {
        "risk_score": final_score,
        "risk_level": level,
        "fraud_probability": model_prob,
        "signals": signals,
        "decision": decision
    }
