from __future__ import annotations

from app.services.sql_client import sql_client


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
    safe_user_id = user_id.replace("'", "''")
    safe_role = user_role.replace("'", "''")
    safe_member = member_id.replace("'", "''") if member_id else None
    safe_action = action.replace("'", "''")
    safe_question = question.replace("'", "''")[:2000]
    safe_preview = response_preview.replace("'", "''")[:500] if response_preview else None
    safe_risk = risk_level.replace("'", "''") if risk_level else None

    tools_str = ",".join(tools_invoked) if tools_invoked else None
    sources_str = ",".join(sources_used) if sources_used else None

    member_val = f"'{safe_member}'" if safe_member else "NULL"
    risk_val = f"'{safe_risk}'" if safe_risk else "NULL"
    preview_val = f"'{safe_preview}'" if safe_preview else "NULL"
    tools_val = f"'{tools_str}'" if tools_str else "NULL"
    sources_val = f"'{sources_str}'" if sources_str else "NULL"
    latency_val = str(latency_ms) if latency_ms is not None else "NULL"

    sql = f"""
        INSERT INTO AI_AUDIT_LOG (
            USER_ID, USER_ROLE, MEMBER_ID, ACTION, QUESTION,
            TOOLS_INVOKED, SOURCES_USED, RISK_LEVEL,
            CONTRADICTION_DETECTED, INSUFFICIENT_EVIDENCE,
            RESPONSE_PREVIEW, LATENCY_MS, CREATED_AT
        ) VALUES (
            '{safe_user_id}', '{safe_role}', {member_val}, '{safe_action}', '{safe_question}',
            {tools_val}, {sources_val}, {risk_val},
            {str(contradiction).upper()}, {str(insufficient).upper()},
            {preview_val}, {latency_val}, CURRENT_TIMESTAMP()
        )
    """
    try:
        await sql_client.execute(sql)
    except Exception:
        pass
