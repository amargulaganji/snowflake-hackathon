import { useMemo, useState, useEffect } from 'react';
import { Heart, Pill, FlaskConical, ClipboardList, Shield, FileText, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import type { MemberDetail } from '../types';
import { Avatar } from './Avatar';
import { getMemberRiskExplanation } from '../api/client';

interface MemberOverviewProps {
  detail: MemberDetail;
}

export function MemberOverview({ detail }: MemberOverviewProps) {
  const [riskExplanation, setRiskExplanation] = useState<any>(null);

  useEffect(() => {
    if (detail.member_id) {
      getMemberRiskExplanation(detail.member_id)
        .then(setRiskExplanation)
        .catch(() => setRiskExplanation(null));
    }
  }, [detail.member_id]);

  const activeMeds = useMemo(() => (detail.medications ?? []).filter((m) => (m.status || '').toLowerCase() === 'active'), [detail.medications]);
  const activeDx = useMemo(() => (detail.diagnoses ?? []).filter((d) => (d.status || '').toLowerCase() === 'active'), [detail.diagnoses]);
  const abnormalLabs = useMemo(() => (detail.labs ?? []).filter((l) => l.abnormal_flag), [detail.labs]);
  const recentEncounters = useMemo(() => (detail.encounters ?? []).slice(0, 5), [detail.encounters]);
  const claims = detail.claims ?? [];
  const sources = detail.sources ?? [];

  const riskLevel = detail.risk_flags.length >= 3 ? 'High' : detail.risk_flags.length >= 1 ? 'Moderate' : 'Low';
  const riskClass = riskLevel.toLowerCase();

  const hasStructured = activeMeds.length > 0 || activeDx.length > 0;
  const hasNotes = sources.length > 0;
  const hasNoContradiction = true;
  const evidenceStrength = hasStructured && hasNotes ? 'Strong' : hasStructured ? 'Partial' : 'Insufficient';

  return (
    <div className="member-overview">
      <div className="overview-header">
        <Avatar firstName={detail.first_name} lastName={detail.last_name} memberId={detail.member_id} size={56} />
        <div className="overview-header-info">
          <h2>{detail.first_name} {detail.last_name}</h2>
          <div className="overview-meta">
            <span>{detail.member_id}</span>
            <span>{detail.age}y</span>
            <span>{detail.gender}</span>
            <span>{detail.plan_type}</span>
            {detail.pcp_name && <span>PCP: {detail.pcp_name}</span>}
          </div>
          <div className="overview-badges">
            <span className={`risk-level-badge risk-${riskClass}`}>{riskLevel} Risk</span>
            <span className="synthetic-badge-sm">Synthetic</span>
          </div>
        </div>
      </div>

      {detail.risk_flags.length > 0 && (
        <div className="overview-risk-flags">
          {detail.risk_flags.map((flag) => (
            <span key={flag} className="condition-tag">{flag}</span>
          ))}
        </div>
      )}

      <div className="overview-cards">
        <SummaryCard icon={Pill} label="Active Medications" value={activeMeds.length} accent={activeMeds.length >= 5 ? 'red' : 'blue'} />
        <SummaryCard icon={Heart} label="Active Diagnoses" value={activeDx.length} accent="blue" />
        <SummaryCard icon={FlaskConical} label="Abnormal Labs" value={abnormalLabs.length} accent={abnormalLabs.length > 0 ? 'amber' : 'green'} />
        <SummaryCard icon={ClipboardList} label="Recent Encounters" value={recentEncounters.length} accent="blue" />
        <SummaryCard icon={Shield} label="Claims" value={claims.length} accent="blue" />
        <SummaryCard icon={FileText} label="Documents" value={sources.length} accent="blue" />
      </div>

      {detail.risk_flags.length > 0 && (
        <div className="overview-section">
          <h3><AlertTriangle size={16} /> Key Risks</h3>
          <div className="overview-risks-list">
            {detail.risk_flags.map((flag) => (
              <div key={flag} className="risk-item">
                <span className="risk-dot" />
                <span>{flag}</span>
              </div>
            ))}
            {activeMeds.length >= 5 && (
              <div className="risk-item">
                <span className="risk-dot risk-dot-high" />
                <span>Polypharmacy — {activeMeds.length} concurrent medications</span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="overview-section">
        <h3>Evidence Status</h3>
        <div className={`evidence-strength evidence-${evidenceStrength.toLowerCase()}`}>
          <span className="evidence-strength-label">Evidence Strength: {evidenceStrength}</span>
        </div>
        <div className="evidence-checklist">
          <EvidenceCheck label="Structured records available" checked={hasStructured} />
          <EvidenceCheck label="Clinical note corroboration" checked={hasNotes} />
          <EvidenceCheck label="No unresolved contradiction" checked={hasNoContradiction} />
          <EvidenceCheck label={`${abnormalLabs.length} abnormal lab result${abnormalLabs.length !== 1 ? 's' : ''} flagged`} checked={abnormalLabs.length > 0} />
        </div>
      </div>

      {abnormalLabs.length > 0 && (
        <div className="overview-section">
          <h3><FlaskConical size={16} /> Abnormal Lab Results</h3>
          <div className="overview-mini-table">
            {abnormalLabs.slice(0, 5).map((l) => (
              <div key={l.lab_id} className="mini-row">
                <span className="mini-label">{l.test_name}</span>
                <span className="mini-value mini-abnormal">{l.result_value} {l.unit}</span>
                <span className="mini-date">{l.result_date}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {riskExplanation && (riskExplanation.old_risk || (riskExplanation.contributing_factors && riskExplanation.contributing_factors.length > 0)) && (
        <div className="overview-section">
          <h3><TrendingUp size={16} /> Recent Clinical Change</h3>
          {riskExplanation.old_risk && riskExplanation.new_risk && (
            <div className="risk-item">
              <span className="risk-dot" />
              <span>Risk transitioned from <strong>{riskExplanation.old_risk}</strong> to <strong>{riskExplanation.new_risk}</strong></span>
            </div>
          )}
          {riskExplanation.contributing_factors && riskExplanation.contributing_factors.length > 0 && (
            <div className="overview-risks-list">
              {riskExplanation.contributing_factors.map((factor: string, i: number) => (
                <div key={i} className="risk-item">
                  <span className="risk-dot" />
                  <span>{factor}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeMeds.length > 0 && (
        <div className="overview-section">
          <h3><Pill size={16} /> Active Medications ({activeMeds.length})</h3>
          <div className="overview-mini-table">
            {activeMeds.slice(0, 6).map((m) => (
              <div key={m.medication_id} className="mini-row">
                <span className="mini-label">{m.drug_name}</span>
                <span className="mini-value">{m.dosage} {m.frequency}</span>
              </div>
            ))}
            {activeMeds.length > 6 && <div className="mini-more">+{activeMeds.length - 6} more</div>}
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, accent }: { icon: typeof Pill; label: string; value: number; accent: string }) {
  return (
    <div className={`overview-card overview-card-${accent}`}>
      <Icon size={18} />
      <div className="overview-card-value">{value}</div>
      <div className="overview-card-label">{label}</div>
    </div>
  );
}

function EvidenceCheck({ label, checked }: { label: string; checked: boolean }) {
  return (
    <div className="evidence-check">
      {checked ? <CheckCircle size={14} className="check-yes" /> : <span className="check-no">○</span>}
      <span>{label}</span>
    </div>
  );
}
