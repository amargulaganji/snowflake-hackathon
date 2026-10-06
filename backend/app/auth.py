from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Request, HTTPException

from app.config import settings

SPCS_TOKEN_PATH = Path("/snowflake/session/token")


def _is_spcs() -> bool:
    return os.getenv("SNOWFLAKE_HOST") is not None and SPCS_TOKEN_PATH.exists()


def _read_spcs_token() -> str:
    return SPCS_TOKEN_PATH.read_text().strip()


def get_service_auth_headers() -> dict[str, str]:
    if _is_spcs():
        return {
            "Authorization": f"Bearer {_read_spcs_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    return {
        "Authorization": f"Bearer {settings.snowflake_pat}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
    }


# Keep backward-compatible alias used by snowflake_client.py
get_auth_headers = get_service_auth_headers


def get_caller_auth_headers(request: Request) -> dict[str, str]:
    user_token = request.headers.get("Sf-Context-Current-User-Token")
    if _is_spcs() and user_token:
        service_token = _read_spcs_token()
        caller_token = f"{service_token}.{user_token}"
        return {
            "Authorization": f"Bearer {caller_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    return get_service_auth_headers()


def get_authenticated_user(request: Request) -> str:
    sf_user = request.headers.get("Sf-Context-Current-User")
    if sf_user:
        return sf_user.upper()
    if not _is_spcs() and settings.snowflake_pat:
        return os.getenv("SNOWFLAKE_LOCAL_USER", "LOCAL_DEV_USER")
    return ""


def is_spcs_authenticated(request: Request) -> bool:
    return bool(request.headers.get("Sf-Context-Current-User"))


def has_caller_token(request: Request) -> bool:
    return bool(request.headers.get("Sf-Context-Current-User-Token"))
