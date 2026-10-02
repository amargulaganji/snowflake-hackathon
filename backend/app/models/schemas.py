from __future__ import annotations

from pydantic import BaseModel, Field


class MemberSummary(BaseModel):
    id: str
    first_name: str
    last_name: str
    age: int | None = None
    gender: str | None = None
    plan_type: str | None = None
    risk_flags: list[str] = Field(default_factory=list)


class EncounterSummary(BaseModel):
    encounter_id: str
    encounter_date: str | None = None
    encounter_type: str | None = None
    provider_name: str | None = None
    facility: str | None = None
    primary_diagnosis_code: str | None = None


class MedicationSummary(BaseModel):
    medication_id: str
    drug_name: str
    dosage: str | None = None
    frequency: str | None = None
    status: str | None = None


class DiagnosisSummary(BaseModel):
    diagnosis_id: str
    icd10_code: str | None = None
    description: str | None = None
    status: str | None = None


class LabResultSummary(BaseModel):
    lab_id: str
    test_name: str | None = None
    result_value: float | None = None
    unit: str | None = None
    abnormal_flag: bool | None = None


class MemberDetail(MemberSummary):
    encounters: list[EncounterSummary] = Field(default_factory=list)
    medications: list[MedicationSummary] = Field(default_factory=list)
    diagnoses: list[DiagnosisSummary] = Field(default_factory=list)
    labs: list[LabResultSummary] = Field(default_factory=list)


class ChatMessageInput(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    member_id: str
    question: str
    history: list[ChatMessageInput] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    source_type: str
    source_name: str
    content: str
    relevance: str | None = None


class Citation(BaseModel):
    index: int
    source_type: str  # structured, document, policy, guideline, udf
    source_name: str
    source_id: str | None = None
    content_preview: str
    metadata: dict = Field(default_factory=dict)  # date, version, section, etc.


class AskResponse(BaseModel):
    answer: str
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    risk_level: str | None = None
    contradiction_detected: bool = False
    contradiction_details: str | None = None
    insufficient_evidence: bool = False


# --- Studio / Member creation ---

class CreateMemberRequest(BaseModel):
    first_name: str
    last_name: str
    dob: str | None = None
    age: int | None = None
    gender: str | None = None
    plan_type: str | None = None
    pcp_name: str | None = None
    risk_flags: list[str] = Field(default_factory=list)


class CreateMedicationRequest(BaseModel):
    drug_name: str
    dosage: str | None = None
    frequency: str | None = None
    status: str | None = None
    prescriber: str | None = None


class CreateDiagnosisRequest(BaseModel):
    icd10_code: str
    description: str | None = None
    diagnosed_date: str | None = None
    status: str | None = None


class CreateLabRequest(BaseModel):
    test_name: str
    result_value: float | None = None
    unit: str | None = None
    reference_range_low: float | None = None
    reference_range_high: float | None = None
    result_date: str | None = None
    abnormal_flag: bool | None = None


class CreateEncounterRequest(BaseModel):
    encounter_date: str | None = None
    encounter_type: str | None = None
    provider_name: str | None = None
    facility: str | None = None
    primary_diagnosis_code: str | None = None


class CreateClaimRequest(BaseModel):
    date_of_service: str | None = None
    procedure_code: str | None = None
    diagnosis_code: str | None = None
    provider: str | None = None
    amount_billed: float | None = None
    amount_paid: float | None = None
    status: str | None = None
    denial_reason: str | None = None


class CreateNoteRequest(BaseModel):
    note_type: str | None = None
    note_date: str | None = None
    author: str | None = None
    content_text: str


class GenerateSyntheticRequest(BaseModel):
    age_min: int = 18
    age_max: int = 85
    conditions: list[str] = Field(default_factory=list)
    complexity: str = "medium"
    includes: list[str] = Field(default_factory=lambda: ["medications", "diagnoses", "labs"])


# --- Documents ---

class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    category: str
    member_id: str | None = None
    chunk_count: int
    processing_status: str


class DocumentDetail(BaseModel):
    document_id: str
    file_name: str
    category: str
    member_id: str | None = None
    content_text: str
    processing_status: str
    uploaded_at: str
    chunks: list[dict] = Field(default_factory=list)


# --- Admin ---

class AuditEntry(BaseModel):
    audit_id: str
    user_id: str
    user_role: str
    member_id: str | None = None
    action: str
    question: str
    tools_invoked: str | None = None
    sources_used: str | None = None
    risk_level: str | None = None
    contradiction_detected: bool = False
    insufficient_evidence: bool = False
    response_preview: str | None = None
    latency_ms: int | None = None
    created_at: str


class UserInfo(BaseModel):
    user_id: str
    user_name: str
    user_role: str
    email: str | None = None


class SwitchRoleRequest(BaseModel):
    role: str
