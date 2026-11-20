# ACME Salary Management

Web application for managing employee profiles and effective-dated salary records, with compensation summaries for a 10,000-person synthetic workforce.

## Project structure

- `backend/` — Python API, SQLite persistence, seed script, and backend tests.
- `frontend/` — React user interface.
- `docs/` — requirements, architecture, and API notes.

## Backend quick start

From the repository root, create and activate a Python virtual environment, then install the backend dependencies and start the API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/health`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

Run backend tests from the `backend/` directory:

```powershell
python -m pytest
```

Frontend setup and database/seed commands will be documented as those steps are implemented.

## Scope

This assessment demo assumes one trusted HR user and does not include authentication. Seed data is synthetic. Salary summaries keep currencies separate; the app does not perform foreign exchange conversion.
