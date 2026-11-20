"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import DEFAULT_DATABASE_PATH, initialize_database
from app.analytics import router as analytics_router
from app.employees import router as employees_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize the local schema before serving requests."""
    initialize_database(application.state.database_path)
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


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is available."""
    return {"status": "ok"}
