"""Initial JanSetu relational schema; only creates missing schema tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
from app.main import Base
revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    # Creates the declared tables; no existing table/column is dropped or altered.
    bind=op.get_bind()
    Base.metadata.create_all(bind=bind,checkfirst=True)
def downgrade():
    # Intentionally non-destructive: shared database objects are never dropped.
    pass
