"""Refresh reporting views after the enriched position columns."""

from alembic import op

from app.db.reporting import REPORTING_OBJECTS, reporting_objects_down_sql


revision = "0005_refresh_reporting_views"
down_revision = "0004_yield_coupons_reversals"
branch_labels = None
depends_on = None


def upgrade():
    for statement in reporting_objects_down_sql():
        op.execute(statement)
    for statement in REPORTING_OBJECTS:
        op.execute(statement)


def downgrade():
    for statement in reporting_objects_down_sql():
        op.execute(statement)
