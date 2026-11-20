"""SQLite connection and schema initialization helpers."""

from pathlib import Path
from contextlib import contextmanager
import sqlite3
from collections.abc import Iterator

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "salary_management.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    employee_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    country TEXT NOT NULL,
    department TEXT NOT NULL,
    job_title TEXT NOT NULL,
    hire_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS salary_records (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    currency_code TEXT NOT NULL CHECK (
        length(currency_code) = 3 AND currency_code = upper(currency_code)
    ),
    effective_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_employees_country ON employees(country);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_salary_employee_effective
    ON salary_records(employee_id, effective_date DESC, id DESC);
"""


@contextmanager
def get_connection(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Iterator[sqlite3.Connection]:
    """Yield a configured SQLite connection and always close it afterwards."""
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    """Create the database file, tables, and indexes if they do not exist."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as connection:
        connection.executescript(SCHEMA)
