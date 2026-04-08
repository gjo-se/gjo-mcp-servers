"""Async SQLAlchemy engine and session helpers."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.config import settings


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Create an async SQLAlchemy engine.

    Args:
        database_url: Optional explicit database URL.

    Returns:
        Configured async engine.
    """
    return create_async_engine(database_url or settings.database_url, future=True)


engine: AsyncEngine = create_engine()
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_session_factory(
    database_url: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create a session factory for the given URL or the default settings URL."""
    if database_url is None:
        return AsyncSessionFactory

    custom_engine = create_engine(database_url)
    return async_sessionmaker(
        bind=custom_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


