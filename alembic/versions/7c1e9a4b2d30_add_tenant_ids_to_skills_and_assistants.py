"""Add tenant_ids to skills and assistants.

Revision ID: 7c1e9a4b2d30
Revises: f2a52438efd7
Create Date: 2026-08-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "7c1e9a4b2d30"
down_revision = "f2a52438efd7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tenant_array = postgresql.ARRAY(sa.String(length=255))
    op.add_column(
        "skills",
        sa.Column("tenant_ids", tenant_array, nullable=True, comment="Tenant IDs"),
    )
    op.add_column(
        "assistants",
        sa.Column("tenant_ids", tenant_array, nullable=True, comment="Tenant IDs"),
    )

    op.execute(
        """
        UPDATE skills
        SET tenant_ids = ARRAY[tenant_id]
        WHERE tenant_id IS NOT NULL
          AND (tenant_ids IS NULL OR cardinality(tenant_ids) = 0)
        """
    )
    op.execute(
        """
        UPDATE assistants
        SET tenant_ids = ARRAY[tenant_id]
        WHERE tenant_id IS NOT NULL
          AND (tenant_ids IS NULL OR cardinality(tenant_ids) = 0)
        """
    )

    op.create_index(
        "idx_skills_tenant_ids", "skills", ["tenant_ids"], postgresql_using="gin"
    )
    op.create_index(
        "idx_assistants_tenant_ids",
        "assistants",
        ["tenant_ids"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_assistants_tenant_ids", table_name="assistants")
    op.drop_index("idx_skills_tenant_ids", table_name="skills")
    op.drop_column("assistants", "tenant_ids")
    op.drop_column("skills", "tenant_ids")
