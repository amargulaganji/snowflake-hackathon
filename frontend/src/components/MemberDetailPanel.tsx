import { useState } from 'react';
import type { MemberDetail, SourceDocument } from '../types';
import { ClinicalTimeline } from './ClinicalTimeline';
import { InsuranceTab } from './InsuranceTab';
import { AttachmentsTab } from './AttachmentsTab';

interface MemberDetailPanelProps {
  detail: MemberDetail;
  activeTab: string;
}

export function MemberDetailPanel({ detail, activeTab }: MemberDetailPanelProps) {
  const medications = detail.medications ?? [];
  const encounters = detail.encounters ?? [];
  const diagnoses = detail.diagnoses ?? [];
  const labs = detail.labs ?? [];
  const sources = detail.sources ?? [];
  const claims = detail.claims ?? [];
  const attachments = detail.attachments ?? [];

  const activeMeds = medications.filter((m) => (m.status || '').toLowerCase() === 'active');
  const pastMeds = medications.filter((m) => (m.status || '').toLowerCase() !== 'active');

  return (
    <div className="detail-fullwidth">
      {activeTab === 'medications' && <MedicationsSplit active={activeMeds} past={pastMeds} />}
      {activeTab === 'timeline' && <ClinicalTimeline detail={detail} />}
      {activeTab === 'encounters' && <EncountersTable items={encounters} />}
      {activeTab === 'diagnoses' && <DiagnosesTable items={diagnoses} />}
      {activeTab === 'labs' && <LabsTable items={labs} />}
      {activeTab === 'sources' && <SourcesPanel items={sources} />}
      {activeTab === 'insurance' && <InsuranceTab claims={claims} />}
      {activeTab === 'attachments' && <AttachmentsTab attachments={attachments} />}
    </div>
  );
}

function MedicationsSplit({ active, past }: { active: MemberDetail['medications']; past: MemberDetail['medications'] }) {
  return (
    <div>
      <div className="med-section-header">Current ({active.length})</div>
      {active.length === 0 ? <div className="detail-empty">No active medications</div> : <MedTable items={active} />}
      {past.length > 0 && (
        <>
          <div className="med-section-header med-section-past">Past ({past.length})</div>
          <MedTable items={past} />
        </>
      )}
    </div>
  );
}

function MedTable({ items }: { items: MemberDetail['medications'] }) {
  return (
    <table className="detail-table">
      <thead><tr><th>Drug</th><th>Dosage</th><th>Frequency</th><th>Status</th><th>Prescriber</th></tr></thead>
      <tbody>
        {items.map((m, i) => (
          <tr key={m.medication_id || i}>
            <td className="td-primary">{m.drug_name || '—'}</td>
            <td>{m.dosage || '—'}</td>
            <td>{m.frequency || '—'}</td>
            <td><span className={`status-pill status-${(m.status || '').toLowerCase()}`}>{m.status || '—'}</span></td>
            <td>{m.prescriber || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EncountersTable({ items }: { items: MemberDetail['encounters'] }) {
  if (!items || items.length === 0) return <div className="detail-empty">No encounters found</div>;
  return (
    <table className="detail-table">
      <thead><tr><th>Date</th><th>Type</th><th>Provider</th><th>Facility</th><th>Diagnosis Code</th></tr></thead>
      <tbody>
        {items.map((e, i) => (
          <tr key={e.encounter_id || i}>
            <td>{e.encounter_date || '—'}</td>
            <td><span className={`type-badge type-${(e.encounter_type || '').toLowerCase()}`}>{e.encounter_type || '—'}</span></td>
            <td>{e.provider_name || '—'}</td>
            <td>{e.facility || '—'}</td>
            <td className="td-code">{e.primary_diagnosis_code || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DiagnosesTable({ items }: { items: MemberDetail['diagnoses'] }) {
  if (!items || items.length === 0) return <div className="detail-empty">No diagnoses found</div>;
  return (
    <table className="detail-table">
      <thead><tr><th>ICD-10</th><th>Description</th><th>Diagnosed Date</th><th>Status</th></tr></thead>
      <tbody>
        {items.map((d, i) => (
          <tr key={d.diagnosis_id || i}>
            <td className="td-code">{d.icd10_code || '—'}</td>
            <td className="td-primary">{d.description || '—'}</td>
            <td>{d.diagnosed_date || '—'}</td>
            <td><span className={`status-pill status-${(d.status || '').toLowerCase()}`}>{d.status || '—'}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function LabsTable({ items }: { items: MemberDetail['labs'] }) {
  if (!items || items.length === 0) return <div className="detail-empty">No lab results found</div>;
  return (
    <table className="detail-table">
      <thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Reference Range</th><th>Date</th><th>Flag</th></tr></thead>
      <tbody>
        {items.map((l, i) => (
          <tr key={l.lab_id || i} className={l.abnormal_flag ? 'row-abnormal' : ''}>
            <td className="td-primary">{l.test_name || '—'}</td>
            <td className="td-value">{l.result_value ?? '—'}</td>
            <td>{l.unit || '—'}</td>
            <td className="td-range">{l.reference_range_low != null && l.reference_range_high != null ? `${l.reference_range_low}–${l.reference_range_high}` : '—'}</td>
            <td>{l.result_date || '—'}</td>
            <td>{l.abnormal_flag ? <span className="flag-abnormal">ABNORMAL</span> : <span className="flag-normal">Normal</span>}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SourcesPanel({ items }: { items: SourceDocument[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  if (!items || items.length === 0) return <div className="detail-empty">No source documents found</div>;
  return (
    <div className="sources-list">
      {items.map((src) => (
        <div key={src.source_id} className="source-card">
          <div className="source-header" onClick={() => setExpanded(expanded === src.source_id ? null : src.source_id)}>
            <div className="source-icon">{src.source_type === 'clinical_note' ? '\u{1F4CB}' : '\u{1F4C4}'}</div>
            <div className="source-info">
              <div className="source-title">{src.title}</div>
              <div className="source-meta">{src.author} · {src.date}</div>
            </div>
            <span className="evidence-chevron">{expanded === src.source_id ? '\u25BC' : '\u25B6'}</span>
          </div>
          {expanded === src.source_id && <div className="source-content">{src.content}</div>}
        </div>
      ))}
    </div>
  );
}
