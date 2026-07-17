"""Parse raw LLM output into structured workflow objects."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from quality.output_validator import OutputValidator
from superagent.context_models import Finding, Recommendation, Risk


_JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_NUMBERED_BULLET_PATTERN = re.compile(r"^\s*(?:[-*]|\d+[.)])\s*")


def _safe_json_loads(raw_output: str) -> object | None:
    candidate = raw_output.strip()
    if not candidate:
        return None

    match = _JSON_BLOCK_PATTERN.search(candidate)
    if match is not None:
        candidate = match.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _coerce_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() or default
    return str(value).strip() or default


def _coerce_confidence(value: object, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(confidence, 1.0))


def _coerce_priority(value: object, default: str) -> str:
    priority = _coerce_text(value, default).lower()
    return priority or default


def _coerce_severity(value: object, default: str) -> str:
    severity = _coerce_text(value, default).lower()
    return severity or default


def _normalize_lines(raw_output: str) -> list[str]:
    normalized_lines: list[str] = []
    for raw_line in raw_output.splitlines():
        line = _NUMBERED_BULLET_PATTERN.sub("", raw_line).strip()
        if line:
            normalized_lines.append(line)
    return normalized_lines


def _iter_items(parsed: object) -> Iterable[object]:
    if isinstance(parsed, dict):
        for key in ("findings", "risks", "recommendations", "items", "data"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    return []


def _extract_value_pairs(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for segment in re.split(r"\s*[|;]\s*", text):
        if ":" in segment:
            key, value = segment.split(":", 1)
            pairs[key.strip().lower()] = value.strip()
    return pairs


def _parse_findings_from_text(raw_output: str, source_agent: str, default_category: str, default_confidence: float) -> list[Finding]:
    findings: list[Finding] = []
    for line in _normalize_lines(raw_output):
        pairs = _extract_value_pairs(line)
        category = pairs.get("category", default_category)
        confidence = _coerce_confidence(pairs.get("confidence"), default_confidence)

        if pairs.get("content"):
            content = pairs["content"]
        elif ":" in line:
            first_key, remainder = line.split(":", 1)
            if first_key.strip().lower() in {"category", "confidence", "source_agent", "source"}:
                content = re.sub(r"\s*[|;]\s*confidence\s*:\s*.*$", "", remainder, flags=re.IGNORECASE).strip()
            else:
                content = line
        else:
            content = line

        content = content.strip()
        if content:
            findings.append(
                Finding(
                    source_agent=source_agent,
                    category=category,
                    content=content,
                    confidence=confidence,
                )
            )

    if findings:
        return findings

    stripped = raw_output.strip()
    if stripped:
        return [Finding(source_agent=source_agent, category=default_category, content=stripped, confidence=default_confidence)]
    return []


def _parse_risks_from_text(raw_output: str, source_agent: str, default_severity: str) -> list[Risk]:
    risks: list[Risk] = []
    for line in _normalize_lines(raw_output):
        pairs = _extract_value_pairs(line)
        severity = _coerce_severity(pairs.get("severity"), default_severity)
        description = pairs.get("description") or pairs.get("content") or line

        if description:
            risks.append(Risk(source_agent=source_agent, description=description, severity=severity))

    if risks:
        return risks

    stripped = raw_output.strip()
    if stripped:
        return [Risk(source_agent=source_agent, description=stripped, severity=default_severity)]
    return []


def _parse_recommendations_from_text(raw_output: str, source_agent: str, default_priority: str) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for line in _normalize_lines(raw_output):
        pairs = _extract_value_pairs(line)
        priority = _coerce_priority(pairs.get("priority"), default_priority)
        content = pairs.get("content") or pairs.get("recommendation") or line

        if content:
            recommendations.append(Recommendation(source_agent=source_agent, content=content, priority=priority))

    if recommendations:
        return recommendations

    stripped = raw_output.strip()
    if stripped:
        return [Recommendation(source_agent=source_agent, content=stripped, priority=default_priority)]
    return []


def parse_findings(raw_output: str, source_agent: str, default_category: str = "general", default_confidence: float = 0.5) -> list[Finding]:
    """Convert raw LLM output into Finding objects."""

    parsed = _safe_json_loads(raw_output)
    if parsed is not None:
        findings: list[Finding] = []
        for item in _iter_items(parsed):
            if isinstance(item, str):
                findings.extend(_parse_findings_from_text(item, source_agent, default_category, default_confidence))
                continue
            if not isinstance(item, dict):
                continue

            content = _coerce_text(item.get("content") or item.get("finding") or item.get("description") or item.get("text"), "")

            # Validate and clean content
            cleaned_content = OutputValidator.validate_and_clean_finding(content)
            if not cleaned_content:
                continue

            findings.append(
                Finding(
                    source_agent=_coerce_text(item.get("source_agent"), source_agent) or source_agent,
                    category=_coerce_text(item.get("category"), default_category) or default_category,
                    content=cleaned_content,
                    confidence=_coerce_confidence(item.get("confidence"), default_confidence),
                )
            )

        return [finding for finding in findings if finding.content]

    # For text parsing, validate each line
    text_findings = _parse_findings_from_text(raw_output, source_agent, default_category, default_confidence)
    validated_findings = []
    for finding in text_findings:
        cleaned_content = OutputValidator.validate_and_clean_finding(finding.content)
        if cleaned_content:
            validated_findings.append(
                Finding(
                    source_agent=finding.source_agent,
                    category=finding.category,
                    content=cleaned_content,
                    confidence=finding.confidence,
                )
            )
    return validated_findings


def parse_risks(raw_output: str, source_agent: str, default_severity: str = "medium") -> list[Risk]:
    """Convert raw LLM output into Risk objects."""

    parsed = _safe_json_loads(raw_output)
    if parsed is not None:
        risks: list[Risk] = []
        for item in _iter_items(parsed):
            if isinstance(item, str):
                risks.extend(_parse_risks_from_text(item, source_agent, default_severity))
                continue
            if not isinstance(item, dict):
                continue

            description = _coerce_text(item.get("description") or item.get("content") or item.get("text"), "")

            # Validate and clean description
            cleaned_description = OutputValidator.validate_and_clean_risk(description)
            if not cleaned_description:
                continue

            risks.append(
                Risk(
                    source_agent=_coerce_text(item.get("source_agent"), source_agent) or source_agent,
                    description=cleaned_description,
                    severity=_coerce_severity(item.get("severity"), default_severity),
                )
            )

        return [risk for risk in risks if risk.description]

    # For text parsing, validate each line
    text_risks = _parse_risks_from_text(raw_output, source_agent, default_severity)
    validated_risks = []
    for risk in text_risks:
        cleaned_description = OutputValidator.validate_and_clean_risk(risk.description)
        if cleaned_description:
            validated_risks.append(
                Risk(
                    source_agent=risk.source_agent,
                    description=cleaned_description,
                    severity=risk.severity,
                )
            )
    return validated_risks


def parse_recommendations(raw_output: str, source_agent: str, default_priority: str = "medium") -> list[Recommendation]:
    """Convert raw LLM output into Recommendation objects."""

    parsed = _safe_json_loads(raw_output)
    if parsed is not None:
        recommendations: list[Recommendation] = []
        for item in _iter_items(parsed):
            if isinstance(item, str):
                recommendations.extend(_parse_recommendations_from_text(item, source_agent, default_priority))
                continue
            if not isinstance(item, dict):
                continue

            content = _coerce_text(item.get("content") or item.get("recommendation") or item.get("text"), "")

            # Validate and clean content
            cleaned_content = OutputValidator.validate_and_clean_recommendation(content)
            if not cleaned_content:
                continue

            recommendations.append(
                Recommendation(
                    source_agent=_coerce_text(item.get("source_agent"), source_agent) or source_agent,
                    content=cleaned_content,
                    priority=_coerce_priority(item.get("priority"), default_priority),
                )
            )

        return [recommendation for recommendation in recommendations if recommendation.content]

    # For text parsing, validate each line
    text_recommendations = _parse_recommendations_from_text(raw_output, source_agent, default_priority)
    validated_recommendations = []
    for recommendation in text_recommendations:
        cleaned_content = OutputValidator.validate_and_clean_recommendation(recommendation.content)
        if cleaned_content:
            validated_recommendations.append(
                Recommendation(
                    source_agent=recommendation.source_agent,
                    content=cleaned_content,
                    priority=recommendation.priority,
                )
            )
    return validated_recommendations