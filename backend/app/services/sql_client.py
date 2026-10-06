from __future__ import annotations

from typing import Optional

import httpx

from app.auth import get_service_auth_headers
from app.config import settings


class SnowflakeSQLClient:
    def __init__(self) -> None:
        base = settings.effective_account_url.rstrip("/")
        self.url = f"{base}/api/v2/statements"

    async def execute(
        self,
        sql: str,
        caller_headers: dict[str, str] | None = None,
        bindings: dict[str, dict[str, str]] | None = None,
    ) -> list[dict]:
        headers = caller_headers or get_service_auth_headers()
        payload: dict = {
            "statement": sql,
            "timeout": 30,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "warehouse": settings.snowflake_warehouse,
        }
        if bindings:
            payload["bindings"] = bindings

        async with httpx.AsyncClient(timeout=60.0, verify=True) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        columns = [col["name"] for col in data.get("resultSetMetaData", {}).get("rowType", [])]
        rows = data.get("data", [])
        return [dict(zip(columns, row)) for row in rows]


def _bind(params: list) -> dict[str, dict[str, str]]:
    """Build a bindings dict for Snowflake REST API from a list of values.

    Each value is mapped to a positional key ("1", "2", ...) with its
    Snowflake type inferred from the Python type.
    """
    bindings = {}
    for i, val in enumerate(params, start=1):
        if val is None:
            bindings[str(i)] = {"type": "TEXT", "value": None}
        elif isinstance(val, bool):
            bindings[str(i)] = {"type": "BOOLEAN", "value": str(val).lower()}
        elif isinstance(val, int):
            bindings[str(i)] = {"type": "FIXED", "value": str(val)}
        elif isinstance(val, float):
            bindings[str(i)] = {"type": "REAL", "value": str(val)}
        else:
            bindings[str(i)] = {"type": "TEXT", "value": str(val)}
    return bindings


sql_client = SnowflakeSQLClient()
