"""Add yield, coupon, fee and accounting reversal controls."""

import sqlalchemy as sa
from alembic import op

from app.db.reporting import REPORTING_OBJECTS, reporting_objects_down_sql


revision = "0004_yield_coupons_reversals"
down_revision = "0003_reporting_views"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def add_column_if_missing(table: str, column: sa.Column) -> None:
        if column.name not in {item["name"] for item in inspector.get_columns(table)}:
            op.add_column(table, column)

    for statement in reporting_objects_down_sql():
        op.execute(statement)
    add_column_if_missing("instruments", sa.Column("entry_fee_rate", sa.Numeric(7, 4), server_default="0", nullable=False))
    add_column_if_missing("subscriptions", sa.Column("fee_amount", sa.Numeric(18, 2), server_default="0", nullable=False))
    add_column_if_missing("transactions", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    add_column_if_missing("transactions", sa.Column("reversal_of_transaction_id", sa.Integer(), nullable=True))
    add_column_if_missing("transactions", sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("transactions", sa.Column("reversal_reason", sa.Text(), nullable=True))
    foreign_keys = {item["name"] for item in inspector.get_foreign_keys("transactions")}
    if "fk_transactions_reversal_of" not in foreign_keys:
        op.create_foreign_key("fk_transactions_reversal_of", "transactions", "transactions", ["reversal_of_transaction_id"], ["id"])
    add_column_if_missing("accounting_entries", sa.Column("posting_version", sa.Integer(), server_default="1", nullable=False))
    add_column_if_missing("accounting_entries", sa.Column("is_reversal", sa.Boolean(), server_default=sa.false(), nullable=False))
    unique_constraints = {item["name"] for item in inspector.get_unique_constraints("interest_payments")}
    if "uq_interest_payment_subscription_date" not in unique_constraints:
        op.create_unique_constraint("uq_interest_payment_subscription_date", "interest_payments", ["subscription_id", "payment_date"])
    for statement in REPORTING_OBJECTS:
        op.execute(statement)


def downgrade():
    for statement in reporting_objects_down_sql():
        op.execute(statement)
    op.drop_constraint("uq_interest_payment_subscription_date", "interest_payments", type_="unique")
    op.drop_column("accounting_entries", "is_reversal")
    op.drop_column("accounting_entries", "posting_version")
    op.drop_constraint("fk_transactions_reversal_of", "transactions", type_="foreignkey")
    op.drop_column("transactions", "reversal_reason")
    op.drop_column("transactions", "reversed_at")
    op.drop_column("transactions", "reversal_of_transaction_id")
    op.drop_column("transactions", "version")
    op.drop_column("subscriptions", "fee_amount")
    op.drop_column("instruments", "entry_fee_rate")
