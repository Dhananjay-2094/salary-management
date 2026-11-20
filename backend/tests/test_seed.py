"""Tests for reproducible synthetic seed data."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.analytics import get_analytics_summary
from app.database import get_connection
from scripts.seed import EMPLOYEE_COUNT, seed_database

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _data_digest(database_path: Path) -> str:
    digest = sha256()
    with get_connection(database_path) as connection:
        for table, order in (
            ("employees", "employee_number"),
            ("salary_records", "employee_id, effective_date, id"),
        ):
            rows = connection.execute(f"SELECT * FROM {table} ORDER BY {order}")
            for row in rows:
                digest.update(repr(tuple(row)).encode("utf-8"))
    return digest.hexdigest()


def test_seed_creates_ten_thousand_reproducible_employees_and_salary_history() -> None:
    with TemporaryDirectory(dir=BACKEND_ROOT) as temp_dir:
        database_path = Path(temp_dir) / "seed.sqlite3"
        result = seed_database(database_path, seed=12345)
        first_digest = _data_digest(database_path)

        assert result.employees == EMPLOYEE_COUNT
        assert result.salary_records > EMPLOYEE_COUNT

        with get_connection(database_path) as connection:
            employee_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            salary_count = connection.execute("SELECT COUNT(*) FROM salary_records").fetchone()[0]
            country_count = connection.execute(
                "SELECT COUNT(DISTINCT country) FROM employees"
            ).fetchone()[0]
            currency_count = connection.execute(
                "SELECT COUNT(DISTINCT currency_code) FROM salary_records"
            ).fetchone()[0]
            invalid_salary_dates = connection.execute(
                "SELECT COUNT(*) FROM salary_records s JOIN employees e ON e.id = s.employee_id "
                "WHERE s.effective_date < e.hire_date"
            ).fetchone()[0]
            analytics = get_analytics_summary(connection)

        assert employee_count == EMPLOYEE_COUNT
        assert salary_count == result.salary_records
        assert country_count == 10
        assert currency_count >= 9
        assert invalid_salary_dates == 0
        assert analytics["headcount"] == EMPLOYEE_COUNT
        assert sum(
            group["employee_count"] for group in analytics["compensation_by_currency"]
        ) == EMPLOYEE_COUNT

        with pytest.raises(ValueError, match="use --reset"):
            seed_database(database_path, seed=12345)

        rerun = seed_database(database_path, reset=True, seed=12345)
        assert rerun == result
        assert _data_digest(database_path) == first_digest
