"""Persist skill frequency entries in the storage database."""

from sqlalchemy import select

import shared.db.session as db_session
from shared.models.skill import Skill, SkillFrequency


def _validate_skill_frequency_input(
    skill: str,
    count: int,
    source_query: str,
) -> tuple[str, int, str]:
    """Validate and normalize input for skill frequency persistence."""
    normalized_skill = " ".join(skill.strip().lower().split())
    normalized_query = " ".join(source_query.strip().split()) or "default"

    if not normalized_skill:
        raise ValueError("skill must not be empty")
    if count < 0:
        raise ValueError("count must be greater than or equal to 0")

    return normalized_skill, count, normalized_query


async def save_skill_frequency(
    skill: str,
    count: int,
    source_query: str = "default",
) -> bool:
    """Create or update a persisted skill frequency entry.

    Args:
        skill: Canonical or raw skill label.
        count: Frequency count to persist.
        source_query: Query bucket for the persisted count.

    Returns:
        True when the frequency was written successfully.
    """
    (
        normalized_skill,
        normalized_count,
        normalized_query,
    ) = _validate_skill_frequency_input(skill, count, source_query)

    session_factory = db_session.get_session_factory()
    async with session_factory() as session:
        skill_result = await session.execute(
            select(Skill).where(Skill.name == normalized_skill)
        )
        skill_model = skill_result.scalar_one_or_none()

        if skill_model is None:
            skill_model = Skill(name=normalized_skill)
            session.add(skill_model)
            await session.flush()

        frequency_result = await session.execute(
            select(SkillFrequency).where(
                SkillFrequency.skill_id == skill_model.id,
                SkillFrequency.source_query == normalized_query,
            )
        )
        frequency_model = frequency_result.scalar_one_or_none()

        if frequency_model is None:
            frequency_model = SkillFrequency(
                skill_id=skill_model.id,
                source_query=normalized_query,
                count=normalized_count,
            )
            session.add(frequency_model)
        else:
            frequency_model.count = normalized_count

        await session.commit()

    return True
