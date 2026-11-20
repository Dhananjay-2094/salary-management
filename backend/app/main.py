"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import DEFAULT_DATABASE_PATH, get_connection, initialize_database
from app.analytics import router as analytics_router
from app.employees import router as employees_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize the local schema before serving requests."""
    initialize_database(application.state.database_path)
    if os.environ.get("SEED_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
        with get_connection(application.state.database_path) as connection:
            employee_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if employee_count == 0:
            from scripts.seed import seed_database

            seed_database(application.state.database_path)
    yield

app = FastAPI(
    title="ACME Salary Management API",
    description="Employee and salary management for the ACME assessment demo.",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.database_path = DEFAULT_DATABASE_PATH
app.include_router(employees_router)
app.include_router(analytics_router)

frontend_dist = Path(os.environ.get("FRONTEND_DIST", ""))
if frontend_dist.is_dir() and (frontend_dist / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_dist / "assets"),
        name="frontend-assets",
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is available."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def frontend_index():
    """Serve the built React application when packaged with the API."""
    index_file = frontend_dist / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return JSONResponse({"name": "ACME Salary Management API", "docs": "/docs"})
