"""Tests for currency-safe compensation summaries."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from app.analytics import get_analytics_summary
from app.database import get_connection, initialize_database
from app.employees import add_salary_record, create_employee
from app.main import app
from app.schemas import EmployeeCreate, SalaryRecordCreate

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _employee(number: str, name: str, country: str, department: str) -> EmployeeCreate:
    return EmployeeCreate(
        employee_number=number,
        name=name,
        email=f"{number.lower()}@example.test",
        country=country,
        department=department,
        job_title="Analyst",
        hire_date=date(2022, 1, 1),
    )


def _salary(amount: int, currency: str, effective_date: str) -> SalaryRecordCreate:
    return SalaryRecordCreate(
        amount_minor=amount,
        currency_code=currency,
        effective_date=effective_date,
    )


def test_summary_uses_current_records_and_keeps_currencies_separate() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "analytics.sqlite3"
        initialize_database(database_path)
        with get_connection(database_path) as connection:
            first = create_employee(_employee("AN-1", "Ari One", "India", "Engineering"), connection)
            second = create_employee(_employee("AN-2", "Bea Two", "India", "Engineering"), connection)
            third = create_employee(_employee("AN-3", "Cam Three", "United States", "Finance"), connection)
            create_employee(_employee("AN-4", "Dee Four", "United States", "Finance"), connection)

            add_salary_record(first["id"], _salary(700, "INR", "2024-01-01"), connection)
            add_salary_record(first["id"], _salary(900, "INR", "2025-01-01"), connection)
            add_salary_record(second["id"], _salary(100, "USD", "2025-01-01"), connection)
            add_salary_record(third["id"], _salary(101, "USD", "2025-01-01"), connection)

            summary = get_analytics_summary(connection)

    assert summary["headcount"] == 4
    assert {row["country"]: row["employee_count"] for row in summary["headcount_by_country"]} == {
        "India": 2,
        "United States": 2,
    }
    by_currency = {row["currency_code"]: row for row in summary["compensation_by_currency"]}
    assert by_currency["INR"]["employee_count"] == 1
    assert by_currency["INR"]["average_salary_minor"] == 900
    assert by_currency["USD"]["employee_count"] == 2
    assert by_currency["USD"]["average_salary_minor"] == 101
    assert {row["currency_code"] for row in summary["compensation_by_country"] if row["country"] == "India"} == {
        "INR",
        "USD",
    }


def test_analytics_summary_route_is_registered() -> None:
    assert "get" in app.openapi()["paths"]["/api/analytics/summary"]
