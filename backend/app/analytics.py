"""SQL-backed compensation summary endpoints."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.database import get_database_connection
from app.schemas import AnalyticsSummaryResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
Database = Annotated[sqlite3.Connection, Depends(get_database_connection)]

CURRENT_SALARY_CTE = """
WITH current_salary AS (
    SELECT employee_id, amount_minor, currency_code
    FROM (
        SELECT employee_id, amount_minor, currency_code,
               ROW_NUMBER() OVER (
                   PARTITION BY employee_id
                   ORDER BY effective_date DESC, id DESC
               ) AS record_rank
        FROM salary_records
    )
    WHERE record_rank = 1
)
"""


def _compensation_groups(
    connection: sqlite3.Connection,
    group_column: str | None = None,
) -> list[dict[str, object]]:
    """Aggregate current salary records without combining currencies."""
    if group_column not in (None, "country", "department"):
        raise ValueError("unsupported aggregation dimension")
    select_group = f"e.{group_column}, " if group_column else ""
    group_by = f"e.{group_column}, " if group_column else ""
    rows = connection.execute(
        CURRENT_SALARY_CTE
        + "SELECT "
        + select_group
        + "s.currency_code, COUNT(*) AS employee_count, SUM(s.amount_minor) AS salary_sum, "
        + "MIN(s.amount_minor) AS minimum_salary_minor, "
        + "MAX(s.amount_minor) AS maximum_salary_minor "
        + "FROM current_salary s JOIN employees e ON e.id = s.employee_id "
        + f"GROUP BY {group_by}s.currency_code "
        + f"ORDER BY {group_by}s.currency_code",
    ).fetchall()

    results: list[dict[str, object]] = []
    for row in rows:
        employee_count = row["employee_count"]
        group = {
            "currency_code": row["currency_code"],
            "employee_count": employee_count,
            # Round a positive integer average to the nearest minor unit, half up.
            "average_salary_minor": (row["salary_sum"] + employee_count // 2) // employee_count,
            "minimum_salary_minor": row["minimum_salary_minor"],
            "maximum_salary_minor": row["maximum_salary_minor"],
        }
        if group_column:
            group[group_column] = row[group_column]
        results.append(group)
    return results


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(connection: Database) -> dict[str, object]:
    """Return headcount and current-pay summaries, keeping currencies separate."""
    headcount = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    countries = connection.execute(
        "SELECT country, COUNT(*) AS employee_count FROM employees "
        "GROUP BY country ORDER BY country COLLATE NOCASE"
    ).fetchall()
    departments = connection.execute(
        "SELECT department, COUNT(*) AS employee_count FROM employees "
        "GROUP BY department ORDER BY department COLLATE NOCASE"
    ).fetchall()

    return {
        "headcount": headcount,
        "headcount_by_country": [dict(row) for row in countries],
        "headcount_by_department": [dict(row) for row in departments],
        "compensation_by_currency": _compensation_groups(connection),
        "compensation_by_country": _compensation_groups(connection, "country"),
        "compensation_by_department": _compensation_groups(connection, "department"),
    }
