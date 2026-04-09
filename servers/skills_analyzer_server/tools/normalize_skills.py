"""Normalization helpers for raw skill labels."""

_SKILL_SYNONYMS: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "postgres": "postgresql",
    "pg": "postgresql",
    "ts": "typescript",
    "js": "javascript",
}


def _normalize_single_skill(raw_skill: str) -> str:
    """Normalize one raw skill label.

    Args:
        raw_skill: Unnormalized skill string.

    Returns:
        Normalized, lower-cased skill label or an empty string.
    """
    normalized = " ".join(raw_skill.strip().lower().split())
    if not normalized:
        return ""

    return _SKILL_SYNONYMS.get(normalized, normalized)


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """Normalize a list of raw skill labels.

    Args:
        raw_skills: Raw skill names from scraping or other inputs.

    Returns:
        Deterministically normalized skill labels without empty values.
    """
    return [
        normalized_skill
        for normalized_skill in (_normalize_single_skill(skill) for skill in raw_skills)
        if normalized_skill
    ]
