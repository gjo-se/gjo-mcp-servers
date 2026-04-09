"""Persist layout snapshots for scraper recovery workflows."""

from datetime import UTC, datetime

import shared.db.session as db_session
from shared.models.skill import LayoutSnapshot


def _parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO timestamp input for layout snapshots."""
    cleaned_timestamp = timestamp.strip()
    if not cleaned_timestamp:
        raise ValueError("timestamp must not be empty")

    normalized_timestamp = cleaned_timestamp.replace("Z", "+00:00")
    parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    if parsed_timestamp.tzinfo is None:
        return parsed_timestamp.replace(tzinfo=UTC)
    return parsed_timestamp


async def save_layout_snapshot(
    url: str,
    tree: str,
    timestamp: str,
    selector: str = "unknown",
) -> bool:
    """Persist a layout snapshot for later recovery analysis.

    Args:
        url: Source URL of the failed scrape.
        tree: Snapshot content or serialized accessibility tree.
        timestamp: ISO-formatted capture timestamp.
        selector: Selector or parser context that failed.

    Returns:
        True when the snapshot was written successfully.
    """
    normalized_url = url.strip()
    normalized_tree = tree.strip()
    normalized_selector = selector.strip() or "unknown"

    if not normalized_url:
        raise ValueError("url must not be empty")
    if not normalized_tree:
        raise ValueError("tree must not be empty")

    captured_at = _parse_timestamp(timestamp)

    session_factory = db_session.get_session_factory()
    async with session_factory() as session:
        session.add(
            LayoutSnapshot(
                url=normalized_url,
                selector=normalized_selector,
                snapshot_content=normalized_tree,
                captured_at=captured_at,
            )
        )
        await session.commit()

    return True
