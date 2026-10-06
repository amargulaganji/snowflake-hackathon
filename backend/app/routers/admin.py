from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.models.schemas import SwitchRoleRequest
from app.services.role_auth import (
    require_authenticated_user,
    require_permission,
    require_role,
    AuthenticatedUser,
    ROLE_PERMISSIONS,
)
from app.services.sql_client import sql_client, _bind
from app.auth import is_spcs_authenticated, has_caller_token

router = APIRouter(tags=["admin"])


@router.get("/auth/me")
async def auth_me(user: AuthenticatedUser = Depends(require_authenticated_user)):
    allowed = ROLE_PERMISSIONS.get(user.role)
    permissions = []
    if allowed is None:
        permissions = ["*"]
    else:
        permissions = list(allowed)
    return {
        "username": user.username,
        "role": user.role,
        "permissions": permissions,
        "authentication_source": "snowflake_spcs" if is_spcs_authenticated(user.request) else "local_dev",
        "caller_rights_available": has_caller_token(user.request),
    }


@router.get("/admin/users")
async def list_users(user: AuthenticatedUser = Depends(require_role("SNOWCARE_ADMIN_ROLE"))):
    sql = """
        SELECT USER_ID, USERNAME, DISPLAY_NAME, ROLE,
               TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT
        FROM APP_USER
        ORDER BY CREATED_AT DESC
    """
    try:
        rows = await sql_client.execute(sql)
        return [
            {
                "user_id": r["USER_ID"],
                "username": r.get("USERNAME", ""),
                "display_name": r.get("DISPLAY_NAME", ""),
                "role": r.get("ROLE", ""),
                "created_at": r.get("CREATED_AT", ""),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/admin/users/current")
async def current_user(user: AuthenticatedUser = Depends(require_authenticated_user)):
    return {
        "user_id": user.username,
        "user_name": user.username,
        "user_role": user.role,
    }


@router.post("/admin/users/switch-role")
async def switch_role(
    req: SwitchRoleRequest,
    user: AuthenticatedUser = Depends(require_authenticated_user),
):
    return {
        "status": "preview_only",
        "actual_role": user.role,
        "preview_role": req.role,
        "note": "Demo role preview does not change backend authorization. "
                "Your actual permissions remain based on your Snowflake identity.",
    }


@router.get("/admin/audit")
async def list_audit(
    member_id: str | None = Query(None),
    user_role: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    user: AuthenticatedUser = Depends(
        require_role("SNOWCARE_ADMIN_ROLE", "COMPLIANCE_ANALYST_ROLE")
    ),
):
    conditions: list[str] = []
    params: list = []
    if member_id:
        conditions.append("MEMBER_ID = ?")
        params.append(member_id)
    if user_role:
        conditions.append("USER_ROLE = ?")
        params.append(user_role)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    sql = f"""
        SELECT AUDIT_ID, USER_ID, USER_ROLE, MEMBER_ID, ACTION, QUESTION,
               TOOLS_INVOKED, SOURCES_USED, RISK_LEVEL,
               CONTRADICTION_DETECTED, INSUFFICIENT_EVIDENCE,
               RESPONSE_PREVIEW, LATENCY_MS,
               TO_VARCHAR(TIMESTAMP, 'YYYY-MM-DD HH24:MI') AS TIMESTAMP
        FROM AI_AUDIT_LOG{where}
        ORDER BY TIMESTAMP DESC
        LIMIT ?
    """
    try:
        rows = await sql_client.execute(sql, bindings=_bind(params))
        return [
            {
                "audit_id": r.get("AUDIT_ID", ""),
                "user_id": r.get("USER_ID", ""),
                "user_role": r.get("USER_ROLE", ""),
                "member_id": r.get("MEMBER_ID"),
                "action": r.get("ACTION", ""),
                "question": r.get("QUESTION", ""),
                "tools_invoked": r.get("TOOLS_INVOKED", ""),
                "sources_used": r.get("SOURCES_USED", ""),
                "risk_level": r.get("RISK_LEVEL"),
                "contradiction_detected": r.get("CONTRADICTION_DETECTED", "false").lower() == "true" if isinstance(r.get("CONTRADICTION_DETECTED"), str) else bool(r.get("CONTRADICTION_DETECTED")),
                "insufficient_evidence": r.get("INSUFFICIENT_EVIDENCE", "false").lower() == "true" if isinstance(r.get("INSUFFICIENT_EVIDENCE"), str) else bool(r.get("INSUFFICIENT_EVIDENCE")),
                "response_preview": r.get("RESPONSE_PREVIEW", ""),
                "latency_ms": int(r["LATENCY_MS"]) if r.get("LATENCY_MS") else None,
                "timestamp": r.get("TIMESTAMP", ""),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/admin/jobs")
async def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    user: AuthenticatedUser = Depends(
        require_role("SNOWCARE_ADMIN_ROLE", "OPERATIONS_ANALYST_ROLE")
    ),
):
    sql = f"""
        SELECT NAME, STATE, ERROR_CODE, ERROR_MESSAGE,
               TO_VARCHAR(TO_TIMESTAMP(SCHEDULED_TIME), 'YYYY-MM-DD HH24:MI:SS') AS SCHEDULED_TIME,
               TO_VARCHAR(TO_TIMESTAMP(COMPLETED_TIME), 'YYYY-MM-DD HH24:MI:SS') AS COMPLETED_TIME,
               TO_VARCHAR(TO_TIMESTAMP(QUERY_START_TIME), 'YYYY-MM-DD HH24:MI:SS') AS QUERY_START_TIME,
               DATABASE_NAME, SCHEMA_NAME
        FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
            RESULT_LIMIT => ?
        ))
        WHERE DATABASE_NAME = 'CLINICAL_COPILOT'
        ORDER BY SCHEDULED_TIME DESC
    """
    try:
        rows = await sql_client.execute(sql, bindings=_bind([limit]))
        results = []
        for r in rows:
            state = r.get("STATE", "")
            if state == "SKIPPED":
                run_status = "SKIPPED"
                error_msg = None
            elif state == "SUCCEEDED":
                run_status = "SUCCEEDED"
                error_msg = None
            elif state == "FAILED":
                run_status = "FAILED"
                error_msg = r.get("ERROR_MESSAGE")
            elif state == "SCHEDULED":
                run_status = "SCHEDULED"
                error_msg = None
            else:
                run_status = state
                error_msg = r.get("ERROR_MESSAGE")
            results.append({
                "name": r.get("NAME", ""),
                "state": state,
                "run_status": run_status,
                "query_start_time": r.get("QUERY_START_TIME") or "",
                "completed_time": r.get("COMPLETED_TIME") or "",
                "error_code": r.get("ERROR_CODE") if state == "FAILED" else None,
                "error_message": error_msg,
                "scheduled_time": r.get("SCHEDULED_TIME") or "",
                "database_name": r.get("DATABASE_NAME", ""),
                "schema_name": r.get("SCHEMA_NAME", ""),
            })
        return results
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc
