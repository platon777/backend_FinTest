"""Add client investment orders and workflow steps."""

from alembic import op

from app.db.database import Base
from app.models import models  # noqa: F401


revision = "0002_investment_orders"
down_revision = "0001_core_schema"
branch_labels = None
depends_on = None


def upgrade():
    # The initial prototype migration deliberately used the metadata for the
    # core schema. Keep the same idempotent approach for the additive tables so
    # existing Docker volumes upgrade without data loss.
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[models.InvestmentOrder.__table__, models.OrderWorkflowStep.__table__])


def downgrade():
    bind = op.get_bind()
    models.OrderWorkflowStep.__table__.drop(bind, checkfirst=True)
    models.InvestmentOrder.__table__.drop(bind, checkfirst=True)
