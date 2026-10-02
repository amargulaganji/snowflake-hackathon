import { useState } from 'react';
import type { MemberDetail } from '../types';

interface TimelineEvent {
  id: string;
  date: string;
  type: 'encounter' | 'medication' | 'diagnosis' | 'lab';
  title: string;
  subtitle: string;
}

interface ClinicalTimelineProps {
  detail: MemberDetail;
}

const TYPE_CONFIG = {
  encounter: { color: '#387ED1', label: 'Encounter' },
  medication: { color: '#6A1B9A', label: 'Medication' },
  diagnosis: { color: '#B26A00', label: 'Diagnosis' },
  lab: { color: '#C62828', label: 'Abnormal Lab' },
};

function buildEvents(detail: MemberDetail): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  (detail.encounters ?? []).forEach((e) => {
    if (e.encounter_date) events.push({ id: e.encounter_id, date: e.encounter_date, type: 'encounter', title: `${e.encounter_type} visit`, subtitle: `${e.provider_name} — ${e.facility}` });
  });
  (detail.medications ?? []).forEach((m) => {
    events.push({ id: m.medication_id, date: '', type: 'medication', title: `${m.drug_name} ${m.dosage}`, subtitle: `${m.status} — ${m.prescriber}` });
  });
  (detail.diagnoses ?? []).forEach((d) => {
    if (d.diagnosed_date) events.push({ id: d.diagnosis_id, date: d.diagnosed_date, type: 'diagnosis', title: `${d.icd10_code} — ${d.description}`, subtitle: d.status });
  });
  (detail.labs ?? []).filter((l) => l.abnormal_flag).forEach((l) => {
    if (l.result_date) events.push({ id: l.lab_id, date: l.result_date, type: 'lab', title: `${l.test_name}: ${l.result_value} ${l.unit}`, subtitle: `Range: ${l.reference_range_low}–${l.reference_range_high}` });
  });
  return events.filter((e) => e.date).sort((a, b) => a.date.localeCompare(b.date));
}

export function ClinicalTimeline({ detail }: ClinicalTimelineProps) {
  const allEvents = buildEvents(detail);
  const [filters, setFilters] = useState<Set<string>>(new Set(['encounter', 'medication', 'diagnosis', 'lab']));
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const events = allEvents.filter((e) => filters.has(e.type));

  if (allEvents.length === 0) return <div className="detail-empty">No timeline events available</div>;

  const dates = events.map((e) => new Date(e.date).getTime());
  const minDate = Math.min(...dates);
  const maxDate = Math.max(...dates);
  const range = maxDate - minDate || 1;

  const toggleFilter = (type: string) => {
    setFilters((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type); else next.add(type);
      return next;
    });
  };

  return (
    <div className="clinical-timeline">
      <div className="timeline-filters">
        {Object.entries(TYPE_CONFIG).map(([key, cfg]) => (
          <button
            key={key}
            className={`timeline-chip ${filters.has(key) ? 'timeline-chip-active' : ''}`}
            style={{ borderColor: cfg.color, color: filters.has(key) ? 'white' : cfg.color, background: filters.has(key) ? cfg.color : 'transparent' }}
            onClick={() => toggleFilter(key)}
          >
            {cfg.label}
          </button>
        ))}
      </div>
      <div className="timeline-scroll">
        <div className="timeline-track">
          <div className="timeline-line" />
          {events.map((evt) => {
            const pos = ((new Date(evt.date).getTime() - minDate) / range) * 100;
            const cfg = TYPE_CONFIG[evt.type];
            const isLab = evt.type === 'lab';
            return (
              <div
                key={evt.id}
                className="timeline-dot-wrapper"
                style={{ left: `${Math.max(2, Math.min(98, pos))}%` }}
                onMouseEnter={() => setHoveredId(evt.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <div
                  className={`timeline-dot ${isLab ? 'timeline-dot-large' : ''}`}
                  style={{ background: cfg.color }}
                />
                {hoveredId === evt.id && (
                  <div className="timeline-popover">
                    <div className="popover-date">{evt.date}</div>
                    <span className="popover-badge" style={{ background: cfg.color }}>{cfg.label}</span>
                    <div className="popover-title">{evt.title}</div>
                    <div className="popover-subtitle">{evt.subtitle}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {events.length > 0 && (
          <div className="timeline-axis">
            <span>{events[0]?.date}</span>
            <span>{events[events.length - 1]?.date}</span>
          </div>
        )}
      </div>
    </div>
  );
}
