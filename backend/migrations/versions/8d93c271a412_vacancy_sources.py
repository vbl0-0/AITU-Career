"""Vacancy provenance and availability without changing existing job identities."""
from alembic import op
import sqlalchemy as sa

revision = '8d93c271a412'
down_revision = '5e40aaabe13b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('jobs', sa.Column('source', sa.String(20), server_default='manual', nullable=False))
    op.add_column('jobs', sa.Column('external_id', sa.String(80), nullable=True))
    op.add_column('jobs', sa.Column('source_url', sa.String(500), nullable=True))
    op.add_column('jobs', sa.Column('source_published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.execute("UPDATE jobs SET source = 'demo' WHERE is_demo = true")
    op.create_unique_constraint('uq_jobs_source_external_id', 'jobs', ['source', 'external_id'])


def downgrade():
    op.drop_constraint('uq_jobs_source_external_id', 'jobs', type_='unique')
    for column in ('is_active', 'last_synced_at', 'source_published_at', 'source_url', 'external_id', 'source'):
        op.drop_column('jobs', column)
