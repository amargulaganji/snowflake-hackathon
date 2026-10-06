from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import AskRequest, AskResponse
from app.services.snowflake_client import agent_client
from app.services.response_parser import parse_agent_response
from app.services import audit_service
from app.services.role_auth import require_permission, AuthenticatedUser

router = APIRouter(tags=["agent"])


@router.post("/ask", response_model=AskResponse)
async def ask_agent(
    req: AskRequest,
    user: AuthenticatedUser = Depends(require_permission),
):
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

    start = time.perf_counter()
    try:
        raw = await agent_client.run_agent(messages)
        result = parse_agent_response(raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    latency_ms = int((time.perf_counter() - start) * 1000)

    tools_invoked = [e.source_name for e in result.evidence_chain]
    sources_used = [e.source_type for e in result.evidence_chain]

    await audit_service.log_audit(
        user_id=user.username,
        user_role=user.role,
        member_id=req.member_id,
        action="ask",
        question=req.question,
        tools_invoked=tools_invoked or None,
        sources_used=list(set(sources_used)) if sources_used else None,
        risk_level=result.risk_level,
        contradiction=result.contradiction_detected,
        insufficient=result.insufficient_evidence,
        response_preview=result.answer[:500] if result.answer else None,
        latency_ms=latency_ms,
    )

    return result
