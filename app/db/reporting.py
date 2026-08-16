"""Objets PostgreSQL dédiés aux lectures de reporting.

Les vues restent volontairement en lecture seule : elles ne remplacent pas le
coeur transactionnel et servent uniquement les dashboards et les extractions
opérationnelles.
"""

REPORTING_OBJECTS = (
    """
    CREATE OR REPLACE FUNCTION profin_order_next_step(p_order_id INTEGER)
    RETURNS TEXT
    LANGUAGE SQL
    STABLE
    AS $$
        SELECT step_code
        FROM order_workflow_steps
        WHERE order_id = p_order_id AND status = 'PENDING'
        ORDER BY CASE step_code
            WHEN 'CONFORMITE' THEN 1
            WHEN 'BACK_OFFICE' THEN 2
            WHEN 'CHECKER' THEN 3
            ELSE 99
        END
        LIMIT 1
    $$;
    """,
    """
    CREATE OR REPLACE VIEW vw_reporting_client_positions AS
    SELECT
        ar.client_id,
        a.id AS account_id,
        a.account_number,
        a.currency AS account_currency,
        s.id AS subscription_id,
        s.instrument_id,
        i.code AS instrument_code,
        i.name AS instrument_name,
        COALESCE(it.code, 'AUTRE') AS instrument_type_code,
        COALESCE(it.name, 'Autre') AS instrument_type_name,
        s.invested_amount,
        s.current_value,
        s.accrued_interest,
        s.current_value - s.invested_amount AS return_amount,
        CASE WHEN s.invested_amount = 0 THEN 0
             ELSE (s.current_value - s.invested_amount) / s.invested_amount * 100
        END AS return_percentage,
        s.subscribed_at,
        s.effective_maturity_date,
        s.status
    FROM account_roles ar
    JOIN accounts a ON a.id = ar.account_id
    JOIN subscriptions s ON s.account_id = a.id
    JOIN instruments i ON i.id = s.instrument_id
    LEFT JOIN instrument_types it ON it.id = i.instrument_type_id
    WHERE ar.is_active = TRUE AND s.status = 'ACTIVE';
    """,
    """
    CREATE OR REPLACE VIEW vw_reporting_order_pipeline AS
    SELECT
        io.id AS order_id,
        io.client_id,
        io.account_id,
        a.account_number,
        a.currency AS account_currency,
        io.instrument_id,
        i.code AS instrument_code,
        i.name AS instrument_name,
        io.amount,
        io.units,
        io.currency,
        io.status,
        io.created_at,
        io.updated_at,
        GREATEST(CURRENT_DATE - io.created_at::date, 0) AS age_days,
        profin_order_next_step(io.id) AS next_step
    FROM investment_orders io
    JOIN accounts a ON a.id = io.account_id
    JOIN instruments i ON i.id = io.instrument_id;
    """,
    """
    CREATE OR REPLACE VIEW vw_reporting_transaction_queue AS
    SELECT DISTINCT
        t.id AS transaction_id,
        t.transaction_type,
        t.amount,
        t.currency,
        t.status,
        t.created_at,
        t.is_automatic,
        t.source_account_id,
        t.destination_account_id,
        COALESCE(src.account_number, dst.account_number) AS account_number,
        COALESCE(t.source_account_id, t.destination_account_id) AS relevant_account_id,
        t.created_by_client_id,
        t.approved_by_client_id
    FROM transactions t
    LEFT JOIN accounts src ON src.id = t.source_account_id
    LEFT JOIN accounts dst ON dst.id = t.destination_account_id
    WHERE t.status = 'PENDING_APPROVAL';
    """,
)


def reporting_objects_down_sql() -> tuple[str, ...]:
    return (
        "DROP VIEW IF EXISTS vw_reporting_transaction_queue",
        "DROP VIEW IF EXISTS vw_reporting_order_pipeline",
        "DROP VIEW IF EXISTS vw_reporting_client_positions",
        "DROP FUNCTION IF EXISTS profin_order_next_step(INTEGER)",
    )
