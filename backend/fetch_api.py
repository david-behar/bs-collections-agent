from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from . import data_access

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["cases"])


@router.get("/cases")
async def list_cases() -> dict:
    cases = data_access.list_cases()
    LOGGER.debug("list_cases returned %s rows", len(cases))
    return {"cases": cases}


@router.get("/cases/{case_id}")
async def get_case(case_id: str) -> dict:
    try:
        payload = data_access.get_case_payload(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found") from exc
    return payload


@router.get("/cases/{case_id}/attachments/{doc_type}")
async def download_attachment(case_id: str, doc_type: str) -> StreamingResponse:
    try:
        buffer, filename = data_access.get_attachment_stream(case_id, doc_type)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Unsupported attachment type") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attachment not found") from exc

    buffer.seek(0)
    headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    LOGGER.debug(
        "download_attachment streaming %s/%s as %s bytes", case_id, doc_type, buffer.getbuffer().nbytes
    )
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)
