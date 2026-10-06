from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.sql_client import sql_client, _bind
from app.services.role_auth import require_permission, AuthenticatedUser

router = APIRouter(prefix="/members", tags=["members"])


def _parse_risk_flags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(f) for f in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _member_row_to_summary(r: dict) -> dict:
    return {
        "member_id": r["MEMBER_ID"],
        "first_name": r["FIRST_NAME"],
        "last_name": r["LAST_NAME"],
        "age": int(r["AGE"]) if r.get("AGE") else None,
        "gender": r.get("GENDER"),
        "plan_type": r.get("PLAN_TYPE"),
        "risk_flags": _parse_risk_flags(r.get("RISK_FLAGS")),
    }


@router.get("/top-risk")
async def top_risk_members(
    limit: int = Query(10, ge=1, le=50),
    user: AuthenticatedUser = Depends(require_permission),
):
    sql = """
        SELECT MEMBER_ID, FIRST_NAME, LAST_NAME, AGE, GENDER, PLAN_TYPE, RISK_FLAGS
        FROM MEMBER
        ORDER BY ARRAY_SIZE(RISK_FLAGS) DESC, AGE DESC
        LIMIT ?
    """
    try:
        rows = await sql_client.execute(sql, caller_headers=user.caller_headers, bindings=_bind([limit]))
        return [_member_row_to_summary(r) for r in rows]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/risk-deltas")
