import type { Medication, MemberSummary } from '../types';

interface MedicationTimelineProps {
  medications: Medication[];
  member: MemberSummary;
}

const STATUS_COLORS: Record<string, string> = {
  active: '#387ED1',
  discontinued: '#9E9E9E',
  'on-hold': '#B26A00',
};

export function MedicationTimeline({ medications }: MedicationTimelineProps) {
  if (!medications || medications.length === 0) {
    return <div className="detail-empty">No medication data available for timeline</div>;
  }

  const activeMeds = medications.filter((m) => (m.status || '').toLowerCase() === 'active');
  const otherMeds = medications.filter((m) => (m.status || '').toLowerCase() !== 'active');
  const sorted = [...activeMeds, ...otherMeds];

  return (
    <div className="med-timeline">
      <div className="timeline-legend">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#387ED1' }}></span> Active</span>
        <span className="legend-item"><span className="legend-dot" style={{ background: '#9E9E9E' }}></span> Discontinued</span>
        <span className="legend-item"><span className="legend-dot" style={{ background: '#B26A00' }}></span> On-hold</span>
      </div>
      <div className="timeline-list">
        {sorted.map((med, i) => {
          const status = (med.status || 'active').toLowerCase();
          const color = STATUS_COLORS[status] || '#387ED1';
          return (
            <div key={med.medication_id || i} className="timeline-row">
              <div className="timeline-drug">
                <span className="timeline-drug-name">{med.drug_name || '—'}</span>
                <span className="timeline-drug-detail">{med.dosage || ''} · {med.frequency || ''}</span>
              </div>
              <div className="timeline-bar-container">
                <div
                  className="timeline-bar"
                  style={{
                    background: color,
                    width: status === 'active' ? '100%' : status === 'on-hold' ? '70%' : '40%',
                  }}
                >
                  <span className="timeline-bar-label">{med.status || ''}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
