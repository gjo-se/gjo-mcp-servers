"""Unit tests for skills_analyzer_server tools using shared conftest fixtures."""

from servers.skills_analyzer_server.tools.analyze_frequency import analyze_frequency
from servers.skills_analyzer_server.tools.normalize_skills import normalize_skills


def test_normalize_skills_output_matches_fixture(
    raw_skills: list[str],
    normalized_skills: list[str],
) -> None:
    """normalize_skills must produce the expected deterministic output from the
    fixture."""
    assert normalize_skills(raw_skills) == normalized_skills


def test_analyze_frequency_counts_and_sorts_by_count_then_alpha(
    normalized_skills: list[str],
) -> None:
    """analyze_frequency must sort descending by count and then alphabetically."""
    result = analyze_frequency(normalized_skills)

    assert result == [
        {"skill": "python", "count": 3},
        {"skill": "postgresql", "count": 2},
        {"skill": "fastapi", "count": 1},
        {"skill": "typescript", "count": 1},
    ]


def test_normalize_skills_handles_empty_input() -> None:
    """normalize_skills must return an empty list for empty input."""
    assert normalize_skills([]) == []


def test_analyze_frequency_handles_empty_input() -> None:
    """analyze_frequency must return an empty list for empty input."""
    assert analyze_frequency([]) == []
