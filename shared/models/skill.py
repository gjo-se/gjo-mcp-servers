"""SQLAlchemy models for skills, frequencies and layout snapshots."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.base import Base


class Skill(Base):
    """Canonical skill entry."""

    __tablename__ = "skill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    frequencies: Mapped[list["SkillFrequency"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )


class SkillFrequency(Base):
    """Persisted skill frequency for one canonical skill."""

    __tablename__ = "skill_frequency"
    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "source_query",
            name="uq_skill_frequency_skill_query",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skill.id", ondelete="CASCADE"))
    source_query: Mapped[str] = mapped_column(String(255), default="default")
    count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    skill: Mapped[Skill] = relationship(back_populates="frequencies")


class LayoutSnapshot(Base):
    """Snapshot of a page layout for scraper recovery workflows."""

    __tablename__ = "layout_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), index=True)
    selector: Mapped[str] = mapped_column(String(255))
    snapshot_content: Mapped[str] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
