from __future__ import annotations

import json
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
from app.services.sql_client import sql_client
from app.services.snowflake_client import agent_client

_WRITE_ROLES = ("SNOWCARE_ADMIN_ROLE", "CARE_MANAGER_ROLE")

router = APIRouter(
    prefix="/studio",
    tags=["studio"],
    dependencies=[Depends(require_role(*_WRITE_ROLES))],
)


async def _next_member_id() -> str:
    rows = await sql_client.execute(
        "SELECT MAX(CAST(REPLACE(MEMBER_ID, 'M', '') AS INT)) AS MAX_NUM FROM MEMBER WHERE MEMBER_ID LIKE 'M%'"
    )
    max_num = int(rows[0]["MAX_NUM"]) if rows and rows[0].get("MAX_NUM") else 0
    return f"M{max_num + 1}"


def _safe(val: str | None) -> str:
    if val is None:
        return "NULL"
    return f"'{val.replace(chr(39), chr(39)*2)}'"


def _safe_num(val: float | int | None) -> str:
    if val is None:
        return "NULL"
    return str(val)


async def _grant_member_access(member_id: str, username: str) -> None:
    safe_user = username.replace("'", "''").upper()
    safe_mid = member_id.replace("'", "''")
    try:
        await sql_client.execute(
            f"INSERT INTO USER_MEMBER_ACCESS (SNOWFLAKE_USER, MEMBER_ID, ACCESS_LEVEL) "
            f"SELECT '{safe_user}', '{safe_mid}', 'write' "
            f"WHERE NOT EXISTS (SELECT 1 FROM USER_MEMBER_ACCESS WHERE SNOWFLAKE_USER='{safe_user}' AND MEMBER_ID='{safe_mid}')"
        )
    except Exception:
        pass


