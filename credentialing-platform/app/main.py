"""FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload

Interactive docs at http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI

from .api import integrations, providers, verifications

app = FastAPI(
    title="Credentialing Platform API",
    version="0.1.0",
    description=(
        "API-first provider credentialing & primary source verification. "
        "Ingest providers from ATS/EMR/Salesforce, then verify across "
        "NPPES, CAQH, PECOS, and state medical boards."
    ),
)

app.include_router(providers.router)
app.include_router(verifications.router)
app.include_router(integrations.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
