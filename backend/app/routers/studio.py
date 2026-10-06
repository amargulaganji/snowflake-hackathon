from __future__ import annotations

import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.services.role_auth import require_role, AuthenticatedUser
from app.auth import get_authenticated_user

from app.models.schemas import (
    CreateMemberRequest,
    CreateMedicationRequest,
    CreateDiagnosisRequest,
    CreateLabRequest,
    CreateEncounterRequest,
    CreateClaimRequest,
    CreateNoteRequest,
    GenerateSyntheticRequest,
)
from app.services.sql_client import sql_client, _bind
from app.services.snowflake_client import agent_client

_WRITE_ROLES = ("PHYSICIAN_ROLE", "CARE_MANAGER_ROLE")

router = APIRouter(
    prefix="/studio",
    tags=["studio"],
    dependencies=[Depends(require_role(*_WRITE_ROLES))],
)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


async def _next_member_id() -> str:
    rows = await sql_client.execute(
        "SELECT MAX(CAST(REPLACE(MEMBER_ID, 'M', '') AS INT)) AS MAX_NUM FROM MEMBER WHERE MEMBER_ID LIKE 'M%'"
    )
    max_num = int(rows[0]["MAX_NUM"]) if rows and rows[0].get("MAX_NUM") else 0
    return f"M{max_num + 1}"


async def _grant_member_access(member_id: str, username: str) -> None:
    sql = """
        INSERT INTO USER_MEMBER_ACCESS (SNOWFLAKE_USER, MEMBER_ID, ACCESS_LEVEL)
        SELECT ?, ?, 'write'
        WHERE NOT EXISTS (
            SELECT 1 FROM USER_MEMBER_ACCESS WHERE SNOWFLAKE_USER = ? AND MEMBER_ID = ?
        )
    """
    uname = username.upper()
    try:
        await sql_client.execute(sql, bindings=_bind([uname, member_id, uname, member_id]))
    except Exception:
        pass


@router.post("/members")
async def create_member(req: CreateMemberRequest, request: Request):
    try:
        member_id = await _next_member_id()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    risk_json = json.dumps(req.risk_flags) if req.risk_flags else "[]"

    sql = """
        INSERT INTO MEMBER (MEMBER_ID, FIRST_NAME, LAST_NAME, DOB, AGE, GENDER, PLAN_TYPE, PCP_NAME, RISK_FLAGS, ENROLLMENT_DATE)
        SELECT ?, ?, ?, ?, ?, ?, ?, ?, PARSE_JSON(?), CURRENT_DATE()
    """
    params = [member_id, req.first_name, req.last_name, req.dob, req.age, req.gender, req.plan_type, req.pcp_name, risk_json]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        username = get_authenticated_user(request)
        await _grant_member_access(member_id, username)
        return {"member_id": member_id, "status": "created"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.put("/members/{member_id}")
async def update_member(member_id: str, req: CreateMemberRequest):
    updates = []
    params: list = []
    if req.first_name:
        updates.append("FIRST_NAME = ?")
        params.append(req.first_name)
    if req.last_name:
        updates.append("LAST_NAME = ?")
        params.append(req.last_name)
    if req.age is not None:
        updates.append("AGE = ?")
        params.append(req.age)
    if req.gender:
        updates.append("GENDER = ?")
        params.append(req.gender)
    if req.plan_type:
        updates.append("PLAN_TYPE = ?")
        params.append(req.plan_type)
    if req.pcp_name:
        updates.append("PCP_NAME = ?")
        params.append(req.pcp_name)
    if req.risk_flags:
        updates.append("RISK_FLAGS = PARSE_JSON(?)")
        params.append(json.dumps(req.risk_flags))
    if not updates:
        return {"member_id": member_id, "status": "no_changes"}
    params.append(member_id)
    sql = f"UPDATE MEMBER SET {', '.join(updates)} WHERE MEMBER_ID = ?"
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "updated"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/medications")
async def add_medication(member_id: str, req: CreateMedicationRequest):
    sql = """
        INSERT INTO MEDICATION (MEDICATION_ID, MEMBER_ID, DRUG_NAME, DOSAGE, FREQUENCY, STATUS, PRESCRIBER)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = [_uid("MED"), member_id, req.drug_name, req.dosage, req.frequency, req.status or "active", req.prescriber]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "medication_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/diagnoses")
async def add_diagnosis(member_id: str, req: CreateDiagnosisRequest):
    sql = """
        INSERT INTO DIAGNOSIS (DIAGNOSIS_ID, MEMBER_ID, ICD10_CODE, DESCRIPTION, DIAGNOSED_DATE, STATUS)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = [_uid("DX"), member_id, req.icd10_code, req.description, req.diagnosed_date, req.status or "active"]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "diagnosis_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/labs")