async def risk_deltas(user: AuthenticatedUser = Depends(require_permission)):
    sql = """
        SELECT d.MEMBER_ID, m.FIRST_NAME, m.LAST_NAME, d.OLD_RISK, d.NEW_RISK,
               TO_VARCHAR(d.CHANGED_AT, 'YYYY-MM-DD HH24:MI') AS CHANGED_AT, d.REASON
        FROM RISK_DELTA_LOG d
        JOIN MEMBER m ON d.MEMBER_ID = m.MEMBER_ID
        WHERE d.CHANGED_AT >= DATEADD(day, -1, CURRENT_TIMESTAMP())
        ORDER BY d.CHANGED_AT DESC
    """
    try:
        rows = await sql_client.execute(sql, caller_headers=user.caller_headers)
        return [
            {
                "member_id": r["MEMBER_ID"],
                "first_name": r.get("FIRST_NAME", ""),
                "last_name": r.get("LAST_NAME", ""),
                "old_risk": r.get("OLD_RISK", ""),
                "new_risk": r.get("NEW_RISK", ""),
                "changed_at": r.get("CHANGED_AT", ""),
                "reason": r.get("REASON", ""),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("")
async def search_members(
    q: str = Query("", description="Search term"),
    user: AuthenticatedUser = Depends(require_permission),
):
    if not q.strip():
        return []
    pattern = f"%{q.strip()}%"
    sql = """
        SELECT MEMBER_ID, FIRST_NAME, LAST_NAME, AGE, GENDER, PLAN_TYPE, RISK_FLAGS
        FROM MEMBER
        WHERE LOWER(FIRST_NAME) LIKE LOWER(?)
           OR LOWER(LAST_NAME) LIKE LOWER(?)
           OR UPPER(MEMBER_ID) LIKE UPPER(?)
        ORDER BY LAST_NAME, FIRST_NAME
        LIMIT 20
    """
    try:
        rows = await sql_client.execute(sql, caller_headers=user.caller_headers, bindings=_bind([pattern, pattern, pattern]))
        return [_member_row_to_summary(r) for r in rows]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/{member_id}")
async def get_member(
    member_id: str,
    user: AuthenticatedUser = Depends(require_permission),
):
    ch = user.caller_headers
    try:
        member_rows = await sql_client.execute(
            "SELECT MEMBER_ID, FIRST_NAME, LAST_NAME, TO_VARCHAR(DOB, 'YYYY-MM-DD') AS DOB, AGE, GENDER, PLAN_TYPE, TO_VARCHAR(ENROLLMENT_DATE, 'YYYY-MM-DD') AS ENROLLMENT_DATE, PCP_NAME, RISK_FLAGS "
            "FROM MEMBER WHERE MEMBER_ID = ?",
            caller_headers=ch,
            bindings=_bind([member_id]),
        )
        if not member_rows:
            raise HTTPException(status_code=404, detail="Member not found")
        m = member_rows[0]

        enc_rows, med_rows, dx_rows, lab_rows, note_rows, claim_rows, att_rows = await asyncio.gather(
            sql_client.execute(
                "SELECT ENCOUNTER_ID, TO_VARCHAR(ENCOUNTER_DATE, 'YYYY-MM-DD') AS ENCOUNTER_DATE, ENCOUNTER_TYPE, PROVIDER_NAME, FACILITY, PRIMARY_DIAGNOSIS_CODE "
                "FROM ENCOUNTER WHERE MEMBER_ID = ? ORDER BY ENCOUNTER_DATE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT MEDICATION_ID, DRUG_NAME, DOSAGE, FREQUENCY, STATUS, PRESCRIBER "
                "FROM MEDICATION WHERE MEMBER_ID = ? ORDER BY STATUS, DRUG_NAME",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT DIAGNOSIS_ID, ICD10_CODE, DESCRIPTION, TO_VARCHAR(DIAGNOSED_DATE, 'YYYY-MM-DD') AS DIAGNOSED_DATE, STATUS "
                "FROM DIAGNOSIS WHERE MEMBER_ID = ? ORDER BY DIAGNOSED_DATE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT LAB_ID, TEST_NAME, RESULT_VALUE, UNIT, REFERENCE_RANGE_LOW, REFERENCE_RANGE_HIGH, TO_VARCHAR(RESULT_DATE, 'YYYY-MM-DD') AS RESULT_DATE, ABNORMAL_FLAG "
                "FROM LAB_RESULT WHERE MEMBER_ID = ? ORDER BY RESULT_DATE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT NOTE_ID, NOTE_TYPE, TO_VARCHAR(NOTE_DATE, 'YYYY-MM-DD') AS NOTE_DATE, AUTHOR, CONTENT_TEXT "
                "FROM CLINICAL_NOTE WHERE MEMBER_ID = ? ORDER BY NOTE_DATE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT CLAIM_ID, TO_VARCHAR(DATE_OF_SERVICE, 'YYYY-MM-DD') AS DATE_OF_SERVICE, PROCEDURE_CODE, DIAGNOSIS_CODE, PROVIDER, AMOUNT_BILLED, AMOUNT_PAID, STATUS, DENIAL_REASON "
                "FROM CLAIM WHERE MEMBER_ID = ? ORDER BY DATE_OF_SERVICE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
            sql_client.execute(
                "SELECT ATTACHMENT_ID, FILE_NAME, FILE_TYPE, TO_VARCHAR(UPLOAD_DATE, 'YYYY-MM-DD') AS UPLOAD_DATE, RELATED_ENCOUNTER_ID, SHORT_NOTE, STORAGE_PATH "
                "FROM ATTACHMENT WHERE MEMBER_ID = ? ORDER BY UPLOAD_DATE DESC",
                caller_headers=ch, bindings=_bind([member_id]),
            ),
        )

        return {
            "member_id": m["MEMBER_ID"],
            "first_name": m["FIRST_NAME"],
            "last_name": m["LAST_NAME"],
            "age": int(m["AGE"]) if m.get("AGE") else None,
            "gender": m.get("GENDER"),
            "plan_type": m.get("PLAN_TYPE"),
            "dob": m.get("DOB", ""),
            "enrollment_date": m.get("ENROLLMENT_DATE"),
            "pcp_name": m.get("PCP_NAME", ""),
            "risk_flags": _parse_risk_flags(m.get("RISK_FLAGS")),
            "encounters": [
                {"encounter_id": r["ENCOUNTER_ID"], "encounter_date": r.get("ENCOUNTER_DATE", ""), "encounter_type": r.get("ENCOUNTER_TYPE", ""), "provider_name": r.get("PROVIDER_NAME", ""), "facility": r.get("FACILITY", ""), "primary_diagnosis_code": r.get("PRIMARY_DIAGNOSIS_CODE", "")}
                for r in enc_rows
            ],
            "medications": [
                {"medication_id": r["MEDICATION_ID"], "drug_name": r.get("DRUG_NAME", ""), "dosage": r.get("DOSAGE", ""), "frequency": r.get("FREQUENCY", ""), "status": r.get("STATUS", ""), "prescriber": r.get("PRESCRIBER", "")}
                for r in med_rows
            ],
            "diagnoses": [
                {"diagnosis_id": r["DIAGNOSIS_ID"], "icd10_code": r.get("ICD10_CODE", ""), "description": r.get("DESCRIPTION", ""), "diagnosed_date": r.get("DIAGNOSED_DATE", ""), "status": r.get("STATUS", "")}
                for r in dx_rows
            ],
            "labs": [
                {"lab_id": r["LAB_ID"], "test_name": r.get("TEST_NAME", ""), "result_value": float(r["RESULT_VALUE"]) if r.get("RESULT_VALUE") else None, "unit": r.get("UNIT", ""), "reference_range_low": float(r["REFERENCE_RANGE_LOW"]) if r.get("REFERENCE_RANGE_LOW") else None, "reference_range_high": float(r["REFERENCE_RANGE_HIGH"]) if r.get("REFERENCE_RANGE_HIGH") else None, "result_date": r.get("RESULT_DATE", ""), "abnormal_flag": r.get("ABNORMAL_FLAG", "false").lower() == "true" if isinstance(r.get("ABNORMAL_FLAG"), str) else bool(r.get("ABNORMAL_FLAG"))}
                for r in lab_rows
            ],
            "sources": [
                {"source_id": r["NOTE_ID"], "source_type": "clinical_note", "title": f"{r.get('NOTE_TYPE', 'Note')} — {r.get('NOTE_DATE', '')}", "author": r.get("AUTHOR", ""), "date": r.get("NOTE_DATE", ""), "preview": (r.get("CONTENT_TEXT") or "")[:200] + "..." if len(r.get("CONTENT_TEXT") or "") > 200 else r.get("CONTENT_TEXT", ""), "content": r.get("CONTENT_TEXT", "")}
                for r in note_rows
            ],
            "claims": [
                {"claim_id": r["CLAIM_ID"], "date_of_service": r.get("DATE_OF_SERVICE", ""), "procedure_code": r.get("PROCEDURE_CODE", ""), "diagnosis_code": r.get("DIAGNOSIS_CODE", ""), "provider": r.get("PROVIDER", ""), "amount_billed": float(r["AMOUNT_BILLED"]) if r.get("AMOUNT_BILLED") else 0, "amount_paid": float(r["AMOUNT_PAID"]) if r.get("AMOUNT_PAID") else 0, "status": r.get("STATUS", ""), "denial_reason": r.get("DENIAL_REASON")}
                for r in claim_rows
            ],
            "attachments": [
                {"attachment_id": r["ATTACHMENT_ID"], "file_name": r.get("FILE_NAME", ""), "file_type": r.get("FILE_TYPE", ""), "upload_date": r.get("UPLOAD_DATE", ""), "related_encounter_id": r.get("RELATED_ENCOUNTER_ID"), "short_note": r.get("SHORT_NOTE", ""), "storage_path": r.get("STORAGE_PATH", "")}
                for r in att_rows
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/{member_id}/risk-explanation")
async def risk_explanation(
    member_id: str,
    user: AuthenticatedUser = Depends(require_permission),
):
    ch = user.caller_headers
    b = _bind([member_id])
    try:
        delta_rows, lab_rows, med_rows, dx_rows = await asyncio.gather(
            sql_client.execute(
                "SELECT OLD_RISK, NEW_RISK, TO_VARCHAR(CHANGED_AT, 'YYYY-MM-DD') AS CHANGED_AT, REASON "
                "FROM RISK_DELTA_LOG WHERE MEMBER_ID = ? ORDER BY CHANGED_AT DESC LIMIT 1",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT TEST_NAME, RESULT_VALUE, UNIT "
                "FROM LAB_RESULT WHERE MEMBER_ID = ? AND ABNORMAL_FLAG = TRUE "
                "ORDER BY RESULT_DATE DESC LIMIT 10",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM MEDICATION "
                "WHERE MEMBER_ID = ? AND UPPER(STATUS) = 'ACTIVE'",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT DESCRIPTION FROM DIAGNOSIS "
                "WHERE MEMBER_ID = ? AND UPPER(STATUS) = 'ACTIVE'",
                caller_headers=ch, bindings=b,
            ),
        )

        delta = delta_rows[0] if delta_rows else {}
        current_risk = delta.get("NEW_RISK", "Unknown")
        previous_risk = delta.get("OLD_RISK", "Unknown")
        changed_at = delta.get("CHANGED_AT", "")

        contributing: list[str] = []
        med_count = int(med_rows[0]["CNT"]) if med_rows else 0
        if med_count >= 5:
            contributing.append(f"{med_count} active medications (polypharmacy threshold: 5)")

        for lab in lab_rows:
            name = lab.get("TEST_NAME", "")
            val = lab.get("RESULT_VALUE", "")
            unit = lab.get("UNIT", "")
            contributing.append(f"{name} {val} {unit} (abnormal)".strip())

        for dx in dx_rows:
            desc = dx.get("DESCRIPTION", "")
            if desc:
                contributing.append(f"{desc} diagnosis active")

        if delta.get("REASON"):
            contributing.append(delta["REASON"])

        risk_flags: list[str] = []
        if med_count >= 5:
            risk_flags.append("Polypharmacy")
        dx_text = " ".join(d.get("DESCRIPTION", "").lower() for d in dx_rows)
        for flag, keywords in [("CKD", ["ckd", "chronic kidney"]), ("Cardiac", ["cardiac", "heart", "chf"]), ("Diabetes", ["diabetes", "diabetic"]), ("COPD", ["copd", "pulmonary"])]:
            if any(kw in dx_text for kw in keywords):
                risk_flags.append(flag)

        return {
            "member_id": member_id,
            "current_risk": current_risk,
            "previous_risk": previous_risk,
            "changed_at": changed_at,
            "contributing_factors": contributing,
            "risk_flags": risk_flags,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/{member_id}/summary")
async def member_summary(
    member_id: str,
    user: AuthenticatedUser = Depends(require_permission),
):
    ch = user.caller_headers
    b = _bind([member_id])
    try:
        results = await asyncio.gather(
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM MEDICATION WHERE MEMBER_ID = ? AND UPPER(STATUS) = 'ACTIVE'",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM DIAGNOSIS WHERE MEMBER_ID = ? AND UPPER(STATUS) = 'ACTIVE'",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM LAB_RESULT WHERE MEMBER_ID = ? AND ABNORMAL_FLAG = TRUE",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM ENCOUNTER WHERE MEMBER_ID = ? AND ENCOUNTER_DATE >= DATEADD(day, -90, CURRENT_DATE())",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM CLAIM WHERE MEMBER_ID = ?",
                caller_headers=ch, bindings=b,
            ),
            sql_client.execute(
                "SELECT COUNT(*) AS CNT FROM DOCUMENT WHERE MEMBER_ID = ?",
                caller_headers=ch, bindings=b,
            ),
        )

        def _cnt(rows: list[dict]) -> int:
            return int(rows[0]["CNT"]) if rows else 0

        return {
            "active_medications": _cnt(results[0]),
            "active_diagnoses": _cnt(results[1]),
            "abnormal_labs": _cnt(results[2]),
            "recent_encounters": _cnt(results[3]),
            "total_claims": _cnt(results[4]),
            "total_documents": _cnt(results[5]),
            "compliance_gaps": 0,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc
