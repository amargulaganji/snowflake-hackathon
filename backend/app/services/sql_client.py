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
    ) -> list[dict]:
        headers = caller_headers or get_service_auth_headers()
        payload = {
            "statement": sql,
            "timeout": 30,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "warehouse": settings.snowflake_warehouse,
        }
        async with httpx.AsyncClient(timeout=60.0, verify=True) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        columns = [col["name"] for col in data.get("resultSetMetaData", {}).get("rowType", [])]
        rows = data.get("data", [])
        return [dict(zip(columns, row)) for row in rows]


sql_client = SnowflakeSQLClient()