async def add_lab(member_id: str, req: CreateLabRequest):
    sql = """
        INSERT INTO LAB_RESULT (LAB_ID, MEMBER_ID, TEST_NAME, RESULT_VALUE, UNIT, REFERENCE_RANGE_LOW, REFERENCE_RANGE_HIGH, RESULT_DATE, ABNORMAL_FLAG)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = [_uid("LAB"), member_id, req.test_name, req.result_value, req.unit, req.reference_range_low, req.reference_range_high, req.result_date, req.abnormal_flag or False]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "lab_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/encounters")
async def add_encounter(member_id: str, req: CreateEncounterRequest):
    sql = """
        INSERT INTO ENCOUNTER (ENCOUNTER_ID, MEMBER_ID, ENCOUNTER_DATE, ENCOUNTER_TYPE, PROVIDER_NAME, FACILITY, PRIMARY_DIAGNOSIS_CODE)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = [_uid("ENC"), member_id, req.encounter_date, req.encounter_type, req.provider_name, req.facility, req.primary_diagnosis_code]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "encounter_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/claims")
async def add_claim(member_id: str, req: CreateClaimRequest):
    sql = """
        INSERT INTO CLAIM (CLAIM_ID, MEMBER_ID, DATE_OF_SERVICE, PROCEDURE_CODE, DIAGNOSIS_CODE, PROVIDER, AMOUNT_BILLED, AMOUNT_PAID, STATUS, DENIAL_REASON)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = [_uid("CLM"), member_id, req.date_of_service, req.procedure_code, req.diagnosis_code, req.provider, req.amount_billed, req.amount_paid, req.status or "submitted", req.denial_reason]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "claim_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/notes")
async def add_note(member_id: str, req: CreateNoteRequest):
    sql = """
        INSERT INTO CLINICAL_NOTE (NOTE_ID, MEMBER_ID, NOTE_TYPE, NOTE_DATE, AUTHOR, CONTENT_TEXT)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = [_uid("NOTE"), member_id, req.note_type, req.note_date, req.author, req.content_text]
    try:
        await sql_client.execute(sql, bindings=_bind(params))
        return {"member_id": member_id, "status": "note_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/generate")
