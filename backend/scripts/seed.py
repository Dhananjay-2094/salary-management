"""Populate SQLite with reproducible synthetic employee and salary data.

Run from ``backend/`` with ``python -m scripts.seed``. Existing data is never
silently overwritten; pass ``--reset`` to replace all employees and salaries.
"""

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import random
import sqlite3

from app.database import DEFAULT_DATABASE_PATH, get_connection, initialize_database

EMPLOYEE_COUNT = 10_000
DEFAULT_SEED = 20261121
AS_OF_DATE = date(2026, 11, 21)
SEEDED_TIMESTAMP = "2026-11-21T00:00:00.000Z"

COUNTRIES = (
    ("Australia", "AUD", 55_000, 170_000, 100),
    ("Brazil", "BRL", 60_000, 360_000, 100),
    ("Canada", "CAD", 50_000, 160_000, 100),
    ("France", "EUR", 35_000, 140_000, 100),
    ("Germany", "EUR", 38_000, 150_000, 100),
    ("India", "INR", 800_000, 4_000_000, 100),
    ("Japan", "JPY", 4_000_000, 18_000_000, 1),
    ("Singapore", "SGD", 45_000, 160_000, 100),
    ("United Kingdom", "GBP", 35_000, 130_000, 100),
    ("United States", "USD", 45_000, 180_000, 100),
)
DEPARTMENTS = (
    "Engineering",
    "Finance",
    "Human Resources",
    "Legal",
    "Marketing",
    "Operations",
    "Product",
    "Sales",
    "Support",
)
JOB_TITLES = (
    "Analyst",
    "Associate",
    "Coordinator",
    "Director",
    "Engineer",
    "Manager",
    "Principal Engineer",
    "Product Manager",
    "Senior Analyst",
    "Senior Engineer",
    "Specialist",
)
FIRST_NAMES = (
    "Alex", "Avery", "Casey", "Charlie", "Dev", "Jordan", "Kai", "Morgan",
    "Nico", "Riley", "Sam", "Taylor",
)
LAST_NAMES = (
    "Anderson", "Brown", "Chen", "Garcia", "Gupta", "Kim", "Lee", "Martin",
    "Patel", "Singh", "Smith", "Wilson",
)


@dataclass(frozen=True)
class SeedResult:
    employees: int
    salary_records: int


def _build_employee_rows(rng: random.Random) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    hire_span_days = (AS_OF_DATE - date(2000, 1, 1)).days
    for number in range(1, EMPLOYEE_COUNT + 1):
        country, _, _, _, _ = rng.choice(COUNTRIES)
        hire_date = date(2000, 1, 1) + timedelta(days=rng.randrange(hire_span_days + 1))
        rows.append(
            (
                f"AC-{number:06d}",
                f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                f"employee{number:05d}@example.test",
                country,
                rng.choice(DEPARTMENTS),
                rng.choice(JOB_TITLES),
                hire_date.isoformat(),
                SEEDED_TIMESTAMP,
                SEEDED_TIMESTAMP,
            )
        )
    return rows


def _build_salary_rows(
    employees: list[tuple[int, str, str]], rng: random.Random
) -> list[tuple[int, int, str, str]]:
    rows: list[tuple[int, int, str, str]] = []
    country_terms = {country: (currency, minimum, maximum, factor)
                     for country, currency, minimum, maximum, factor in COUNTRIES}

    for employee_id, country, hire_date_text in employees:
        currency, minimum, maximum, minor_unit_factor = country_terms[country]
        earliest_effective_date = max(date.fromisoformat(hire_date_text), date(2020, 1, 1))
        maximum_effective_offset = (AS_OF_DATE - earliest_effective_date).days
        current_major = rng.randint(minimum, maximum)
        history_count = rng.choices((1, 2, 3), weights=(55, 35, 10), k=1)[0]
        dates = sorted(
            {
                AS_OF_DATE - timedelta(days=rng.randint(0, maximum_effective_offset))
                for _ in range(history_count)
            }
        )
        # Keep at least one record and ensure the last record is the current salary.
        for index, effective_date in enumerate(dates):
            progress = (index + 1) / len(dates)
            amount = int(current_major * (0.82 + 0.18 * progress))
            amount_minor = amount * minor_unit_factor
            rows.append(
                (employee_id, amount_minor, currency, effective_date.isoformat(), SEEDED_TIMESTAMP)
            )

    return rows


def seed_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    *,
    reset: bool = False,
    seed: int = DEFAULT_SEED,
) -> SeedResult:
    """Seed exactly 10,000 synthetic employees; refuse overwrite by default."""
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        existing_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if existing_count and not reset:
            raise ValueError(
                f"Database already contains {existing_count} employees; "
                "use --reset to replace the data"
            )
        if reset:
            connection.execute("DELETE FROM employees")

        rng = random.Random(seed)
        employee_rows = _build_employee_rows(rng)
        connection.executemany(
            "INSERT INTO employees "
            "(employee_number, name, email, country, department, job_title, hire_date, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            employee_rows,
        )

        employees = [
            (row["id"], row["country"], row["hire_date"])
            for row in connection.execute(
                "SELECT id, country, hire_date FROM employees ORDER BY employee_number"
            )
        ]
        salary_rng = random.Random(seed ^ 0x5A1A7)
        salary_rows = _build_salary_rows(employees, salary_rng)
        connection.executemany(
            "INSERT INTO salary_records "
            "(employee_id, amount_minor, currency_code, effective_date, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            salary_rows,
        )

    return SeedResult(employees=len(employee_rows), salary_records=len(salary_rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help=f"SQLite file to seed (default: {DEFAULT_DATABASE_PATH})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"random seed for reproducible data (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete existing employee and salary data before seeding",
    )
    args = parser.parse_args()

    try:
        result = seed_database(args.database, reset=args.reset, seed=args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Seeded {result.employees:,} employees and {result.salary_records:,} salary records.")


if __name__ == "__main__":
    main()
