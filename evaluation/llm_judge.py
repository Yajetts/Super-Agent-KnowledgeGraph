"""LLM-based judge for completeness scoring."""

from __future__ import annotations

import json

from services.llm_service import get_llm_service


class LLMJudge:
    """Use LLM to evaluate response completeness and quality."""

    def __init__(self) -> None:
        self.llm_service = get_llm_service()

    def evaluate(self, query: str, response: str) -> float:
        """Evaluate response and return a score from 1-10."""
        prompt = f"""You are an expert evaluator of decision-support outputs.

Rate the following response on a scale of 1-10 based on:
- Completeness: Does it cover all relevant aspects of the query?
- Depth: Does it provide sufficient detail and analysis?
- Actionability: Are the recommendations specific and actionable?
- Decision usefulness: Would this help a decision-maker make an informed choice?

Query: {query}

Response:
{response}

Return only a single numeric score (1-10). No explanation, no text, just the number."""

        try:
            result = self.llm_service.generate(prompt)
            # Extract numeric score from response
            import re

            match = re.search(r"\b([1-9]|10)\b", result)
            if match:
                return float(match.group(1))
            # Fallback: try to parse the entire response as a number
            try:
                return float(result.strip())
            except ValueError:
                return 5.0  # Default middle score if parsing fails
        except Exception:
            return 5.0  # Default middle score on error

    def calculate_recommendation_quality(self, task: str, response: str) -> dict:
        """Calculate recommendation quality score with sub-dimensions."""
        prompt = f"""You are evaluating a decision-support system.

Task:
{task}

Response:
{response}

Rate the recommendations from 1-10 for:
1. Actionability - Are recommendations concrete and executable?
2. Specificity - Are recommendations tailored to the scenario?
3. Feasibility - Are recommendations realistic and implementable?
4. Strategic Value - Would the recommendations help a decision-maker?

Provide scores for each category and an overall Recommendation Quality Score.

Return JSON only:
{{
"actionability": float,
"specificity": float,
"feasibility": float,
"strategic_value": float,
"overall_score": float
}}"""

        try:
            result = self.llm_service.generate(prompt)
            # Try to parse JSON from response
            import re

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                return {
                    "actionability": float(parsed.get("actionability", 5.0)),
                    "specificity": float(parsed.get("specificity", 5.0)),
                    "feasibility": float(parsed.get("feasibility", 5.0)),
                    "strategic_value": float(parsed.get("strategic_value", 5.0)),
                    "overall_score": float(parsed.get("overall_score", 5.0)),
                }
            # Fallback: return default scores
            return {
                "actionability": 5.0,
                "specificity": 5.0,
                "feasibility": 5.0,
                "strategic_value": 5.0,
                "overall_score": 5.0,
            }
        except Exception:
            return {
                "actionability": 5.0,
                "specificity": 5.0,
                "feasibility": 5.0,
                "strategic_value": 5.0,
                "overall_score": 5.0,
            }

    def calculate_decision_support_quality(self, task: str, response: str) -> dict:
        """Calculate decision support quality score with sub-dimensions."""
        prompt = f"""You are an expert evaluator of business and strategic decision-support systems.

Task:
{task}

Response:
{response}

Evaluate the response from 1-10 on:
1. Analytical Depth - Does it provide deep, thoughtful analysis?
2. Risk Awareness - Does it identify and assess risks appropriately?
3. Evidence and Justification - Are claims supported with evidence?
4. Strategic Insight - Does it provide valuable strategic perspectives?
5. Decision Usefulness - Would this help a real decision-maker?

Provide scores for each category and an overall Decision Support Quality Score.

Return JSON only:
{{
"analytical_depth": float,
"risk_awareness": float,
"evidence": float,
"strategic_insight": float,
"decision_usefulness": float,
"overall_score": float
}}"""

        try:
            result = self.llm_service.generate(prompt)
            # Try to parse JSON from response
            import re

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                return {
                    "analytical_depth": float(parsed.get("analytical_depth", 5.0)),
                    "risk_awareness": float(parsed.get("risk_awareness", 5.0)),
                    "evidence": float(parsed.get("evidence", 5.0)),
                    "strategic_insight": float(parsed.get("strategic_insight", 5.0)),
                    "decision_usefulness": float(parsed.get("decision_usefulness", 5.0)),
                    "overall_score": float(parsed.get("overall_score", 5.0)),
                }
            # Fallback: return default scores
            return {
                "analytical_depth": 5.0,
                "risk_awareness": 5.0,
                "evidence": 5.0,
                "strategic_insight": 5.0,
                "decision_usefulness": 5.0,
                "overall_score": 5.0,
            }
        except Exception:
            return {
                "analytical_depth": 5.0,
                "risk_awareness": 5.0,
                "evidence": 5.0,
                "strategic_insight": 5.0,
                "decision_usefulness": 5.0,
                "overall_score": 5.0,
            }
