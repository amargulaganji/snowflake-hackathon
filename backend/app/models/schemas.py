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


class AskResponse(BaseModel):
    answer: str
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)
    risk_level: str | None = None
    contradiction_detected: bool = False
    contradiction_details: str | None = None
    insufficient_evidence: bool = False
