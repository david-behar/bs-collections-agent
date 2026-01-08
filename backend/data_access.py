from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

try:
    import dataiku  # type: ignore
except ImportError:  # pragma: no cover - local dev fallback
    dataiku = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DATASET_NAME = os.getenv("DATAIKU_DATASET", "sonar_emails_generated")
FOLDER_ID = os.getenv("DATAIKU_FOLDER", "tuOw3D5i")
CACHE_TTL_MINUTES = int(os.getenv("DATA_CACHE_TTL_MINUTES", "5"))

_ATTACHMENT_COLUMNS: Dict[str, Tuple[str, str]] = {
    "invoice": ("path_invoice", "Customer invoice"),
    "contract": ("path_contract", "Master contract"),
    "pod": ("path_pod", "Proof of delivery"),
}

_FALLBACK_ROWS: List[Dict[str, Any]] = [
    {
        "case_id": "DSP-PLACEHOLDER",
        "company": "Sample Manufacturing",
        "email_body": "Placeholder email body",
        "llm_output": "<p>Placeholder LLM output</p>",
        "path_invoice": "",
        "path_contract": "",
        "path_pod": "",
    }
]

_CACHE: Dict[str, Any] = {"rows": _FALLBACK_ROWS, "expires_at": datetime.min}


def _load_rows() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    cached_rows = _CACHE.get("rows", [])
    expires_at: datetime = _CACHE.get("expires_at", datetime.min)

    if cached_rows and expires_at > now:
        return cached_rows

    if dataiku is None:
        LOGGER.warning("dataiku package unavailable; falling back to sample rows")
        return cached_rows

    try:
        dataset = dataiku.Dataset(DATASET_NAME)
        rows = list(dataset.iter_rows())
    except Exception as exc:  # pragma: no cover - DSS specific failure
        LOGGER.exception("Failed to load dataset %s: %s", DATASET_NAME, exc)
        return cached_rows or _FALLBACK_ROWS

    if not rows:
        LOGGER.warning("Dataset %s is empty; returning fallback rows", DATASET_NAME)
        rows = _FALLBACK_ROWS

    _CACHE["rows"] = rows
    _CACHE["expires_at"] = now + timedelta(minutes=CACHE_TTL_MINUTES)
    return rows


def _normalize_case_id(raw: Any) -> str:
    return str(raw).strip()


def list_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for row in _load_rows():
        case_id = _normalize_case_id(row.get("case_id"))
        if not case_id:
            continue
        attachments_available = sum(bool(row.get(column)) for column, _ in _ATTACHMENT_COLUMNS.values())
        cases.append(
            {
                "case_id": case_id,
                "company": row.get("company") or "",
                "email_excerpt": (row.get("email_body") or "")[:140],
                "attachments": attachments_available,
            }
        )
    return cases


def _get_case_row(case_id: str) -> Dict[str, Any]:
    target = _normalize_case_id(case_id)
    for row in _load_rows():
        if _normalize_case_id(row.get("case_id")) == target:
            return row
    raise KeyError(f"Case {case_id} not found")


def get_case_payload(case_id: str) -> Dict[str, Any]:
    row = _get_case_row(case_id)
    attachments = []
    for doc_type, (column, label) in _ATTACHMENT_COLUMNS.items():
        rel_path = row.get(column)
        if rel_path:
            attachments.append(
                {
                    "type": doc_type,
                    "label": label,
                    "filename": os.path.basename(rel_path),
                    "download_url": f"api/cases/{case_id}/attachments/{doc_type}",
                }
            )

    return {
        "case_id": case_id,
        "company": row.get("company") or "",
        "email_body": row.get("email_body") or "",
        "llm_output": row.get("llm_output") or "",
        "attachments": attachments,
    }


def get_attachment_stream(case_id: str, doc_type: str) -> Tuple[io.BytesIO, str]:
    doc_key = doc_type.lower()
    if doc_key not in _ATTACHMENT_COLUMNS:
        raise KeyError(f"Unsupported attachment type: {doc_type}")

    row = _get_case_row(case_id)
    column, _ = _ATTACHMENT_COLUMNS[doc_key]
    rel_path = row.get(column)
    if not rel_path:
        raise FileNotFoundError(f"No attachment stored for {doc_type}")

    if dataiku is None:
        raise FileNotFoundError("Dataiku API unavailable")

    folder = dataiku.Folder(FOLDER_ID)
    try:
        with folder.get_download_stream(rel_path) as stream:
            payload = stream.read()
    except Exception as exc:  # pragma: no cover
        raise FileNotFoundError(f"Unable to read attachment {rel_path}") from exc

    buffer = io.BytesIO(payload)
    buffer.seek(0)
    filename = os.path.basename(rel_path)
    return buffer, filename
