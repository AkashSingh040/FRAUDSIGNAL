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
        You are an expert fraud risk investigator. Analyze the provided transaction and risk signals.
        Return a JSON object matching this schema:
        {
            "summary": "Short paragraph summary",
            "risk_assessment": "Detailed interpretation of the risk",
            "evidence": ["list of factual evidence"],
            "reasoning": ["list of logical deductions"],
            "uncertainties": ["list of things that cannot be concluded"],
            "recommended_action": "APPROVE" | "MONITOR" | "MANUAL_REVIEW" | "BLOCK",
            "confidence": 0.0 to 1.0
        }
        Base everything ONLY on the provided context. Do not invent evidence.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(case_context, default=str)}
                ],
                response_format={"type": "json_object"},
                temperature=1,
                max_completion_tokens=2048,
                top_p=1,
                reasoning_effort="medium",
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
