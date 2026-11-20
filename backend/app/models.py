"""Names and lightweight helpers for persisted data entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Employee:
    id: int
    employee_number: str
    name: str
    email: str
    country: str
    department: str
    job_title: str
    hire_date: str


@dataclass(frozen=True)
class SalaryRecord:
    id: int
    employee_id: int
    amount_minor: int
    currency_code: str
    effective_date: str

