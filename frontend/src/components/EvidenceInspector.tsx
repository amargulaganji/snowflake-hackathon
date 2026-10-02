import { useState } from 'react';
import { X, Database, FileText, Shield, FlaskConical, ChevronDown, ChevronRight, CheckCircle, AlertTriangle } from 'lucide-react';

export interface Citation {
  index: number;
  source_type: string;
  source_name: string;
  source_id: string | null;
  content_preview: string;
  metadata: Record<string, string>;
}

interface EvidenceInspectorProps {
  citations: Citation[];
  contradictionDetected: boolean;
  insufficientEvidence: boolean;
  onClose: () => void;
  highlightIndex?: number | null;
}

const TYPE_ICON: Record<string, typeof Database> = {
  structured: Database,
  document: FileText,
  policy: Shield,
  guideline: FlaskConical,
  udf: FlaskConical,
};

const TYPE_LABEL: Record<string, string> = {
  structured: 'Structured Data',
  document: 'Clinical Document',
  policy: 'Policy Document',
  guideline: 'Drug Guideline',
  udf: 'Analysis',
};

export function EvidenceInspector({ citations, contradictionDetected, insufficientEvidence, onClose, highlightIndex }: EvidenceInspectorProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(highlightIndex ?? null);

  const grouped = citations.reduce<Record<string, Citation[]>>((acc, c) => {
    const key = c.source_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(c);
    return acc;
  }, {});

  const corroborationStatus = (() => {
    const types = new Set(citations.map((c) => c.source_type));
    const hasStructured = types.has('structured') || types.has('udf');
    const hasUnstructured = types.has('document') || types.has('guideline');
    if (hasStructured && hasUnstructured) return 'Structured + unstructured corroboration';
    if (hasStructured) return 'Structured data only';
    if (hasUnstructured) return 'Unstructured sources only';
    return 'No sources';
  })();

  return (
    <div className="evidence-inspector-overlay" onClick={onClose}>
      <div className="evidence-inspector" onClick={(e) => e.stopPropagation()}>
        <div className="inspector-header">
          <h3>Evidence Inspector</h3>
          <button className="drawer-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="inspector-summary">
          <div className="inspector-stat">{citations.length} source{citations.length !== 1 ? 's' : ''} used</div>
          <div className="inspector-stat">{corroborationStatus}</div>
          {!contradictionDetected && (
            <div className="inspector-stat inspector-stat-ok"><CheckCircle size={12} /> No unresolved contradiction</div>
          )}
          {contradictionDetected && (
            <div className="inspector-stat inspector-stat-warn"><AlertTriangle size={12} /> Contradiction detected</div>
          )}
          {insufficientEvidence && (
            <div className="inspector-stat inspector-stat-warn"><AlertTriangle size={12} /> Insufficient evidence flagged</div>
          )}
        </div>

        <div className="inspector-groups">
          {Object.entries(grouped).map(([type, items]) => {
            const Icon = TYPE_ICON[type] || Database;
            const label = TYPE_LABEL[type] || type;
            return (
              <div key={type} className="inspector-group">
                <div className="inspector-group-header">
                  <Icon size={14} />
                  <span>{label.toUpperCase()}</span>
                  <span className="inspector-group-count">{items.length}</span>
                </div>
                {items.map((c) => {
                  const isExpanded = expandedIdx === c.index;
                  const isHighlighted = highlightIndex === c.index;
                  return (
                    <div key={c.index} className={`inspector-citation ${isHighlighted ? 'inspector-citation-highlight' : ''}`}>
                      <button className="inspector-citation-header" onClick={() => setExpandedIdx(isExpanded ? null : c.index)}>
                        <span className="citation-badge">[{c.index}]</span>
                        <span className="citation-name">{c.source_name}</span>
                        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      </button>
                      {isExpanded && (
                        <div className="inspector-citation-body">
                          <div className="citation-preview">{c.content_preview}</div>
                          {Object.entries(c.metadata).filter(([, v]) => v).map(([k, v]) => (
                            <div key={k} className="citation-meta-row">
                              <span className="citation-meta-key">{k}</span>
                              <span className="citation-meta-val">{v}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>

        <div className="inspector-workflow">
          <div className="inspector-workflow-label">Workflow</div>
          <div className="inspector-workflow-steps">
            <span className="workflow-step">Retrieve</span>
            <span className="workflow-arrow">→</span>
            <span className="workflow-step">Safety</span>
            <span className="workflow-arrow">→</span>
            <span className="workflow-step">Policy</span>
            <span className="workflow-arrow">→</span>
            <span className="workflow-step">Validate</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface CitationLinkProps {
  index: number;
  onClick: (index: number) => void;
}

export function CitationLink({ index, onClick }: CitationLinkProps) {
  return (
    <button className="citation-link" onClick={() => onClick(index)} title={`View source [${index}]`}>
      [{index}]
    </button>
  );
}
