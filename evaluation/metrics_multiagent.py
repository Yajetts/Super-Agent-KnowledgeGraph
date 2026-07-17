"""Metrics for evaluating agent outputs."""

from __future__ import annotations

import re


class MetricsCalculator:
    """Calculate evaluation metrics for agent outputs."""

    # Decision-analysis dimensions to check for coverage
    DIMENSIONS = [
        "market analysis",
        "risks",
        "opportunities",
        "competitors",
        "regulations",
        "recommendations",
    ]

    def calculate_coverage(self, text: str) -> float:
        """Calculate coverage score (0.0 - 1.0) based on dimensions present."""
        text_lower = text.lower()
        dimensions_found = sum(
            1 for dimension in self.DIMENSIONS if dimension in text_lower
        )
        return dimensions_found / len(self.DIMENSIONS)

    def count_risks(self, text: str) -> int:
        """Count distinct risks mentioned in the text."""
        # Look for risk-related keywords and count them
        risk_patterns = [
            r"risk[s]?:",
            r"potential risk",
            r"major risk",
            r"significant risk",
            r"key risk",
            r"primary risk",
        ]
        risk_count = 0
        for pattern in risk_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            risk_count += len(matches)
        # Also count bullet points that mention risk
        risk_bullets = re.findall(r"[-*]\s.*risk", text, re.IGNORECASE)
        risk_count += len(risk_bullets)
        return max(risk_count, 0)

    def count_recommendations(self, text: str) -> int:
        """Count distinct actionable recommendations."""
        # Look for recommendation-related keywords
        rec_patterns = [
            r"recommend[s]?:",
            r"suggest[s]?:",
            r"advise[s]?:",
            r"should:",
            r"action:",
            r"step:",
        ]
        rec_count = 0
        for pattern in rec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rec_count += len(matches)
        # Also count bullet points that look like recommendations
        rec_bullets = re.findall(
            r"[-*]\s.*(recommend|suggest|advise|implement|adopt|consider)",
            text,
            re.IGNORECASE,
        )
        rec_count += len(rec_bullets)
        return max(rec_count, 0)
