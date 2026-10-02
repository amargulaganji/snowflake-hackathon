from __future__ import annotations

import os
from pathlib import Path

from app.config import settings

SPCS_TOKEN_PATH = Path("/snowflake/session/token")


def _is_spcs() -> bool:
    return os.getenv("SNOWFLAKE_HOST") is not None and SPCS_TOKEN_PATH.exists()


def _read_spcs_token() -> str:
    return SPCS_TOKEN_PATH.read_text().strip()


def get_auth_headers() -> dict[str, str]:
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
