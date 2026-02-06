"""add project key

Revision ID: 3c7d9f5b2a11
Revises: 098b9137fbe5
Create Date: 2026-02-06 07:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c7d9f5b2a11'
down_revision = '098b9137fbe5'
branch_labels = None
depends_on = None


def upgrade():
    # Add as nullable first so existing rows can be backfilled safely.
    op.add_column('projects', sa.Column('key', sa.String(length=20), nullable=True))

    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Stable deterministic backfill for existing rows.
        op.execute("""
            UPDATE projects
            SET key = CONCAT('PRJ', id)
            WHERE key IS NULL
        """)
    else:
        # SQLite/MySQL fallback
        op.execute("""
            UPDATE projects
            SET key = 'PRJ' || id
            WHERE key IS NULL
        """)

    op.alter_column('projects', 'key', existing_type=sa.String(length=20), nullable=False)
    op.create_index(op.f('ix_projects_key'), 'projects', ['key'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_projects_key'), table_name='projects')
    op.drop_column('projects', 'key')
