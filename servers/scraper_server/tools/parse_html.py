"""HTML parsing helpers for freelancermap scraper fixtures and live pages."""

import re
from html import unescape

_RESULT_CARD_PATTERN = re.compile(
    r'<article[^>]*class="[^"]*result-card[^"]*"[^>]*>(.*?)</article>',
    re.DOTALL,
)
_PROJECT_LINK_PATTERN = re.compile(
    r'<a[^>]*class="[^"]*project-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.DOTALL,
)
_SUMMARY_PATTERN = re.compile(
    r'<p[^>]*class="[^"]*summary[^"]*"[^>]*>(.*?)</p>',
    re.DOTALL,
)
_SKILL_PATTERN = re.compile(
    r'<span[^>]*class="[^"]*skill-tag[^"]*"[^>]*>(.*?)</span>',
    re.DOTALL,
)
_PAGINATION_PATTERN = re.compile(
    r'<nav[^>]*class="[^"]*pagination[^"]*"[^>]*'
    r'data-current-page="(?P<current>\d+)"[^>]*'
    r'data-total-pages="(?P<total>\d+)"[^>]*>(?P<body>.*?)</nav>',
    re.DOTALL,
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def _clean_text(value: str) -> str:
    """Remove HTML tags, unescape entities and normalize whitespace."""
    without_tags = _HTML_TAG_PATTERN.sub(" ", value)
    return " ".join(unescape(without_tags).split())


def extract_skill_rows_from_html(html: str) -> list[dict[str, str]]:
    """Extract structured result rows from freelancermap HTML.

    Args:
        html: Raw HTML page content.

    Returns:
        Structured rows with title, url, skills_raw and summary.
    """
    rows: list[dict[str, str]] = []

    for raw_card in _RESULT_CARD_PATTERN.findall(html):
        project_link = _PROJECT_LINK_PATTERN.search(raw_card)
        if not project_link:
            continue

        summary = _SUMMARY_PATTERN.search(raw_card)
        skills = [_clean_text(skill) for skill in _SKILL_PATTERN.findall(raw_card)]

        rows.append(
            {
                "title": _clean_text(project_link.group(2)),
                "url": project_link.group(1).strip(),
                "skills_raw": ", ".join(skill for skill in skills if skill),
                "summary": _clean_text(summary.group(1)) if summary else "",
            }
        )

    return rows


def extract_pagination_info(html: str) -> dict[str, int | bool]:
    """Extract simple pagination metadata from HTML.

    Args:
        html: Raw HTML page content.

    Returns:
        Dictionary with current_page, total_pages and has_next.
    """
    match = _PAGINATION_PATTERN.search(html)
    if not match:
        return {"current_page": 1, "total_pages": 1, "has_next": False}

    current_page = int(match.group("current"))
    total_pages = int(match.group("total"))
    body = match.group("body")
    has_next = 'class="next"' in body or "class='next'" in body

    return {
        "current_page": current_page,
        "total_pages": total_pages,
        "has_next": has_next,
    }
