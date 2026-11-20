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

Initialize the database and seed the 10,000 synthetic employees with one command from the `backend/` directory:

```powershell
python -m scripts.seed
```

The seed command refuses to overwrite existing employees. To intentionally replace the local dataset, run `python -m scripts.seed --reset`. Use `--database path/to/file.sqlite3` to target another SQLite file.

Start the React/Vite frontend in another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Vite proxies `/health` and `/api` to the local backend at `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in `frontend/.env` to use a separately hosted API; see `frontend/.env.example`.

Create and verify the static frontend build with `npm run build` from `frontend/`.
Run the frontend interaction tests with `npm test` from `frontend/`.

## Scope

This assessment demo assumes one trusted HR user and does not include authentication. Seed data is synthetic. Salary summaries keep currencies separate; the app does not perform foreign exchange conversion.
