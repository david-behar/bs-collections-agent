from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from .wsgi_dss import init_dss_app

load_dotenv()

app = FastAPI(title="Collections Agent API", version="1.0.0")
init_dss_app(app)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("VITE_API_PORT", "8000"))
    uvicorn.run("backend.wsgi:app", host="127.0.0.1", port=port, reload=True)
