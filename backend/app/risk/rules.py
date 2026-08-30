from typing import List, Dict, Any
from app.schemas.models import NormalizedTransaction, RiskSignal
import uuid

VELOCITY_THRESHOLD = 3  # max transactions allowed per customer per hour

from datetime import datetime

def generate_signals(tx: NormalizedTransaction, velocity_count: int = 0, historical_data: Dict[str, Any] = None) -> List[RiskSignal]:
    signals = []
    
    # 1. Amount Anomaly
    avg_amount = historical_data.get("avg_amount") if historical_data else None
    if avg_amount and avg_amount > 0:
        # Customer-relative thresholds (median/percentile preferred if data supports it)
        if tx.amount > avg_amount * 5:
            signals.append(RiskSignal(
                signal_id="UNUSUAL_AMOUNT_RELATIVE",
                title="Unusually high transaction amount (relative)",
                severity="HIGH",
                description=f"Transaction amount of {tx.amount} is over 5x the customer's historical average of {avg_amount:.2f}.",
                evidence={"observed_amount": tx.amount, "historical_avg": round(avg_amount, 2), "multiplier": 5},
                source="derived",
                confidence=0.9
            ))
        elif tx.amount > avg_amount * 2:
            signals.append(RiskSignal(
                signal_id="ELEVATED_AMOUNT_RELATIVE",
                title="Elevated transaction amount (relative)",
                severity="MEDIUM",
                description=f"Transaction amount of {tx.amount} is over 2x the customer's historical average of {avg_amount:.2f}.",
                evidence={"observed_amount": tx.amount, "historical_avg": round(avg_amount, 2), "multiplier": 2},
                source="derived",
                confidence=0.7
            ))
    else:
        # Cold-start fixed thresholds
        if tx.amount >= 50000:
            signals.append(RiskSignal(
                signal_id="UNUSUAL_AMOUNT",
                title="Unusually high transaction amount",
                severity="HIGH",
                description=f"Transaction amount of {tx.amount} exceeds the absolute threshold.",
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

    # 2. Velocity — Multi-level (Includes check for simulated velocity)
    simulated_velocity = False
    if tx.metadata and tx.metadata.get("is_high_velocity"):
        simulated_velocity = True
        
    if velocity_count > 6 or simulated_velocity:
        signals.append(RiskSignal(
            signal_id="CRITICAL_VELOCITY",
            title="Critical transaction velocity",
            severity="HIGH",
            description=f"Customer made {velocity_count} transactions in the last hour (> 6 threshold).",
            evidence={"transactions_last_hour": velocity_count, "threshold": 6},
            source="derived",
            confidence=0.9
        ))
    elif velocity_count > 3:
        signals.append(RiskSignal(
            signal_id="ELEVATED_VELOCITY",
            title="Elevated transaction velocity",
            severity="MEDIUM",
            description=f"Customer made {velocity_count} transactions in the last hour (> 3 threshold).",
            evidence={"transactions_last_hour": velocity_count, "threshold": 3},
            source="derived",
            confidence=0.7
        ))
        
    # 3. Device / Location
    if tx.device and tx.device.ip_address and tx.metadata:
        ip_country = tx.metadata.get("ip_country")
        expected_country = tx.metadata.get("expected_country")
        if ip_country and expected_country and ip_country != expected_country:
            # Downgraded to MEDIUM due to VPN commonality
            signals.append(RiskSignal(
                signal_id="LOCATION_MISMATCH",
                title="Geographic location mismatch",
                severity="MEDIUM",
                description=f"IP country ({ip_country}) does not match expected customer country ({expected_country}).",
                evidence={
                    "ip_address": tx.device.ip_address,
                    "ip_country": ip_country,
                    "expected": expected_country
                },
                source="derived",
                confidence=0.75
            ))
            
    # 4. New Device Detection
    if historical_data and tx.device:
        known_devices = historical_data.get("known_devices", [])
        device_identifier = tx.device.device_id or tx.device.ip_address
        
        if known_devices and device_identifier and device_identifier not in known_devices:
            signals.append(RiskSignal(
                signal_id="NEW_DEVICE",
                title="New device detected",
                severity="MEDIUM",
                description=f"Transaction initiated from an unrecognised device/IP: {device_identifier}.",
                evidence={"observed_device": device_identifier, "known_devices_count": len(known_devices)},
                source="derived",
                confidence=0.8
            ))

    # 5. Time/Pattern Anomalies (e.g. 2:00 AM - 5:00 AM UTC)
    try:
        dt = datetime.fromisoformat(tx.timestamp.replace("Z", "+00:00"))
        if 2 <= dt.hour <= 5:
            severity = "MEDIUM" if tx.amount > 10000 else "LOW"
            signals.append(RiskSignal(
                signal_id="UNUSUAL_TIME",
                title="Unusual transaction time",
                severity=severity,
                description=f"Transaction occurred at an unusual hour ({dt.hour}:00 UTC).",
                evidence={"hour_utc": dt.hour},
                source="derived",
                confidence=0.6
            ))
    except Exception:
        pass

    return signals

def evaluate_risk(tx: NormalizedTransaction, model_prob: float = None, velocity_count: int = 0, historical_data: Dict[str, Any] = None) -> Dict[str, Any]:
    signals = generate_signals(tx, velocity_count=velocity_count, historical_data=historical_data)
    
    # Calculate base risk from rules
    score = 0
    high_count = 0
    medium_count = 0
    
    for s in signals:
        if s.severity == "HIGH":
            score += 30
            high_count += 1
        elif s.severity == "MEDIUM":
            score += 15
            medium_count += 1
        elif s.severity == "LOW":
            score += 5
            
    # Compounding penalties for multiple risk factors
    if medium_count >= 3:
        score += 15
    
    if high_count >= 2:
        score += 20
    # Integrate ML Model if available
    if model_prob is not None:
        from app.risk.model_loader import model_loader
        optimal_thresh = model_loader.optimal_threshold
        
        # Calculate model contribution (scale probability based on the threshold)
        # If probability == threshold, model_score is 50.
        # If probability = 1, model_score is 100.
        if model_prob >= optimal_thresh:
            # Scale from 50 to 100
            divisor = max(1e-6, 1.0 - optimal_thresh)
            model_score = 50 + int(((model_prob - optimal_thresh) / divisor) * 50)
        else:
            # Scale from 0 to 50
            divisor = max(1e-6, optimal_thresh)
            model_score = int((model_prob / divisor) * 50)
            
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

    # Signal-based floor: the ML model must not bury cases with real observable signals.
    has_high  = any(s.severity == "HIGH"   for s in signals if s.source != "model")
    has_medium = any(s.severity == "MEDIUM" for s in signals if s.source != "model")
    
    # If a rule was blatantly violated, the rules engine acts as a circuit breaker, overriding the ML model
    if has_high and final_score < 70:
        final_score = 70
    elif has_medium and final_score < 30:
        final_score = 30

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
