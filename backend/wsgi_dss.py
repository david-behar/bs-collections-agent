"""DSS entry point helpers for the Collections Agent FastAPI backend."""
from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .fetch_api import router as fetch_api_router


def _collect_allowed_origins() -> List[str]:
    origins: List[str] = []
    explicit_origin = os.getenv("VITE_CLIENT_ORIGIN", "").strip()
    if explicit_origin:
        origins.append(explicit_origin)

    client_port = os.getenv("VITE_CLIENT_PORT", "5173")
    origins.extend(
        [
            f"http://localhost:{client_port}",
            f"http://127.0.0.1:{client_port}",
        ]
    )
    # Filter duplicates / empties while preserving deterministic order
    seen = set()
    deduped: List[str] = []
    for origin in origins:
        if origin and origin not in seen:
            deduped.append(origin)
            seen.add(origin)
    return deduped


def init_dss_app(app: FastAPI) -> None:
    """Attach API routes and middleware to the DSS-provided FastAPI instance."""

    allowed_origins = _collect_allowed_origins()
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health", tags=["meta"])
    async def healthcheck() -> dict:  # pragma: no cover - trivial endpoint
        return {"status": "ok"}

    app.include_router(fetch_api_router)