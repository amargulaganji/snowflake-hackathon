import { useState, useMemo } from 'react';
import { X } from 'lucide-react';
import type { MemberDetail } from '../types';

interface TimelineEvent {
  id: string;
  date: string;
  type: 'encounter' | 'medication' | 'diagnosis' | 'lab' | 'claim' | 'document';
  title: string;
  subtitle: string;
  detail: Record<string, string>;
}

interface ClinicalTimelineProps {
  detail: MemberDetail;
}

const LANE_CONFIG: Record<string, { color: string; label: string; symbol: string }> = {
  encounter: { color: '#387ED1', label: 'Encounter', symbol: '●' },
  diagnosis: { color: '#B26A00', label: 'Diagnosis', symbol: '◆' },
  medication: { color: '#6A1B9A', label: 'Medication', symbol: '■' },
  lab: { color: '#C62828', label: 'Abnormal Lab', symbol: '▲' },
  claim: { color: '#00695C', label: 'Claim', symbol: '●' },
  document: { color: '#37474F', label: 'Document', symbol: '📄' },
};

const LANE_ORDER = ['encounter', 'diagnosis', 'medication', 'lab', 'claim', 'document'];
const TIME_RANGES = [
  { label: '1Y', months: 12 },
  { label: '3Y', months: 36 },
  { label: '5Y', months: 60 },
  { label: 'All', months: 0 },
];

function buildEvents(detail: MemberDetail): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  (detail.encounters ?? []).forEach((e) => {
    if (e.encounter_date) events.push({
      id: `enc-${e.encounter_id}`, date: e.encounter_date, type: 'encounter',
      title: `${e.encounter_type || 'Visit'}`, subtitle: e.provider_name || '',
      detail: { Type: e.encounter_type || '', Provider: e.provider_name || '', Facility: e.facility || '', 'Dx Code': e.primary_diagnosis_code || '', Date: e.encounter_date },
    });
  });
  (detail.diagnoses ?? []).forEach((d) => {
    if (d.diagnosed_date) events.push({
      id: `dx-${d.diagnosis_id}`, date: d.diagnosed_date, type: 'diagnosis',
      title: `${d.icd10_code || ''} ${d.description || ''}`, subtitle: d.status || '',
      detail: { 'ICD-10': d.icd10_code || '', Description: d.description || '', Status: d.status || '', Date: d.diagnosed_date },
    });
  });
  (detail.labs ?? []).filter((l) => l.abnormal_flag).forEach((l) => {
    if (l.result_date) events.push({
      id: `lab-${l.lab_id}`, date: l.result_date, type: 'lab',
      title: `${l.test_name}: ${l.result_value} ${l.unit || ''}`, subtitle: `Range: ${l.reference_range_low ?? ''}–${l.reference_range_high ?? ''}`,
      detail: { Test: l.test_name || '', Value: `${l.result_value} ${l.unit || ''}`, Range: `${l.reference_range_low ?? ''}–${l.reference_range_high ?? ''}`, Date: l.result_date },
    });
  });
  (detail.claims ?? []).forEach((c) => {
    if (c.date_of_service) events.push({
      id: `clm-${c.claim_id}`, date: c.date_of_service, type: 'claim',
      title: `${c.procedure_code || 'Claim'} — ${c.status}`, subtitle: `$${c.amount_billed} billed`,
      detail: { Procedure: c.procedure_code || '', Status: c.status || '', Billed: `$${c.amount_billed}`, Paid: `$${c.amount_paid}`, Date: c.date_of_service },
    });
  });
  (detail.sources ?? []).forEach((s) => {
    if (s.date) events.push({
      id: `doc-${s.source_id}`, date: s.date, type: 'document',
      title: s.title || 'Document', subtitle: s.author || '',
      detail: { Title: s.title || '', Author: s.author || '', Date: s.date, Type: s.source_type || '' },
    });
  });
  return events.filter((e) => e.date).sort((a, b) => a.date.localeCompare(b.date));
}

