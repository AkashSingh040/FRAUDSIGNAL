import os
import json
import logging
from typing import Dict, Any, Optional
from groq import Groq
from app.config import settings
from app.schemas.models import InvestigationReport, ActionDecision

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # We still read from LLM_API_KEY but pass to Groq
        self.api_key = settings.LLM_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def _deterministic_fallback(self, case_context: Dict[str, Any]) -> InvestigationReport:
        logger.info("Using deterministic investigation fallback.")
        signals = case_context.get("signals", [])
        risk_score = case_context.get("risk_score", 0)
        
        evidence = [f"{s['title']}: {s['description']}" for s in signals]
        reasoning = ["Multiple independent signals indicate anomalous payment behavior."] if len(signals) > 1 else ["A single risk signal was detected."]
        
        if risk_score >= 90:
            rec = ActionDecision.BLOCK
            summary = "Critical risk transaction with strong fraud indicators."
        elif risk_score >= 70:
            rec = ActionDecision.MANUAL_REVIEW
            summary = "High risk transaction requiring manual verification."
        elif risk_score >= 30:
            rec = ActionDecision.MONITOR
            summary = "Medium risk transaction. Monitoring advised."
        else:
            rec = ActionDecision.APPROVE
            summary = "Low risk transaction. Normal patterns observed."
            
        return InvestigationReport(
            summary=summary,
            risk_assessment=f"Risk Score is {risk_score}.",
            evidence=evidence if evidence else ["No significant evidence found."],
            reasoning=reasoning,
            uncertainties=["No definitive external evidence (like account takeover confirmation) is available."],
            recommended_action=rec,
            confidence=0.8
        )

    def investigate(self, case_context: Dict[str, Any]) -> InvestigationReport:
        if not self.client:
            return self._deterministic_fallback(case_context)
            
        system_prompt = """
        You are an elite forensic fraud risk investigator. You are analyzing a transaction payload that has been flagged by our ML engine.
        Your job is to provide a highly detailed, transaction-specific investigation report. DO NOT use generic boilerplate language. 
        You MUST explicitly reference the exact values from the JSON context provided (e.g., mention the specific transaction amount, the actual email domain, or the exact card brand).
        
        Return a JSON object strictly matching this schema:
        {
            "summary": "A 2-3 sentence forensic summary of exactly what looks suspicious about this specific transaction.",
            "risk_assessment": "A detailed interpretation of the risk score in relation to the specific signals triggered.",
            "evidence": ["Factual evidence point 1 referencing specific data...", "Factual evidence point 2..."],
            "reasoning": ["Logical deduction 1 based on the evidence...", "Logical deduction 2..."],
            "uncertainties": ["List any missing data points that prevent a 100% confident conclusion (e.g., 'Device fingerprint is absent')."],
            "recommended_action": "APPROVE" | "MONITOR" | "MANUAL_REVIEW" | "BLOCK",
            "confidence": 0.0 to 1.0 (float)
        }
        Base everything ONLY on the provided context.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL or "llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(case_context, default=str)}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_completion_tokens=2048,
                top_p=0.9,
                stream=True
            )
            
            content = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content += chunk.choices[0].delta.content
                    
            parsed = json.loads(content)
            
            return InvestigationReport(**parsed)
        except Exception as e:
            logger.error(f"LLM Investigation failed: {e}")
            return self._deterministic_fallback(case_context)

llm_service = LLMService()
