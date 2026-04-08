"""Unit tests for the freelancermap scraper tool."""

from pathlib import Path

import pytest

import servers.scraper_server.tools.scrape_freelancermap as scraper_module
from servers.scraper_server.tools.parse_html import extract_pagination_info
from servers.scraper_server.tools.scrape_freelancermap import (
    LayoutChangedError,
    scrape_freelancermap,
)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "freelancermap"


def _read_fixture(name: str) -> str:
    """Read a fixture file from the freelancermap fixture directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_scrape_freelancermap_returns_structured_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The scraper tool should return structured project rows from fixture HTML."""
    html = _read_fixture("search_results_page_1.html")

    monkeypatch.setattr(
        scraper_module,
        "_fetch_search_results_html",
        lambda query: (html, f"https://example.test/?q={query}"),
    )

    results = scrape_freelancermap("Python Backend")

    assert len(results) == 2
    assert results[0]["title"] == "Python Backend API Projekt"
    assert results[0]["url"] == "https://www.freelancermap.de/project/python-backend-api"
    assert results[0]["skills_raw"] == "Python, FastAPI, PostgreSQL"
    assert "FastAPI-Schnittstelle" in results[0]["summary"]


def test_scrape_freelancermap_raises_layout_changed_error_on_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty or structurally wrong HTML should raise LayoutChangedError."""
    html = _read_fixture("search_results_empty.html")

    monkeypatch.setattr(
        scraper_module,
        "_fetch_search_results_html",
        lambda query: (html, f"https://example.test/?q={query}"),
    )

    with pytest.raises(LayoutChangedError) as exc_info:
        scrape_freelancermap("Python Backend")

    error = exc_info.value
    assert error.url == "https://example.test/?q=Python Backend"
    assert error.selector == "article.result-card"
    assert error.timestamp


def test_extract_pagination_info_returns_expected_metadata() -> None:
    """Pagination helper should parse current page, total pages and next flag."""
    html = _read_fixture("search_results_page_1.html")

    pagination = extract_pagination_info(html)

    assert pagination == {
        "current_page": 1,
        "total_pages": 2,
        "has_next": True,
    }


