from __future__ import annotations

from app.services.sql_client import sql_client, _bind


async def log_audit(
    user_id: str,
    user_role: str,
    member_id: str | None,
    action: str,
    question: str,
    tools_invoked: list[str] | None = None,
    sources_used: list[str] | None = None,
    risk_level: str | None = None,
    contradiction: bool = False,
    insufficient: bool = False,
    response_preview: str | None = None,
    latency_ms: int | None = None,
) -> None:
    tools_str = ",".join(tools_invoked) if tools_invoked else None
    sources_str = ",".join(sources_used) if sources_used else None

    sql = """
        INSERT INTO AI_AUDIT_LOG (
            USER_ID, USER_ROLE, MEMBER_ID, ACTION, QUESTION,
            TOOLS_INVOKED, SOURCES_USED, RISK_LEVEL,
            CONTRADICTION_DETECTED, INSUFFICIENT_EVIDENCE,
            RESPONSE_PREVIEW, LATENCY_MS, CREATED_AT
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, CURRENT_TIMESTAMP()
        )
    """
    params = [
        user_id, user_role, member_id, action, question[:2000],
        tools_str, sources_str, risk_level,
        contradiction, insufficient,
        response_preview[:500] if response_preview else None,
        latency_ms,
    ]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
    except Exception:
        pass
