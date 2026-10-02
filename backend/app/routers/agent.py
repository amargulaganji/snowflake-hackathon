from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.snowflake_client import agent_client
from app.services.response_parser import parse_agent_response

router = APIRouter(tags=["agent"])


@router.post("/ask", response_model=AskResponse)
async def ask_agent(req: AskRequest):
    messages = []
    for msg in req.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append(
        {
            "role": "user",
            "content": (
                f"Context: This question is about member {req.member_id}.\n\n"
                f"{req.question}"
            ),
        }
    )
    try:
        raw = await agent_client.run_agent(messages)
        return parse_agent_response(raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc
