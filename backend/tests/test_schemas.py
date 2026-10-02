"""Tests for the Pydantic schema models."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SNOWFLAKE_ACCOUNT_URL", "https://test.snowflakecomputing.com")
os.environ.setdefault("SNOWFLAKE_PAT", "test-token")

from app.models.schemas import (
    MemberSummary,
    MemberDetail,
    AskRequest,
    AskResponse,
    EvidenceItem,
    EncounterSummary,
    MedicationSummary,
    DiagnosisSummary,
    LabResultSummary,
)


def test_member_summary_defaults():
    m = MemberSummary(id="M001", first_name="John", last_name="Doe")
    assert m.id == "M001"
    assert m.age is None
    assert m.gender is None
    assert m.plan_type is None
    assert m.risk_flags == []


def test_member_summary_full():
    m = MemberSummary(
        id="M001",
        first_name="Jane",
        last_name="Smith",
        age=72,
        gender="Female",
        plan_type="HMO",
        risk_flags=["polypharmacy", "fall_risk"],
    )
    assert m.age == 72
    assert len(m.risk_flags) == 2


def test_member_detail_extends_summary():
    m = MemberDetail(id="M002", first_name="A", last_name="B")
    assert m.encounters == []
    assert m.medications == []
    assert m.diagnoses == []
    assert m.labs == []


def test_ask_request():
    req = AskRequest(member_id="M001", question="What medications?")
    assert req.member_id == "M001"


def test_ask_response_defaults():
    resp = AskResponse(answer="Test answer")
    assert resp.evidence_chain == []
    assert resp.risk_level is None
    assert resp.contradiction_detected is False
    assert resp.contradiction_details is None
    assert resp.insufficient_evidence is False


def test_evidence_item():
    e = EvidenceItem(
        source_type="structured",
        source_name="analyst",
        content="data here",
        relevance="high",
    )
    assert e.source_type == "structured"


def test_encounter_summary():
    e = EncounterSummary(encounter_id="E001")
    assert e.encounter_date is None


def test_medication_summary():
    m = MedicationSummary(medication_id="MED001", drug_name="Metformin")
    assert m.status is None


def test_diagnosis_summary():
    d = DiagnosisSummary(diagnosis_id="D001")
    assert d.icd10_code is None


def test_lab_result_summary():
    lr = LabResultSummary(lab_id="L001")
    assert lr.abnormal_flag is None
