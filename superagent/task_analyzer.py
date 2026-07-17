"""Rule-based task analysis for the SuperAgent workflow."""

from __future__ import annotations

import re

from loguru import logger

from superagent.schemas import TaskAnalysis


class TaskAnalyzer:
    """Analyze raw user tasks into a structured representation."""

    _task_keywords: dict[str, tuple[str, ...]] = {
        "risk_assessment": (
            "risk",
            "risks",
            "cybersecurity",
            "threat",
            "threats",
            "mitigation",
            "vulnerability",
            "vulnerabilities",
            "assess",
        ),
        "technology_research": (
            "technology",
            "technologies",
            "quantum",
            "ai",
            "machine learning",
            "startup",
            "startups",
            "software",
            "computing",
            "technical",
        ),
        "competitive_analysis": (
            "competitor",
            "competitors",
            "competitive",
            "compare",
            "competition",
            "benchmark",
        ),
        "market_research": (
            "market research",
            "customers",
            "demand",
            "segments",
            "segmentation",
        ),
        "business_analysis": (
            "market",
            "expand",
            "expansion",
            "business",
            "industry",
            "growth",
            "entry",
        ),
    }

    _subtask_map: dict[str, list[str]] = {
        "business_analysis": [
            "market_research",
            "competitor_analysis",
            "risk_assessment",
            "strategy_recommendation",
        ],
        "market_research": [
            "market_scoping",
            "customer_analysis",
            "demand_assessment",
        ],
        "risk_assessment": [
            "risk_identification",
            "impact_analysis",
            "mitigation_strategy",
        ],
        "technology_research": [
            "technology_review",
            "trend_analysis",
            "future_opportunities",
        ],
        "competitive_analysis": [
            "competitor_review",
            "market_positioning",
            "strategy_recommendation",
        ],
        "general_research": [
            "information_gathering",
            "source_review",
            "summary_synthesis",
        ],
        "unknown": [
            "task_clarification",
            "information_gathering",
        ],
    }

    _skill_map: dict[str, list[str]] = {
        "business_analysis": ["research", "risk_analysis", "strategy"],
        "market_research": ["research"],
        "risk_assessment": ["research", "risk_analysis"],
        "technology_research": ["research"],
        "competitive_analysis": ["research", "strategy"],
        "general_research": ["research"],
        "unknown": ["research"],
    }

    def classify_task(self, query: str) -> str:
        """Classify a query using deterministic keyword rules."""
        normalized_query = query.lower()
        for task_type, keywords in self._task_keywords.items():
            if any(keyword in normalized_query for keyword in keywords):
                return task_type
        return "general_research" if normalized_query.strip() else "unknown"

    def extract_subtasks(self, query: str) -> list[str]:
        """Generate subtasks for the classified query."""
        task_type = self.classify_task(query)
        return list(self._subtask_map.get(task_type, self._subtask_map["unknown"]))

    def extract_required_skills(self, query: str) -> list[str]:
        """Map the classified query to the skills it requires."""
        task_type = self.classify_task(query)
        return list(self._skill_map.get(task_type, self._skill_map["unknown"]))

    def _estimate_complexity(self, query: str) -> str:
        """Estimate complexity using simple, deterministic heuristics."""
        normalized_query = query.strip()
        if not normalized_query:
            return "low"

        token_count = len(re.findall(r"\b\w+\b", normalized_query))
        multi_part_markers = sum(
            normalized_query.lower().count(marker)
            for marker in (",", ";", " and ", " or ", " vs ", " compare ")
        )

        if token_count <= 7 and multi_part_markers == 0:
            return "low"
        if token_count >= 18 or multi_part_markers >= 2:
            return "high"
        return "medium"

    def analyze(self, query: str) -> TaskAnalysis:
        """Return a structured analysis for the supplied query."""
        task_type = self.classify_task(query)
        subtasks = self.extract_subtasks(query)
        required_skills = self.extract_required_skills(query)
        complexity = self._estimate_complexity(query)

        logger.info("Task type identified: {}", task_type)
        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            subtasks=subtasks,
            required_skills=required_skills,
        )
