from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.models.schemas import SwitchRoleRequest
from app.services.role_auth import check_role
from app.services.sql_client import sql_client

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(_role: str = Depends(check_role)):
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


@router.get("/users/current")
async def current_user(request: Request):
    role = request.headers.get("X-User-Role", "admin")
    return {
        "user_id": "demo-user",
        "user_name": "Demo User",
        "user_role": role,
    }


@router.post("/users/switch-role")
async def switch_role(req: SwitchRoleRequest, _role: str = Depends(check_role)):
    return {
        "status": "switched",
        "new_role": req.role,
    }


@router.get("/audit")
async def list_audit(
    member_id: str | None = Query(None),
    user_role: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    conditions: list[str] = []
    if member_id:
        conditions.append(f"MEMBER_ID = '{member_id.replace(chr(39), chr(39)*2)}'")
    if user_role:
        conditions.append(f"USER_ROLE = '{user_role.replace(chr(39), chr(39)*2)}'")

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT AUDIT_ID, USER_ID, USER_ROLE, MEMBER_ID, ACTION, QUESTION,
               TOOLS_INVOKED, SOURCES_USED, RISK_LEVEL,
               CONTRADICTION_DETECTED, INSUFFICIENT_EVIDENCE,
               RESPONSE_PREVIEW, LATENCY_MS,
               TO_VARCHAR(TIMESTAMP, 'YYYY-MM-DD HH24:MI') AS TIMESTAMP
        FROM AI_AUDIT_LOG{where}
        ORDER BY TIMESTAMP DESC
        LIMIT {limit}
    """
    try:
        rows = await sql_client.execute(sql)
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


@router.get("/jobs")
async def list_jobs(limit: int = Query(20, ge=1, le=100), _role: str = Depends(check_role)):
    sql = f"""
        SELECT NAME, STATE, ERROR_CODE, ERROR_MESSAGE,
               TO_VARCHAR(TO_TIMESTAMP(SCHEDULED_TIME), 'YYYY-MM-DD HH24:MI:SS') AS SCHEDULED_TIME,
               TO_VARCHAR(TO_TIMESTAMP(COMPLETED_TIME), 'YYYY-MM-DD HH24:MI:SS') AS COMPLETED_TIME,
               TO_VARCHAR(TO_TIMESTAMP(QUERY_START_TIME), 'YYYY-MM-DD HH24:MI:SS') AS QUERY_START_TIME,
               DATABASE_NAME, SCHEMA_NAME
        FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
            RESULT_LIMIT => {limit}
        ))
        WHERE DATABASE_NAME = 'CLINICAL_COPILOT'
        ORDER BY SCHEDULED_TIME DESC
    """
    try:
        rows = await sql_client.execute(sql)
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
