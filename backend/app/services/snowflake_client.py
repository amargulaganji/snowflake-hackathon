from __future__ import annotations

import httpx

from app.auth import get_auth_headers
from app.config import settings


class CortexAgentClient:
    def __init__(self) -> None:
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
        headers = get_auth_headers()
        # Normalize messages: ensure content is array of {type, text} objects
        normalized = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            normalized.append({"role": msg["role"], "content": content})

        payload: dict = {"messages": normalized, "stream": stream}

        async with httpx.AsyncClient(timeout=120.0, verify=True) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()


agent_client = CortexAgentClient()
