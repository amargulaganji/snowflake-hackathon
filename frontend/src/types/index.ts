export interface MemberSummary {
  member_id: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  plan_type: string;
  risk_flags: string[];
}

export interface Encounter {
  encounter_id: string;
  encounter_date: string;
  encounter_type: string;
  provider_name: string;
  facility: string;
  primary_diagnosis_code: string;
  notes_summary: string;
}

export interface Medication {
  medication_id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  status: string;
  prescriber: string;
}

export interface Diagnosis {
  diagnosis_id: string;
  icd10_code: string;
  description: string;
  diagnosed_date: string;
  status: string;
}

export interface LabResult {
  lab_id: string;
  test_name: string;
  result_value: number;
  unit: string;
  reference_range_low: number;
  reference_range_high: number;
  result_date: string;
  abnormal_flag: boolean;
}

export interface SourceDocument {
  source_id: string;
  source_type: string;
  title: string;
  author: string;
  date: string;
  preview: string;
  content: string;
}

export interface Claim {
  claim_id: string;
  date_of_service: string;
  procedure_code: string;
  diagnosis_code: string;
  provider: string;
  amount_billed: number;
  amount_paid: number;
  status: string;
  denial_reason: string | null;
}

export interface Attachment {
  attachment_id: string;
  file_name: string;
  file_type: string;
  upload_date: string;
  related_encounter_id: string | null;
  short_note: string;
  storage_path: string;
}

export interface MemberDetail extends MemberSummary {
  dob: string;
  enrollment_date: string;
  pcp_name: string;
  encounters: Encounter[];
  medications: Medication[];
  diagnoses: Diagnosis[];
  labs: LabResult[];
  sources: SourceDocument[];
  claims: Claim[];
  attachments: Attachment[];
}

export interface EvidenceItem {
  source_type: string;
  source_name: string;
  content: string;
  relevance: string;
}

export interface AskRequest {
  member_id: string;
  question: string;
  history?: { role: string; content: string }[];
}

export interface AskResponse {
  answer: string;
  evidence_chain: EvidenceItem[];
  citations: {
    index: number;
    source_type: string;
    source_name: string;
    source_id: string | null;
    content_preview: string;
    metadata: Record<string, string>;
  }[];
  risk_level: string | null;
  contradiction_detected: boolean;
  contradiction_details: string | null;
  insufficient_evidence: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: AskResponse;
  timestamp: Date;
}
