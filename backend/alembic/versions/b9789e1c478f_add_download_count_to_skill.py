"""Add download_count to Skill

Revision ID: b9789e1c478f
Revises: f2a52438efd7
Create Date: 2026-06-06 22:56:08.711705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9789e1c478f'
down_revision = 'f2a52438efd7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('skills', sa.Column('download_count', sa.Integer(), server_default='0', nullable=False))
    op.create_index(op.f('ix_skills_download_count'), 'skills', ['download_count'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_skills_download_count'), table_name='skills')
    op.drop_column('skills', 'download_count')
