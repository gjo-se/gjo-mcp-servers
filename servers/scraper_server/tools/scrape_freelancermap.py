"""Playwright-powered scraper tool for freelancermap results."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypedDict
from urllib.parse import quote_plus

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from servers.scraper_server.tools.parse_html import extract_skill_rows_from_html

FREELANCERMAP_BASE_URL = "https://www.freelancermap.de"
RESULT_SELECTOR = "article.result-card"


class ScrapedProject(TypedDict):
    """Structured scraper output for one result card."""

    title: str
    url: str
    skills_raw: str
    summary: str


@dataclass(slots=True)
class LayoutChangedError(RuntimeError):
    """Raised when the expected page layout can no longer be parsed."""

    url: str
    selector: str
    detail: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        RuntimeError.__init__(
            self,
            f"Layout changed for {self.url} (selector={self.selector}): {self.detail}",
        )


def _build_search_url(query: str) -> str:
    """Create a freelancermap search URL for the given query."""
    return f"{FREELANCERMAP_BASE_URL}/?query={quote_plus(query)}"


def _fetch_search_results_html(query: str) -> tuple[str, str]:
    """Fetch rendered HTML for a search query using Playwright."""
    search_url = _build_search_url(query)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(search_url, wait_until="networkidle")
                return page.content(), page.url
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise LayoutChangedError(
            url=search_url,
            selector=RESULT_SELECTOR,
            detail=f"Playwright fetch failed: {exc}",
        ) from exc


def scrape_freelancermap(query: str) -> list[ScrapedProject]:
    """Scrape structured freelancermap results for a search query.

    Args:
        query: Search phrase, e.g. ``Python Backend``.

    Returns:
        A structured list of freelancermap result rows.

    Raises:
        LayoutChangedError: If the page structure no longer matches expectations.
    """
    html, source_url = _fetch_search_results_html(query)
    rows = extract_skill_rows_from_html(html)

    if not rows:
        raise LayoutChangedError(
            url=source_url,
            selector=RESULT_SELECTOR,
            detail="No result cards could be extracted from the HTML response.",
        )

    return [ScrapedProject(**row) for row in rows]