async def generate_synthetic(req: GenerateSyntheticRequest, request: Request):
    prompt = (
        f"Generate a realistic synthetic healthcare member profile with the following parameters:\n"
        f"- Age range: {req.age_min} to {req.age_max}\n"
        f"- Conditions: {', '.join(req.conditions)}\n"
        f"- Complexity: {req.complexity}\n"
        f"- Include records for: {', '.join(req.includes)}\n\n"
        f"Return a JSON object with these fields:\n"
        f"- first_name, last_name, age, gender, plan_type, pcp_name, risk_flags (array)\n"
        f"- medications (array of {{drug_name, dosage, frequency, status, prescriber}})\n"
        f"- diagnoses (array of {{icd10_code, description, diagnosed_date, status}})\n"
        f"- labs (array of {{test_name, result_value, unit, reference_range_low, reference_range_high, result_date, abnormal_flag}})\n"
        f"- encounters (array of {{encounter_date, encounter_type, provider_name, facility, primary_diagnosis_code}})\n"
        f"- claims (array of {{date_of_service, procedure_code, diagnosis_code, provider, amount_billed, amount_paid, status}})\n"
        f"- notes (array of {{note_type, note_date, author, content_text}})\n\n"
        f"Only return valid JSON, no markdown."
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        raw = await agent_client.run_agent(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    text = ""
    for msg in raw.get("messages", []):
        content = msg.get("content", "")
        if isinstance(content, str):
            text += content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")

    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= 0:
        return {"status": "error", "detail": "Agent did not return valid JSON", "raw": text[:2000]}

    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        return {"status": "error", "detail": "Failed to parse agent JSON", "raw": text[start:end][:2000]}

    try:
        member_id = await _next_member_id()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    risk_json = json.dumps(data.get("risk_flags", []))
    insert_member = """
        INSERT INTO MEMBER (MEMBER_ID, FIRST_NAME, LAST_NAME, AGE, GENDER, PLAN_TYPE, PCP_NAME, RISK_FLAGS, ENROLLMENT_DATE)
        VALUES (?, ?, ?, ?, ?, ?, ?, PARSE_JSON(?), CURRENT_DATE())
    """
    try:
        await sql_client.execute(insert_member, bindings=_bind([
            member_id, data.get("first_name"), data.get("last_name"),
            data.get("age"), data.get("gender"), data.get("plan_type"),
            data.get("pcp_name"), risk_json,
        ]))
        username = get_authenticated_user(request)
        await _grant_member_access(member_id, username)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error inserting member: {exc}") from exc

    records_inserted = {"member": member_id}

    for med in data.get("medications", []):
        try:
            await sql_client.execute(
                "INSERT INTO MEDICATION (MEDICATION_ID, MEMBER_ID, DRUG_NAME, DOSAGE, FREQUENCY, STATUS, PRESCRIBER) VALUES (?, ?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("MED"), member_id, med.get("drug_name"), med.get("dosage"), med.get("frequency"), med.get("status", "active"), med.get("prescriber")]),
            )
        except Exception:
            pass
    records_inserted["medications"] = len(data.get("medications", []))

    for dx in data.get("diagnoses", []):
        try:
            await sql_client.execute(
                "INSERT INTO DIAGNOSIS (DIAGNOSIS_ID, MEMBER_ID, ICD10_CODE, DESCRIPTION, DIAGNOSED_DATE, STATUS) VALUES (?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("DX"), member_id, dx.get("icd10_code"), dx.get("description"), dx.get("diagnosed_date"), dx.get("status", "active")]),
            )
        except Exception:
            pass
    records_inserted["diagnoses"] = len(data.get("diagnoses", []))

    for lab in data.get("labs", []):
        try:
            await sql_client.execute(
                "INSERT INTO LAB_RESULT (LAB_ID, MEMBER_ID, TEST_NAME, RESULT_VALUE, UNIT, REFERENCE_RANGE_LOW, REFERENCE_RANGE_HIGH, RESULT_DATE, ABNORMAL_FLAG) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("LAB"), member_id, lab.get("test_name"), lab.get("result_value"), lab.get("unit"), lab.get("reference_range_low"), lab.get("reference_range_high"), lab.get("result_date"), lab.get("abnormal_flag", False)]),
            )
        except Exception:
            pass
    records_inserted["labs"] = len(data.get("labs", []))

    for enc in data.get("encounters", []):
        try:
            await sql_client.execute(
                "INSERT INTO ENCOUNTER (ENCOUNTER_ID, MEMBER_ID, ENCOUNTER_DATE, ENCOUNTER_TYPE, PROVIDER_NAME, FACILITY, PRIMARY_DIAGNOSIS_CODE) VALUES (?, ?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("ENC"), member_id, enc.get("encounter_date"), enc.get("encounter_type"), enc.get("provider_name"), enc.get("facility"), enc.get("primary_diagnosis_code")]),
            )
        except Exception:
            pass
    records_inserted["encounters"] = len(data.get("encounters", []))

    for clm in data.get("claims", []):
        try:
            await sql_client.execute(
                "INSERT INTO CLAIM (CLAIM_ID, MEMBER_ID, DATE_OF_SERVICE, PROCEDURE_CODE, DIAGNOSIS_CODE, PROVIDER, AMOUNT_BILLED, AMOUNT_PAID, STATUS, DENIAL_REASON) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("CLM"), member_id, clm.get("date_of_service"), clm.get("procedure_code"), clm.get("diagnosis_code"), clm.get("provider"), clm.get("amount_billed"), clm.get("amount_paid"), clm.get("status", "submitted"), clm.get("denial_reason")]),
            )
        except Exception:
            pass
    records_inserted["claims"] = len(data.get("claims", []))

    for note in data.get("notes", []):
        try:
            await sql_client.execute(
                "INSERT INTO CLINICAL_NOTE (NOTE_ID, MEMBER_ID, NOTE_TYPE, NOTE_DATE, AUTHOR, CONTENT_TEXT) VALUES (?, ?, ?, ?, ?, ?)",
                bindings=_bind([_uid("NOTE"), member_id, note.get("note_type"), note.get("note_date"), note.get("author"), note.get("content_text")]),
            )
        except Exception:
            pass
    records_inserted["notes"] = len(data.get("notes", []))

    return {"status": "generated", "member_id": member_id, "records_inserted": records_inserted}
