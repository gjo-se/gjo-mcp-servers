"""Query persisted top skills from the storage database."""

from typing import TypedDict

from sqlalchemy import Select, desc, select

import shared.db.session as db_session
from shared.models.skill import Skill, SkillFrequency


class SkillCount(TypedDict):
    """Aggregated top-skill result payload."""

    skill: str
    count: int


async def query_top_skills(limit: int = 20) -> list[SkillCount]:
    """Return top persisted skills ordered by count.

    Args:
        limit: Maximum number of rows to return.

    Returns:
        Aggregated skill/count pairs.
    """
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    stmt: Select[tuple[str, int]] = (
        select(Skill.name, SkillFrequency.count)
        .join(SkillFrequency, Skill.id == SkillFrequency.skill_id)
        .order_by(desc(SkillFrequency.count), Skill.name.asc())
        .limit(limit)
    )

    session_factory = db_session.get_session_factory()
    async with session_factory() as session:
        result = await session.execute(stmt)
        rows = result.all()

    return [SkillCount(skill=skill_name, count=count) for skill_name, count in rows]

