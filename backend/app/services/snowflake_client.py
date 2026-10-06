from __future__ import annotations

import logging
import httpx

from app.auth import get_service_auth_headers
from app.config import settings

logger = logging.getLogger("snowcare360.agent")


class CortexAgentClient:
    def __init__(self) -> None:
        # Use effective_account_url (SNOWFLAKE_HOST inside SPCS) — the external
        # account URL is not resolvable from inside the container.
        base = settings.effective_account_url.rstrip("/")
        db = settings.snowflake_database
        schema = settings.snowflake_schema
        agent = settings.snowflake_agent_name
        self.url = (
            f"{base}/api/v2/databases/{db}/schemas/{schema}"
            f"/agents/{agent}:run"
        )

    async def run_agent(
        self,
        messages: list[dict],
        *,
        stream: bool = False,
    ) -> dict:
        headers = get_service_auth_headers()
        # Explicitly set the role so the service token uses ACCOUNTADMIN
        # (which owns the agent) rather than the token's default role.
        headers["X-Snowflake-Role"] = "ACCOUNTADMIN"
        # Normalize messages: ensure content is array of {type, text} objects
        normalized = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            normalized.append({"role": msg["role"], "content": content})

        payload: dict = {"messages": normalized, "stream": stream}

        print(f"[AGENT] Calling {self.url}", flush=True)
        async with httpx.AsyncClient(timeout=120.0, verify=True) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            if resp.status_code >= 400:
                print(f"[AGENT] ERROR {resp.status_code}: {resp.text[:2000]}", flush=True)
            resp.raise_for_status()
            return resp.json()


agent_client = CortexAgentClient()
