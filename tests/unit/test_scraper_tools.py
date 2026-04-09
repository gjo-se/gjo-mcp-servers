"""Unit tests for scraper_server tools (parse_html + scrape_freelancermap)."""

from pathlib import Path

import pytest

import servers.scraper_server.tools.scrape_freelancermap as scraper_module
from servers.scraper_server.tools.parse_html import extract_skill_rows_from_html
from servers.scraper_server.tools.scrape_freelancermap import (
    LayoutChangedError,
    scrape_freelancermap,
)

_FIXTURES = Path(__file__).parent.parent / "fixtures"
_SAMPLE_HTML = _FIXTURES / "html" / "freelancermap_sample.html"
_EMPTY_HTML = _FIXTURES / "freelancermap" / "search_results_empty.html"


def _read_html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_extract_skill_rows_returns_results_from_fixture_html() -> None:
    """extract_skill_rows_from_html should return at least one row from fixture HTML."""
    rows = extract_skill_rows_from_html(_read_html(_SAMPLE_HTML))

    assert len(rows) >= 1


def test_extract_skill_rows_returns_dicts_with_required_keys() -> None:
    """Every result row must contain title, url, skills_raw and summary."""
    rows = extract_skill_rows_from_html(_read_html(_SAMPLE_HTML))

    for row in rows:
        assert "title" in row
        assert "url" in row
        assert "skills_raw" in row
        assert "summary" in row


def test_scrape_freelancermap_raises_layout_changed_error_on_empty_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty or structurally invalid HTML must raise LayoutChangedError."""
    monkeypatch.setattr(
        scraper_module,
        "_fetch_search_results_html",
        lambda query: (_read_html(_EMPTY_HTML), f"https://example.test/?q={query}"),
    )

    with pytest.raises(LayoutChangedError):
        scrape_freelancermap("Python Backend")


def test_layout_changed_error_exposes_url_selector_and_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LayoutChangedError must carry url, selector and timestamp attributes."""
    monkeypatch.setattr(
        scraper_module,
        "_fetch_search_results_html",
        lambda query: (_read_html(_EMPTY_HTML), f"https://example.test/?q={query}"),
    )

    with pytest.raises(LayoutChangedError) as exc_info:
        scrape_freelancermap("Python Backend")

    error = exc_info.value
    assert error.url
    assert error.selector
    assert error.timestamp

