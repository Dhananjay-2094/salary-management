# Salary Management — Step-by-Step Implementation Plan

This is a build checklist for a small, end-to-end assessment project. Follow it in order and make one working commit at each milestone.

## Decisions for this assignment

- **No authentication or login.** Assume a single trusted HR manager using the demo. Do not add login pages, user tables, or role management.
- Backend: Python with FastAPI; database: SQLite; frontend: React with Vite. Use one API service (modular monolith).
- Use synthetic employee data only. Seed exactly 10,000 employees.
- Store salaries with a currency code and effective date. Keep history when salary changes.
- Never combine different currencies into a single average. Display summaries grouped by currency.
- Leave payroll processing, tax/benefits, Excel import, and currency conversion out of the first version.

## Step 1 — Write requirements before code

Create `docs/requirements.md` (one page) with the goal, user, key workflows, scope, exclusions and reasons, assumptions, and acceptance criteria. Include these criteria:

1. HR can find and view an employee among 10,000 records.
2. HR can add an employee and change employee details.
3. HR can add a salary change and view prior salary records.
4. HR can see headcount and salary summaries grouped by country, department, and currency.
5. The project can be set up locally using documented commands and seeded reproducibly.

Commit: `docs: define salary management requirements`.

## Step 2 — Set up the repository layout

Create this structure (names can be adjusted, but keep backend and frontend separate):

```text
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    employees.py
    analytics.py
  scripts/seed.py
  tests/
  requirements.txt
frontend/
  src/
    api/
    components/
    pages/
    App.jsx
  package.json
docs/
  requirements.md
```

Add `.gitignore` entries for virtual environments, `node_modules`, build output, local SQLite databases, and environment files. Add a README with the intended setup commands. Commit the scaffold.

## Step 3 — Create and verify the Python API skeleton

1. Create a Python virtual environment in `backend` and install FastAPI, Uvicorn, and the chosen SQLite access approach (SQLAlchemy is a reasonable default). Add pytest and an HTTP test client for tests.
2. Create `app/main.py`, instantiate the API, and add `GET /health` returning a small JSON status.
3. Run the API locally and request `/health` before adding database complexity.
4. Add a minimal test that calls `/health`.

Commit: `feat: add FastAPI service skeleton`.

## Step 4 — Define data and create SQLite schema

Use two core tables:

- `employees`: id, employee number, name, email, country, department, job title, hire date, created/updated timestamps.
- `salary_records`: id, employee id, amount, currency code, effective date, created timestamp.

Set employee number and email to unique. Make salary records reference an employee with a foreign key. Add indexes for employee number, name, country, department, and `(employee_id, effective_date)`. Store monetary amounts as integer minor units (for example cents) to avoid floating point errors; retain currency separately. Enable SQLite foreign keys.

Implement database initialization so a fresh checkout creates the tables. Add a short schema note to `docs/architecture.md`. Verify initialization creates the expected tables. Commit: `feat: add employee and salary database schema`.

## Step 5 — Define request/response validation

Create Pydantic schemas for employee create/update/list/detail and salary record create/list. Validate required fields, email format, positive salary amount, three-letter currency code, and ISO dates. Keep database models separate from API schemas. Return clear 404 for missing employees and 422 for invalid input.

Commit: `feat: define employee and salary API schemas`.

## Step 6 — Implement employee and salary endpoints

Implement and manually exercise these endpoints (document exact response shapes in `docs/api.md`):

- `GET /api/employees?search=&country=&department=&page=1&page_size=25` — paginated, filtered directory.
- `POST /api/employees` — create an employee.
- `GET /api/employees/{id}` — employee detail, including latest salary and history.
- `PATCH /api/employees/{id}` — update editable employee fields.
- `POST /api/employees/{id}/salaries` — add an effective-dated salary record.
- `GET /api/employees/{id}/salaries` — list salary history in date order.

Put query/database logic in small helper or repository functions rather than crowding route handlers. Ensure search and filters are parameterized. Define latest salary as the record with the newest effective date (with a stable tie-break rule). Commit in a working increment.

## Step 7 — Add deterministic 10,000-row seed data

Write `backend/scripts/seed.py`. Use Python's seeded random generator and clearly synthetic names/emails. Include a small chosen set of countries, departments, currencies, and job titles. Give every employee at least one salary record, and a subset more than one to demonstrate history. Make reruns safe: either clear and recreate only when an explicit `--reset` flag is passed, or use an idempotent upsert strategy. Print counts at completion.

