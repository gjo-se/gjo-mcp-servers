"""Frequency analysis helpers for normalized skills."""

from collections import Counter
from typing import TypedDict


class SkillFrequency(TypedDict):
    """Frequency entry for one normalized skill."""

    skill: str
    count: int


def analyze_frequency(skills: list[str]) -> list[SkillFrequency]:
    """Count and sort normalized skills by frequency.

    Args:
        skills: Normalized skill labels.

    Returns:
        A list of dictionaries sorted by count descending, then by skill name.
    """
    counts = Counter(skill for skill in skills if skill)
    ordered_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return [
        SkillFrequency(skill=skill_name, count=count)
        for skill_name, count in ordered_counts
    ]

