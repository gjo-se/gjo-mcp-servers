"""initial storage schema

Revision ID: 0001_initial_storage_schema
Revises:
Create Date: 2026-04-08 00:00:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_storage_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "layout_snapshot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("selector", sa.String(length=255), nullable=False),
        sa.Column("snapshot_content", sa.Text(), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_layout_snapshot_url"),
        "layout_snapshot",
        ["url"],
        unique=False,
    )

    op.create_table(
        "skill",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skill_name"), "skill", ["name"], unique=True)

    op.create_table(
        "skill_frequency",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("source_query", sa.String(length=255), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skill.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "skill_id",
            "source_query",
            name="uq_skill_frequency_skill_query",
        ),
    )


def downgrade() -> None:
    op.drop_table("skill_frequency")
    op.drop_index(op.f("ix_skill_name"), table_name="skill")
    op.drop_table("skill")
    op.drop_index(op.f("ix_layout_snapshot_url"), table_name="layout_snapshot")
    op.drop_table("layout_snapshot")
