"""Validation tests for employee and salary API schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import EmployeeCreate, EmployeeUpdate, SalaryRecordCreate


def valid_employee() -> dict[str, object]:
    return {
        "employee_number": "AC-1001",
        "name": "Jordan Lee",
        "email": "jordan.lee@example.test",
        "country": "India",
        "department": "Engineering",
        "job_title": "Software Engineer",
        "hire_date": "2024-03-15",
    }


def test_employee_create_trims_text_and_parses_iso_date() -> None:
    payload = valid_employee() | {"name": "  Jordan Lee  "}

    employee = EmployeeCreate.model_validate(payload)

    assert employee.name == "Jordan Lee"
    assert employee.hire_date == date(2024, 3, 15)


@pytest.mark.parametrize(
    "changes",
    [
        {"email": "not-an-email"},
        {"name": "   "},
        {"hire_date": "15/03/2024"},
        {"unexpected": "field"},
    ],
)
def test_employee_create_rejects_invalid_values(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate.model_validate(valid_employee() | changes)


def test_employee_update_requires_a_nonempty_valid_patch() -> None:
    with pytest.raises(ValidationError):
        EmployeeUpdate.model_validate({})

    with pytest.raises(ValidationError):
        EmployeeUpdate.model_validate({"department": "  "})

    assert EmployeeUpdate.model_validate({"department": "Finance"}).department == "Finance"


def test_salary_create_validates_positive_minor_units_currency_and_date() -> None:
    salary = SalaryRecordCreate.model_validate(
        {"amount_minor": 8250000, "currency_code": "USD", "effective_date": "2026-01-01"}
    )

    assert salary.amount_minor == 8250000
    assert salary.effective_date == date(2026, 1, 1)

    for payload in (
        {"amount_minor": 0, "currency_code": "USD", "effective_date": "2026-01-01"},
        {"amount_minor": 100, "currency_code": "usd", "effective_date": "2026-01-01"},
        {"amount_minor": 100, "currency_code": "US", "effective_date": "2026-01-01"},
        {"amount_minor": 100, "currency_code": "USD", "effective_date": "2026-13-01"},
    ):
        with pytest.raises(ValidationError):
            SalaryRecordCreate.model_validate(payload)
