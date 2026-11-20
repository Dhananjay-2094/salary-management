"""Tests for SQLite schema initialization and database constraints."""

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from app.database import get_connection, initialize_database


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_initialize_database_creates_tables_indexes_and_foreign_keys() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "fresh.sqlite3"

        initialize_database(database_path)

        with get_connection(database_path) as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            indexes = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
            foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]

    assert {"employees", "salary_records"}.issubset(tables)
    assert "idx_employees_country" in indexes
    assert "idx_employees_department" in indexes
    assert "idx_salary_employee_effective" in indexes
    assert foreign_keys_enabled == 1


def test_salary_record_requires_an_existing_employee() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "foreign-key.sqlite3"
        initialize_database(database_path)

        with get_connection(database_path) as connection:
            try:
                connection.execute(
                    "INSERT INTO salary_records "
                    "(employee_id, amount_minor, currency_code, effective_date) "
                    "VALUES (999, 100000, 'USD', '2026-01-01')"
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("salary record without an employee should be rejected")