Run the script on a fresh database and verify there are exactly 10,000 employees, no real personal data, and rows across the dimensions. Commit: `feat: seed 10000 synthetic employees`.

## Step 8 — Implement summary analytics

Add `GET /api/analytics/summary` returning headcount, plus salary count/average/minimum/maximum grouped by currency. Add breakdown endpoints or response sections grouped by country and department; salary metrics within each breakdown must remain currency-specific. Use SQL aggregation rather than fetching all rows into Python. Document the currency rule in the API docs and UI labels.

Commit: `feat: add salary summary analytics`.

## Step 9 — Build the React app shell and API connection

1. Create the Vite React app in `frontend` and choose a component library (for example, MUI) or simple reusable CSS components.
2. Add routes or page state for Dashboard, Employees, and Employee detail.
3. Add one API client module that uses a configurable backend base URL.
4. Configure development proxy or CORS so the frontend can call the API locally.
5. Show API loading and error states; verify the frontend can call `/health`.

Commit: `feat: add React app shell and API client`.

## Step 10 — Build the employee directory

Create a directory page with search, country and department filters, pagination, and a table showing employee number, name, department, country, and latest salary with currency. Filters and pagination should call the backend instead of loading all 10,000 records at once. Add empty and error states and a link/action to open details.

Commit: `feat: add searchable employee directory`.

## Step 11 — Build employee detail and edit flows

Create a detail page showing profile fields and salary history ordered by effective date. Add forms to create an employee, edit profile fields, and add a salary record. Show validation messages from the API, prevent accidental duplicate submissions while saving, and confirm success. Keep salary changes append-only in the UI; corrections should be a new effective-dated record for this demo.

Commit: `feat: add employee detail and salary history workflows`.

## Step 12 — Build the analytics dashboard

Show headcount cards and grouped tables/charts for compensation by country, department, and currency. Every salary amount and average must display its currency code; avoid a global cross-currency average. Keep charts simple and include a table or accessible text equivalent. Commit: `feat: add compensation dashboard`.

## Step 13 — Add meaningful automated tests

Backend tests should use a temporary SQLite database and cover:

- health and schema initialization;
- employee creation, update, not-found behavior, filters and pagination;
- validation failures;
- adding and ordering salary history;
- analytics aggregation and separation by currency;
- seed count and deterministic output (without requiring the full seed for every unit test).

Add a small number of frontend tests for directory rendering/filter interaction, form validation/error display, and currency labels. Keep tests independent of external services. Run the documented full test commands and fix failures. Commit: `test: cover core employee and salary workflows`.

## Step 14 — Polish and check the 10,000-record experience

Run the seed and use the app with the full dataset. Check directory pagination/search latency and analytics response time. Add or adjust indexes only for observed query paths. Check keyboard use, labels, responsive layout, and readable empty/loading/error states. Make sure no credentials or real personal information are committed. Authentication remains out of scope; describe the app as an assessment demo for a trusted user.

## Step 15 — Document, deploy, and record the demo

Update README with prerequisites, install steps, database initialization, seed command, run commands for backend and frontend, test commands, and deployment URL. Deploy to an environment that preserves the SQLite file (or explicitly call it a temporary demo if it does not). Verify the deployed app and seeded data. Record a short video showing dashboard, employee search, employee detail/history, salary update, and setup/test evidence. Add the video link and deployment link to README.

Commit: `docs: add setup deployment and demo instructions`.

## Recommended commit progression

Keep commits small and working, in roughly this order:

1. Requirements and architecture notes.
2. Repository scaffold and health endpoint.
3. Schema and API validation.
4. Employee/salary endpoints.
5. Seed script.
6. Analytics.
7. Frontend shell and directory.
8. Detail/history/edit forms.
9. Dashboard.
10. Tests and polish.
11. Deployment and demo documentation.

## Architecture at a glance

```text
React pages/components → HTTP JSON API (FastAPI) → validation/service logic → SQLite
```

The initial deliverable is a single-user assessment demo with no authentication, payroll execution, tax logic, or FX conversion. SQLite is appropriate for the assignment dataset and local demo; ensure the chosen deployment keeps its database file between restarts.
