"""Employee and salary history API routes."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_database_connection
from app.schemas import (
    EmployeeCreate,
    EmployeeDetailResponse,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
    SalaryRecordCreate,
    SalaryRecordResponse,
)

router = APIRouter(prefix="/api/employees", tags=["employees"])
Database = Annotated[sqlite3.Connection, Depends(get_database_connection)]


def _employee_dict(row: sqlite3.Row) -> dict[str, object]:
    return {key: row[key] for key in row.keys()}


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    connection: Database,
    search: Annotated[str | None, Query(max_length=100)] = None,
    country: Annotated[str | None, Query(max_length=100)] = None,
    department: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, object]:
    """Return a filtered, paginated employee directory."""
    clauses: list[str] = []
    parameters: list[object] = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        clauses.append(
            "(name LIKE ? COLLATE NOCASE OR email LIKE ? COLLATE NOCASE "
            "OR employee_number LIKE ? COLLATE NOCASE)"
        )
        parameters.extend((pattern, pattern, pattern))
    if country and country.strip():
        clauses.append("country = ? COLLATE NOCASE")
        parameters.append(country.strip())
    if department and department.strip():
        clauses.append("department = ? COLLATE NOCASE")
        parameters.append(department.strip())

    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = connection.execute(
        f"SELECT COUNT(*) FROM employees{where_clause}", parameters
    ).fetchone()[0]
    offset = (page - 1) * page_size
    rows = connection.execute(
        "SELECT id, employee_number, name, email, country, department, job_title, hire_date "
        f"FROM employees{where_clause} "
        "ORDER BY name COLLATE NOCASE, id LIMIT ? OFFSET ?",
        [*parameters, page_size, offset],
    ).fetchall()
    return {
        "items": [_employee_dict(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, connection: Database) -> dict[str, object]:
    """Create an employee profile."""
    try:
        cursor = connection.execute(
            "INSERT INTO employees "
            "(employee_number, name, email, country, department, job_title, hire_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                payload.employee_number,
                payload.name,
                payload.email,
                payload.country,
                payload.department,
                payload.job_title,
                payload.hire_date.isoformat(),
            ),
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number or email already exists",
        ) from exc

    row = connection.execute(
        "SELECT id, employee_number, name, email, country, department, job_title, hire_date "
        "FROM employees WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return _employee_dict(row)


def _require_employee(connection: sqlite3.Connection, employee_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT id, employee_number, name, email, country, department, job_title, hire_date "
        "FROM employees WHERE id = ?",
        (employee_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return row


def _salary_rows(connection: sqlite3.Connection, employee_id: int) -> list[dict[str, object]]:
    rows = connection.execute(
        "SELECT id, employee_id, amount_minor, currency_code, effective_date "
        "FROM salary_records WHERE employee_id = ? "
        "ORDER BY effective_date DESC, id DESC",
        (employee_id,),
    ).fetchall()
    return [_employee_dict(row) for row in rows]


@router.get("/{employee_id}", response_model=EmployeeDetailResponse)
def get_employee(employee_id: int, connection: Database) -> dict[str, object]:
    """Return an employee profile with the latest pay and complete history."""
    employee = _employee_dict(_require_employee(connection, employee_id))
    salary_history = _salary_rows(connection, employee_id)
    return {
        **employee,
        "latest_salary": salary_history[0] if salary_history else None,
        "salary_history": salary_history,
    }


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    connection: Database,
) -> dict[str, object]:
    """Update supplied employee profile fields."""
    _require_employee(connection, employee_id)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if key == "hire_date":
            changes[key] = value.isoformat()
    assignments = ", ".join(f"{key} = ?" for key in changes)
    values = [*changes.values(), employee_id]
    try:
        connection.execute(
            f"UPDATE employees SET {assignments}, "
            "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            values,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already belongs to another employee",
        ) from exc
    return _employee_dict(_require_employee(connection, employee_id))


@router.post(
    "/{employee_id}/salaries",
    response_model=SalaryRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_salary_record(
    employee_id: int,
    payload: SalaryRecordCreate,
    connection: Database,
) -> dict[str, object]:
    """Append an effective-dated salary record for an employee."""
    _require_employee(connection, employee_id)
    cursor = connection.execute(
        "INSERT INTO salary_records (employee_id, amount_minor, currency_code, effective_date) "
        "VALUES (?, ?, ?, ?)",
        (employee_id, payload.amount_minor, payload.currency_code, payload.effective_date.isoformat()),
    )
    row = connection.execute(
        "SELECT id, employee_id, amount_minor, currency_code, effective_date "
        "FROM salary_records WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return _employee_dict(row)


@router.get("/{employee_id}/salaries", response_model=list[SalaryRecordResponse])
def get_salary_history(employee_id: int, connection: Database) -> list[dict[str, object]]:
    """Return salary records newest effective date first."""
    _require_employee(connection, employee_id)
    return _salary_rows(connection, employee_id)
