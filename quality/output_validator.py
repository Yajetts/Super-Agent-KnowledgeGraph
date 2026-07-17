"""Output validation for agent-generated content."""

from __future__ import annotations

import re
from typing import Any

from loguru import logger


class OutputValidator:
    """Validate and sanitize agent-generated findings, risks, and recommendations."""

    # Patterns to reject
    INVALID_PATTERNS = [
        r"^##",  # Markdown headers
        r"^#",  # Markdown headers
        r"^References",  # References section
        r"^Bibliography",  # Bibliography section
        r"^Source",  # Source section
        r"^Citation",  # Citation section
        r"^http",  # URLs
        r"^www",  # URLs
        r"^DOI",  # DOI references
        r"^--",  # Separators
        r"^---",  # Separators
    ]

    # Invalid content patterns (standalone)
    INVALID_CONTENT_PATTERNS = [
        r"^UL \d+",  # Standards like UL 2580
        r"^IEC \d+",  # Standards like IEC 62660
        r"^ISO \d+",  # Standards like ISO 26262
        r"^EU.*Directive",  # EU directives
        r"^Nature Energy",  # Journal names
        r"^Wang et al\.",  # Citations
        r"et al\., \d{4}",  # Citations
        r"For further consultation",  # Boilerplate
        r"See also",  # Boilerplate
        r"\(\d{4}\)",  # Citations with year in parentheses
        r"Journal of",  # Journal names
        r"Proceedings of",  # Conference proceedings
        r"DOI:",  # DOI references
        r"doi:",  # DOI references
        r"pp\. \d+",  # Page numbers
        r"vol\. \d+",  # Volume numbers
        r"no\. \d+",  # Issue numbers
        r"pp\.",  # Page references
        r"vol\.",  # Volume references
        r"no\.",  # Issue references
        r"Available at:",  # Availability statements
        r"Retrieved from:",  # Retrieval statements
        r"Accessed:",  # Access statements
        r":$",  # Ends with colon (incomplete)
        r":\s*$",  # Ends with colon with whitespace (incomplete)
    ]

    # Header/incomplete patterns
    HEADER_PATTERNS = [
        r"^Drivers of Demand",  # Incomplete header
        r"^Key Resources in Demand",  # Incomplete header
        r"^Market Drivers",  # Incomplete header
        r"^Demand Drivers",  # Incomplete header
        r"^Supply Chain",  # Incomplete header
        r"^Resource Types",  # Incomplete header
        r"^Extraction Methods",  # Incomplete header
        r"^Technical Challenges",  # Incomplete header
        r"^Economic Factors",  # Incomplete header
        r"^Regulatory Environment",  # Incomplete header
        r"^Competitive Landscape",  # Incomplete header
        r"^Investment Requirements",  # Incomplete header
        r"^Risk Factors",  # Incomplete header
        r"^Opportunities",  # Incomplete header
        r"^Challenges",  # Incomplete header
        r"^Barriers",  # Incomplete header
        r"^Considerations",  # Incomplete header
        r"^Analysis",  # Incomplete header
        r"^Overview",  # Incomplete header
        r"^Summary",  # Incomplete header
        r"^Introduction",  # Incomplete header
        r"^Background",  # Incomplete header
        r"^Methodology",  # Incomplete header
        r"^Results",  # Incomplete header
        r"^Discussion",  # Incomplete header
        r"^Conclusion",  # Incomplete header
        r"^Recommendations",  # Incomplete header
        r"^Findings",  # Incomplete header
        r"^Risks",  # Incomplete header
    ]

    # Citation patterns (more aggressive)
    CITATION_PATTERNS = [
        r"^[A-Z][a-z]+, [A-Z]\. \(\d{4}\)",  # Author, Initial. (Year)
        r"^[A-Z][a-z]+ & [A-Z][a-z]+, \d{4}",  # Author & Author, Year
        r"^[A-Z][a-z]+ et al\., \d{4}",  # Author et al., Year
        r"\(\d{4}[a-z]?\)",  # Year in parentheses with optional letter
        r"doi\.org/",  # DOI URLs
        r"https://doi\.org/",  # DOI URLs
    ]

    @classmethod
    def validate_finding(cls, content: str) -> tuple[bool, str | None]:
        """Validate a finding.

        A Finding must represent a factual observation, insight, conclusion, trend,
        discovery, or analysis result.

        Args:
            content: The finding content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content or not content.strip():
            return False, "Empty finding"

        content = content.strip()

        # Check for invalid patterns
        for pattern in cls.INVALID_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid pattern: {pattern}"

        # Check for invalid content patterns
        for pattern in cls.INVALID_CONTENT_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid content pattern: {pattern}"

        # Check for citation patterns (more aggressive)
        for pattern in cls.CITATION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Matches citation pattern: {pattern}"

        # Check for header/incomplete patterns
        for pattern in cls.HEADER_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches header/incomplete pattern: {pattern}"

        # Check for URLs
        if "http://" in content or "https://" in content:
            return False, "Contains URL"

        # Check if it's just a citation/reference
        if len(content) < 20:
            return False, "Too short to be a valid finding"

        # Check if it's mostly citation-like
        if re.match(r"^[A-Z][a-z]+ et al\., \d{4}", content):
            return False, "Appears to be a citation"

        return True, None

    @classmethod
    def validate_risk(cls, content: str) -> tuple[bool, str | None]:
        """Validate a risk.

        A Risk must contain:
        1. A threat
        2. A potential negative outcome
        3. A consequence or impact

        Args:
            content: The risk content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content or not content.strip():
            return False, "Empty risk"

        content = content.strip()

        # Check for invalid patterns
        for pattern in cls.INVALID_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid pattern: {pattern}"

        # Check for invalid content patterns
        for pattern in cls.INVALID_CONTENT_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid content pattern: {pattern}"

        # Check for citation patterns (more aggressive)
        for pattern in cls.CITATION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Matches citation pattern: {pattern}"

        # Check for header/incomplete patterns
        for pattern in cls.HEADER_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches header/incomplete pattern: {pattern}"

        # Check for URLs
        if "http://" in content or "https://" in content:
            return False, "Contains URL"

        # Check if it's just a standard name
        if re.match(r"^(UL|IEC|ISO|EU) \d+", content):
            return False, "Appears to be a standard name"

        # Check for risk-related keywords
        risk_keywords = [
            "risk",
            "threat",
            "may",
            "could",
            "potential",
            "vulnerability",
            "failure",
            "danger",
            "hazard",
            "consequence",
            "impact",
        ]

        has_risk_keyword = any(keyword in content.lower() for keyword in risk_keywords)

        if not has_risk_keyword:
            return False, "Missing risk-related keywords"

        return True, None

    @classmethod
    def validate_recommendation(cls, content: str) -> tuple[bool, str | None]:
        """Validate a recommendation.

        A Recommendation must contain an actionable mitigation, strategy,
        decision, or implementation step.

        Args:
            content: The recommendation content to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content or not content.strip():
            return False, "Empty recommendation"

        content = content.strip()

        # Check for invalid patterns
        for pattern in cls.INVALID_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid pattern: {pattern}"

        # Check for invalid content patterns
        for pattern in cls.INVALID_CONTENT_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches invalid content pattern: {pattern}"

        # Check for citation patterns (more aggressive)
        for pattern in cls.CITATION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Matches citation pattern: {pattern}"

        # Check for header/incomplete patterns
        for pattern in cls.HEADER_PATTERNS:
            if re.match(pattern, content, re.IGNORECASE):
                return False, f"Matches header/incomplete pattern: {pattern}"

        # Check for URLs
        if "http://" in content or "https://" in content:
            return False, "Contains URL"

        # Check if it's just a standard name
        if re.match(r"^(UL|IEC|ISO|EU) \d+", content):
            return False, "Appears to be a standard name"

        # Check for action-related keywords
        action_keywords = [
            "implement",
            "conduct",
            "establish",
            "develop",
            "create",
            "deploy",
            "use",
            "adopt",
            "ensure",
            "monitor",
            "assess",
            "review",
            "should",
            "must",
            "recommend",
            "consider",
        ]

        has_action_keyword = any(keyword in content.lower() for keyword in action_keywords)

        if not has_action_keyword:
            return False, "Missing action-related keywords"

        return True, None

    @classmethod
    def clean_output(cls, content: str) -> str:
        """Clean output by removing markdown formatting and separators.

        Args:
            content: The content to clean.

        Returns:
            Cleaned content.
        """
        if not content:
            return ""

        content = content.strip()

        # Remove markdown headers
        content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)

        # Remove separators
        content = re.sub(r"^---+$", "", content, flags=re.MULTILINE)
        content = re.sub(r"^--+$", "", content, flags=re.MULTILINE)

        # Remove reference sections
        lines = content.split("\n")
        cleaned_lines = []
        skip_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip reference sections
            if re.match(r"^(References|Bibliography|Source|Citation)", line, re.IGNORECASE):
                skip_section = True
                continue

            if skip_section:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @classmethod
    def validate_and_clean_finding(cls, content: str) -> str | None:
        """Validate and clean a finding. Returns None if invalid.

        Args:
            content: The finding content.

        Returns:
            Cleaned finding if valid, None otherwise.
        """
        is_valid, error = cls.validate_finding(content)
        if not is_valid:
            logger.debug("Finding validation failed: {}", error)
            return None

        return cls.clean_output(content)

    @classmethod
    def validate_and_clean_risk(cls, content: str) -> str | None:
        """Validate and clean a risk. Returns None if invalid.

        Args:
            content: The risk content.

        Returns:
            Cleaned risk if valid, None otherwise.
        """
        is_valid, error = cls.validate_risk(content)
        if not is_valid:
            logger.debug("Risk validation failed: {}", error)
            return None

        return cls.clean_output(content)

    @classmethod
    def validate_and_clean_recommendation(cls, content: str) -> str | None:
        """Validate and clean a recommendation. Returns None if invalid.

        Args:
            content: The recommendation content.

        Returns:
            Cleaned recommendation if valid, None otherwise.
        """
        is_valid, error = cls.validate_recommendation(content)
        if not is_valid:
            logger.debug("Recommendation validation failed: {}", error)
            return None

        return cls.clean_output(content)
