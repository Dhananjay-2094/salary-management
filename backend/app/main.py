"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="ACME Salary Management API",
    description="Employee and salary management for the ACME assessment demo.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is available."""
    return {"status": "ok"}
