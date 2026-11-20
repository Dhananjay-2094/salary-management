# Initial Architecture and Data Model

## Architecture

The application is a modular monolith: a React frontend calls a Python API, and the API applies validation and business rules before reading or writing SQLite. The backend uses Python's standard-library `sqlite3` module to keep the small assessment service dependency-light.

```text
React UI → FastAPI JSON API → application logic → SQLite
```

## Data model

- `employees` stores the current employee profile. Employee number and email are unique; email uniqueness is case-insensitive.
- `salary_records` stores effective-dated pay history and references an employee. The latest record is selected by `effective_date DESC, id DESC`, making ties deterministic.
- Salary amounts are stored as positive integer minor units (such as cents) and paired with a three-letter uppercase currency code. Values in different currencies are summarized separately.
- Foreign keys are enabled on every SQLite connection. Deleting an employee cascades to that employee's salary history.
- Indexes support name search ordering, country/department filters, and per-employee salary-history lookup.

SQLite is suitable for the assignment's local demo and 10,000 seeded records. The deployed environment must preserve the database file; SQLite is not intended here as a high-concurrency, multi-writer production database.
