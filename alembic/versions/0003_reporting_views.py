"""Add PostgreSQL reporting views for client and back-office dashboards."""

from alembic import op
from sqlalchemy import text

from app.db.reporting import REPORTING_OBJECTS, reporting_objects_down_sql


revision = "0003_reporting_views"
down_revision = "0002_investment_orders"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for statement in REPORTING_OBJECTS:
        bind.execute(text(statement))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for statement in reporting_objects_down_sql():
        bind.execute(text(statement))
