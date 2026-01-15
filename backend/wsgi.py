from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .fetch_api import router as fetch_api_router

load_dotenv()

app = FastAPI(title="Collections Agent API", version="1.0.0")


def _collect_allowed_origins() -> List[str]:
    origins: List[str] = []
    explicit_origin = os.getenv("VITE_CLIENT_ORIGIN", "").strip()
    if explicit_origin:
        origins.append(explicit_origin)

    client_port = os.getenv("VITE_CLIENT_PORT", "5173")
    origins.extend([f"http://localhost:{client_port}", f"http://127.0.0.1:{client_port}"])
    return sorted({origin for origin in origins if origin})


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
async def healthcheck() -> dict:
    return {"status": "ok"}


app.include_router(fetch_api_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("VITE_API_PORT", "8000"))
    uvicorn.run("backend.wsgi:app", host="127.0.0.1", port=port, reload=True)