export function ClinicalTimeline({ detail }: ClinicalTimelineProps) {
  const allEvents = useMemo(() => buildEvents(detail), [detail]);
  const [enabledLanes, setEnabledLanes] = useState<Set<string>>(new Set(LANE_ORDER));
  const [timeRange, setTimeRange] = useState('All');
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [zoom, setZoom] = useState(1);

  const now = new Date();
  const filteredByTime = useMemo(() => {
    const r = TIME_RANGES.find((t) => t.label === timeRange);
    if (!r || r.months === 0) return allEvents;
    const cutoff = new Date(now.getFullYear(), now.getMonth() - r.months, now.getDate());
    return allEvents.filter((e) => new Date(e.date) >= cutoff);
  }, [allEvents, timeRange]);

  const events = useMemo(() => filteredByTime.filter((e) => enabledLanes.has(e.type)), [filteredByTime, enabledLanes]);

  if (allEvents.length === 0) return <div className="page-empty"><p>No timeline events available</p></div>;

  const dates = events.map((e) => new Date(e.date).getTime());
  const minDate = dates.length > 0 ? Math.min(...dates) : Date.now();
  const maxDate = dates.length > 0 ? Math.max(...dates) : Date.now();
  const dateRange = maxDate - minDate || 86400000;
  const canvasWidth = Math.max(1600, 800 * zoom);

  const toggleLane = (type: string) => {
    setEnabledLanes((prev) => { const n = new Set(prev); if (n.has(type)) n.delete(type); else n.add(type); return n; });
  };

  const yearMarkers = useMemo(() => {
    const markers: { year: number; pos: number }[] = [];
    const startY = new Date(minDate).getFullYear();
    const endY = new Date(maxDate).getFullYear();
    for (let y = startY; y <= endY; y++) {
      const t = new Date(y, 0, 1).getTime();
      if (t >= minDate && t <= maxDate) markers.push({ year: y, pos: ((t - minDate) / dateRange) * 100 });
    }
    return markers;
  }, [minDate, maxDate, dateRange]);

  return (
    <div className="timeline-v2">
      <div className="timeline-toolbar">
        <div className="timeline-filters-v2">
          {LANE_ORDER.map((type) => {
            const cfg = LANE_CONFIG[type];
            const active = enabledLanes.has(type);
            const count = filteredByTime.filter((e) => e.type === type).length;
            return (
              <button key={type} className={`timeline-chip-v2 ${active ? 'timeline-chip-v2-active' : ''}`}
                style={{ borderColor: cfg.color, color: active ? 'white' : cfg.color, background: active ? cfg.color : 'transparent' }}
                onClick={() => toggleLane(type)}>
                {cfg.label} ({count})
              </button>
            );
          })}
        </div>
        <div className="timeline-range-btns">
          {TIME_RANGES.map((r) => (
            <button key={r.label} className={`filter-chip ${timeRange === r.label ? 'filter-chip-active' : ''}`} onClick={() => setTimeRange(r.label)}>{r.label}</button>
          ))}
          <div className="zoom-controls">
            <button className="zoom-btn" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>−</button>
            <span className="zoom-label">{Math.round(zoom * 100)}%</span>
            <button className="zoom-btn" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>+</button>
          </div>
        </div>
      </div>

      <div className="timeline-viewport">
        <div className="timeline-canvas" style={{ width: canvasWidth }}>
          <div className="timeline-year-axis">
            {yearMarkers.map((m) => (
              <div key={m.year} className="year-marker" style={{ left: `${m.pos}%` }}>
                <div className="year-line" />
                <span className="year-label">{m.year}</span>
              </div>
            ))}
          </div>

          {LANE_ORDER.filter((type) => enabledLanes.has(type)).map((type) => {
            const cfg = LANE_CONFIG[type];
            const laneEvents = events.filter((e) => e.type === type);
            return (
              <div key={type} className="timeline-lane">
                <div className="lane-label" style={{ color: cfg.color }}>{cfg.label}</div>
                <div className="lane-track">
                  {laneEvents.map((evt) => {
                    const pos = ((new Date(evt.date).getTime() - minDate) / dateRange) * 100;
                    return (
                      <button key={evt.id} className={`lane-event ${selectedEvent?.id === evt.id ? 'lane-event-selected' : ''}`}
                        style={{ left: `${Math.max(1, Math.min(99, pos))}%`, background: cfg.color }}
                        onClick={() => setSelectedEvent(selectedEvent?.id === evt.id ? null : evt)}
                        title={`${evt.title} (${evt.date})`}>
                        <span className="lane-event-dot" />
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {events.length > 0 && (
            <div className="timeline-date-axis">
              <span>{events[0]?.date}</span><span>{events[events.length - 1]?.date}</span>
            </div>
          )}
        </div>
      </div>

      {selectedEvent && (
        <div className="event-drawer">
          <div className="drawer-header">
            <div>
              <span className="drawer-type-badge" style={{ background: LANE_CONFIG[selectedEvent.type]?.color }}>{LANE_CONFIG[selectedEvent.type]?.label}</span>
              <h4>{selectedEvent.title}</h4>
              <p className="drawer-date">{selectedEvent.date}</p>
            </div>
            <button className="drawer-close" onClick={() => setSelectedEvent(null)}><X size={16} /></button>
          </div>
          <div className="drawer-body">
            {Object.entries(selectedEvent.detail).filter(([, v]) => v).map(([key, val]) => (
              <div key={key} className="drawer-field"><span className="drawer-key">{key}</span><span className="drawer-val">{val}</span></div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
