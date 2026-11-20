"""Tests for employee and salary route behavior against temporary SQLite."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi import HTTPException

from app.database import get_connection, initialize_database
from app.employees import (
    add_salary_record,
    create_employee,
    get_employee,
    get_salary_history,
    list_employees,
    update_employee,
)
from app.main import app
from app.schemas import EmployeeCreate, EmployeeUpdate, SalaryRecordCreate

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def make_employee(employee_number: str, email: str, name: str) -> EmployeeCreate:
    return EmployeeCreate(
        employee_number=employee_number,
        name=name,
        email=email,
        country="India",
        department="Engineering",
        job_title="Software Engineer",
        hire_date=date(2024, 3, 15),
    )


def test_employee_create_search_filter_and_pagination() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "employees.sqlite3"
        initialize_database(database_path)
        with get_connection(database_path) as connection:
            create_employee(make_employee("AC-1001", "jordan@example.test", "Jordan Lee"), connection)
            create_employee(make_employee("AC-1002", "sam@example.test", "Sam Patel"), connection)

            result = list_employees(
                connection=connection,
                search="AC-100",
                country="India",
                department="Engineering",
                page=2,
                page_size=1,
            )

    assert result["total"] == 2
    assert result["page"] == 2
    assert result["items"][0]["employee_number"] == "AC-1002"


def test_salary_history_and_latest_salary_are_ordered_deterministically() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "history.sqlite3"
        initialize_database(database_path)
        with get_connection(database_path) as connection:
            employee = create_employee(
                make_employee("AC-2001", "alex@example.test", "Alex Kim"), connection
            )
            employee_id = employee["id"]
            add_salary_record(
                employee_id,
                SalaryRecordCreate(
                    amount_minor=7000000, currency_code="INR", effective_date="2024-01-01"
                ),
                connection,
            )
            add_salary_record(
                employee_id,
                SalaryRecordCreate(
                    amount_minor=8000000, currency_code="INR", effective_date="2025-01-01"
                ),
                connection,
            )

            detail = get_employee(employee_id, connection)
            history = get_salary_history(employee_id, connection)

    assert detail["latest_salary"]["amount_minor"] == 8000000
    assert [record["effective_date"] for record in history] == ["2025-01-01", "2024-01-01"]


def test_employee_update_and_missing_employee_errors() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "updates.sqlite3"
        initialize_database(database_path)
        with get_connection(database_path) as connection:
            employee = create_employee(
                make_employee("AC-3001", "casey@example.test", "Casey Reed"), connection
            )
            updated = update_employee(
                employee["id"], EmployeeUpdate(department="Finance"), connection
            )

            with pytest.raises(HTTPException) as error:
                get_employee(9999, connection)

    assert updated["department"] == "Finance"
    assert error.value.status_code == 404


def test_employee_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert {"get", "post"}.issubset(paths["/api/employees"])
    assert {"get", "patch"}.issubset(paths["/api/employees/{employee_id}"])
    assert {"get", "post"}.issubset(paths["/api/employees/{employee_id}/salaries"])