@router.post("/members")
async def create_member(req: CreateMemberRequest, request: Request):
    try:
        member_id = await _next_member_id()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    risk_json = json.dumps(req.risk_flags) if req.risk_flags else "[]"
    safe_risk = risk_json.replace("'", "''")

    sql = f"""
        INSERT INTO MEMBER (MEMBER_ID, FIRST_NAME, LAST_NAME, DOB, AGE, GENDER, PLAN_TYPE, PCP_NAME, RISK_FLAGS, ENROLLMENT_DATE)
        SELECT
            '{member_id}',
            {_safe(req.first_name)},
            {_safe(req.last_name)},
            {_safe(req.dob)},
            {_safe_num(req.age)},
            {_safe(req.gender)},
            {_safe(req.plan_type)},
            {_safe(req.pcp_name)},
            PARSE_JSON('{safe_risk}'),
            CURRENT_DATE()
    """
    try:
        await sql_client.execute(sql)
        username = get_authenticated_user(request)
        await _grant_member_access(member_id, username)
        return {"member_id": member_id, "status": "created"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.put("/members/{member_id}")
async def update_member(member_id: str, req: CreateMemberRequest):
    safe_id = member_id.replace("'", "''")
    updates = []
    if req.first_name:
        updates.append(f"FIRST_NAME = {_safe(req.first_name)}")
    if req.last_name:
        updates.append(f"LAST_NAME = {_safe(req.last_name)}")
    if req.age is not None:
        updates.append(f"AGE = {_safe_num(req.age)}")
    if req.gender:
        updates.append(f"GENDER = {_safe(req.gender)}")
    if req.plan_type:
        updates.append(f"PLAN_TYPE = {_safe(req.plan_type)}")
    if req.pcp_name:
        updates.append(f"PCP_NAME = {_safe(req.pcp_name)}")
    if req.risk_flags:
        risk_json = json.dumps(req.risk_flags).replace("'", "''")
        updates.append(f"RISK_FLAGS = PARSE_JSON('{risk_json}')")
    if not updates:
        return {"member_id": member_id, "status": "no_changes"}
    sql = f"UPDATE MEMBER SET {', '.join(updates)} WHERE MEMBER_ID = '{safe_id}'"
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "updated"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/medications")
async def add_medication(member_id: str, req: CreateMedicationRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO MEDICATION (MEDICATION_ID, MEMBER_ID, DRUG_NAME, DOSAGE, FREQUENCY, STATUS, PRESCRIBER)
        VALUES (
            'MED-' || SEQ_MEDICATION.NEXTVAL,
            '{safe_id}',
            {_safe(req.drug_name)},
            {_safe(req.dosage)},
            {_safe(req.frequency)},
            {_safe(req.status or 'active')},
            {_safe(req.prescriber)}
        )
    """
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "medication_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/diagnoses")
async def add_diagnosis(member_id: str, req: CreateDiagnosisRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO DIAGNOSIS (DIAGNOSIS_ID, MEMBER_ID, ICD10_CODE, DESCRIPTION, DIAGNOSED_DATE, STATUS)
        VALUES (
            'DX-' || SEQ_DIAGNOSIS.NEXTVAL,
            '{safe_id}',
            {_safe(req.icd10_code)},
            {_safe(req.description)},
            {_safe(req.diagnosed_date)},
            {_safe(req.status or 'active')}
        )
    """
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "diagnosis_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/labs")
async def add_lab(member_id: str, req: CreateLabRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO LAB_RESULT (LAB_ID, MEMBER_ID, TEST_NAME, RESULT_VALUE, UNIT, REFERENCE_RANGE_LOW, REFERENCE_RANGE_HIGH, RESULT_DATE, ABNORMAL_FLAG)
        VALUES (
            'LAB-' || SEQ_LAB.NEXTVAL,
            '{safe_id}',
            {_safe(req.test_name)},
            {_safe_num(req.result_value)},
            {_safe(req.unit)},
            {_safe_num(req.reference_range_low)},
            {_safe_num(req.reference_range_high)},
            {_safe(req.result_date)},
            {str(req.abnormal_flag).upper() if req.abnormal_flag is not None else 'FALSE'}
        )
    """
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "lab_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/encounters")
async def add_encounter(member_id: str, req: CreateEncounterRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO ENCOUNTER (ENCOUNTER_ID, MEMBER_ID, ENCOUNTER_DATE, ENCOUNTER_TYPE, PROVIDER_NAME, FACILITY, PRIMARY_DIAGNOSIS_CODE)
        VALUES (
            'ENC-' || SEQ_ENCOUNTER.NEXTVAL,
            '{safe_id}',
            {_safe(req.encounter_date)},
            {_safe(req.encounter_type)},
            {_safe(req.provider_name)},
            {_safe(req.facility)},
            {_safe(req.primary_diagnosis_code)}
        )
    """
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "encounter_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/claims")
async def add_claim(member_id: str, req: CreateClaimRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO CLAIM (CLAIM_ID, MEMBER_ID, DATE_OF_SERVICE, PROCEDURE_CODE, DIAGNOSIS_CODE, PROVIDER, AMOUNT_BILLED, AMOUNT_PAID, STATUS, DENIAL_REASON)
        VALUES (
            'CLM-' || SEQ_CLAIM.NEXTVAL,
            '{safe_id}',
            {_safe(req.date_of_service)},
            {_safe(req.procedure_code)},
            {_safe(req.diagnosis_code)},
            {_safe(req.provider)},
            {_safe_num(req.amount_billed)},
            {_safe_num(req.amount_paid)},
            {_safe(req.status or 'submitted')},
            {_safe(req.denial_reason)}
        )
    """
    try:
        await sql_client.execute(sql)
        return {"member_id": member_id, "status": "claim_added"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.post("/members/{member_id}/notes")
async def add_note(member_id: str, req: CreateNoteRequest):
    safe_id = member_id.replace("'", "''")
    sql = f"""
        INSERT INTO CLINICAL_NOTE (NOTE_ID, MEMBER_ID, NOTE_TYPE, NOTE_DATE, AUTHOR, CONTENT_TEXT)
        VALUES (
            'NOTE-' || SEQ_NOTE.NEXTVAL,
            '{safe_id}',
            {_safe(req.note_type)},
            {_safe(req.note_date)},
            {_safe(req.author)},
            {_safe(req.content_text)}
        )
    """
    try:
        await sql_client.execute(sql)
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

    risk_json = json.dumps(data.get("risk_flags", [])).replace("'", "''")
    insert_member = f"""
        INSERT INTO MEMBER (MEMBER_ID, FIRST_NAME, LAST_NAME, AGE, GENDER, PLAN_TYPE, PCP_NAME, RISK_FLAGS, ENROLLMENT_DATE)
        VALUES (
            '{member_id}',
            {_safe(data.get('first_name'))},
            {_safe(data.get('last_name'))},
            {_safe_num(data.get('age'))},
            {_safe(data.get('gender'))},
            {_safe(data.get('plan_type'))},
            {_safe(data.get('pcp_name'))},
            PARSE_JSON('{risk_json}'),
            CURRENT_DATE()
        )
    """
    try:
        await sql_client.execute(insert_member)
        username = get_authenticated_user(request)
        await _grant_member_access(member_id, username)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error inserting member: {exc}") from exc

    records_inserted = {"member": member_id}

    for med in data.get("medications", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO MEDICATION (MEDICATION_ID, MEMBER_ID, DRUG_NAME, DOSAGE, FREQUENCY, STATUS, PRESCRIBER)
                VALUES ('MED-' || SEQ_MEDICATION.NEXTVAL, '{member_id}', {_safe(med.get('drug_name'))}, {_safe(med.get('dosage'))}, {_safe(med.get('frequency'))}, {_safe(med.get('status', 'active'))}, {_safe(med.get('prescriber'))})
            """)
        except Exception:
            pass
    records_inserted["medications"] = len(data.get("medications", []))

    for dx in data.get("diagnoses", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO DIAGNOSIS (DIAGNOSIS_ID, MEMBER_ID, ICD10_CODE, DESCRIPTION, DIAGNOSED_DATE, STATUS)
                VALUES ('DX-' || SEQ_DIAGNOSIS.NEXTVAL, '{member_id}', {_safe(dx.get('icd10_code'))}, {_safe(dx.get('description'))}, {_safe(dx.get('diagnosed_date'))}, {_safe(dx.get('status', 'active'))})
            """)
        except Exception:
            pass
    records_inserted["diagnoses"] = len(data.get("diagnoses", []))

    for lab in data.get("labs", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO LAB_RESULT (LAB_ID, MEMBER_ID, TEST_NAME, RESULT_VALUE, UNIT, REFERENCE_RANGE_LOW, REFERENCE_RANGE_HIGH, RESULT_DATE, ABNORMAL_FLAG)
                VALUES ('LAB-' || SEQ_LAB.NEXTVAL, '{member_id}', {_safe(lab.get('test_name'))}, {_safe_num(lab.get('result_value'))}, {_safe(lab.get('unit'))}, {_safe_num(lab.get('reference_range_low'))}, {_safe_num(lab.get('reference_range_high'))}, {_safe(lab.get('result_date'))}, {str(lab.get('abnormal_flag', False)).upper()})
            """)
        except Exception:
            pass
    records_inserted["labs"] = len(data.get("labs", []))

    for enc in data.get("encounters", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO ENCOUNTER (ENCOUNTER_ID, MEMBER_ID, ENCOUNTER_DATE, ENCOUNTER_TYPE, PROVIDER_NAME, FACILITY, PRIMARY_DIAGNOSIS_CODE)
                VALUES ('ENC-' || SEQ_ENCOUNTER.NEXTVAL, '{member_id}', {_safe(enc.get('encounter_date'))}, {_safe(enc.get('encounter_type'))}, {_safe(enc.get('provider_name'))}, {_safe(enc.get('facility'))}, {_safe(enc.get('primary_diagnosis_code'))})
            """)
        except Exception:
            pass
    records_inserted["encounters"] = len(data.get("encounters", []))

    for clm in data.get("claims", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO CLAIM (CLAIM_ID, MEMBER_ID, DATE_OF_SERVICE, PROCEDURE_CODE, DIAGNOSIS_CODE, PROVIDER, AMOUNT_BILLED, AMOUNT_PAID, STATUS, DENIAL_REASON)
                VALUES ('CLM-' || SEQ_CLAIM.NEXTVAL, '{member_id}', {_safe(clm.get('date_of_service'))}, {_safe(clm.get('procedure_code'))}, {_safe(clm.get('diagnosis_code'))}, {_safe(clm.get('provider'))}, {_safe_num(clm.get('amount_billed'))}, {_safe_num(clm.get('amount_paid'))}, {_safe(clm.get('status', 'submitted'))}, {_safe(clm.get('denial_reason'))})
            """)
        except Exception:
            pass
    records_inserted["claims"] = len(data.get("claims", []))

    for note in data.get("notes", []):
        try:
            await sql_client.execute(f"""
                INSERT INTO CLINICAL_NOTE (NOTE_ID, MEMBER_ID, NOTE_TYPE, NOTE_DATE, AUTHOR, CONTENT_TEXT)
                VALUES ('NOTE-' || SEQ_NOTE.NEXTVAL, '{member_id}', {_safe(note.get('note_type'))}, {_safe(note.get('note_date'))}, {_safe(note.get('author'))}, {_safe(note.get('content_text'))})
            """)
        except Exception:
            pass
    records_inserted["notes"] = len(data.get("notes", []))

    return {"status": "generated", "member_id": member_id, "records_inserted": records_inserted}
