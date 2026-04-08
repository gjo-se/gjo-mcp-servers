"""Unit tests for storage models, migrations and health endpoint."""

import tempfile
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect
from starlette.testclient import TestClient

from alembic import command
from servers.storage_server.server import app
from shared.db.base import Base
from shared.models.skill import LayoutSnapshot, Skill, SkillFrequency


def test_storage_models_are_registered_in_metadata() -> None:
    """The shared metadata should contain all storage tables."""
    table_names = set(Base.metadata.tables)

    assert table_names >= {"skill", "skill_frequency", "layout_snapshot"}
    assert Skill.__tablename__ == "skill"
    assert SkillFrequency.__tablename__ == "skill_frequency"
    assert LayoutSnapshot.__tablename__ == "layout_snapshot"


def test_initial_migration_creates_all_tables() -> None:
    """Alembic upgrade should create all storage tables on a test database."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        database_path = Path(tmp_dir) / "storage_test.db"
        database_url = f"sqlite+aiosqlite:///{database_path}"
        inspection_url = f"sqlite:///{database_path}"

        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)

        command.upgrade(config, "head")

        engine = create_engine(inspection_url)
        with engine.begin() as connection:
            table_names = set(inspect(connection).get_table_names())
        engine.dispose()

    assert table_names >= {"skill", "skill_frequency", "layout_snapshot"}


def test_storage_server_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "storage-server"}



