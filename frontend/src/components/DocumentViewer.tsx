import { useState } from 'react';
import { FileText, User, Calendar, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react';
import type { SourceDocument } from '../types';

interface DocumentViewerProps {
  items: SourceDocument[];
}

const SECTION_PATTERNS = [
  /^(SUBJECTIVE|OBJECTIVE|ASSESSMENT|PLAN|IMPRESSION|HISTORY|MEDICATIONS|ALLERGIES|VITALS|LABS|DIAGNOSIS|DISPOSITION|FOLLOW.?UP|CHIEF COMPLAINT|HPI|ROS|PHYSICAL EXAM)/im,
];

function parseSections(content: string): { heading: string; body: string }[] {
  const lines = content.split('\n');
  const sections: { heading: string; body: string }[] = [];
  let currentHeading = '';
  let currentBody: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    const isHeading = SECTION_PATTERNS.some((p) => p.test(trimmed)) || (trimmed === trimmed.toUpperCase() && trimmed.length > 2 && trimmed.length < 60 && /^[A-Z]/.test(trimmed));

    if (isHeading && trimmed) {
      if (currentHeading || currentBody.length > 0) {
        sections.push({ heading: currentHeading, body: currentBody.join('\n').trim() });
      }
      currentHeading = trimmed;
      currentBody = [];
    } else {
      currentBody.push(line);
    }
  }
  if (currentHeading || currentBody.length > 0) {
    sections.push({ heading: currentHeading, body: currentBody.join('\n').trim() });
  }
  return sections;
}

function extractFindings(content: string): string[] {
  const findings: string[] = [];
  const lower = content.toLowerCase();
  const patterns = [
    { regex: /hyperkalemia/i, label: 'Hyperkalemia', severity: 'high' },
    { regex: /polypharmacy/i, label: 'Polypharmacy', severity: 'high' },
    { regex: /ckd\s*(stage\s*\d)?/i, label: 'CKD', severity: 'moderate' },
    { regex: /heart failure|chf|hf\b/i, label: 'Heart Failure', severity: 'moderate' },
    { regex: /fall\s*risk|orthostatic/i, label: 'Fall Risk', severity: 'moderate' },
    { regex: /drug.?interaction/i, label: 'Drug Interaction', severity: 'high' },
    { regex: /bleeding\s*risk/i, label: 'Bleeding Risk', severity: 'high' },
    { regex: /renal\s*(insufficiency|failure|impairment)/i, label: 'Renal Impairment', severity: 'moderate' },
  ];
  for (const p of patterns) {
    if (p.regex.test(lower)) findings.push(p.label);
  }
  return findings;
}

export function DocumentViewer({ items }: DocumentViewerProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!items || items.length === 0) {
    return <div className="page-empty"><FileText size={40} strokeWidth={1} /><p>No documents found for this member.</p></div>;
  }

  return (
    <div className="document-viewer">
      {items.map((doc) => {
        const isExpanded = expandedId === doc.source_id;
        const sections = isExpanded ? parseSections(doc.content || '') : [];
        const findings = extractFindings(doc.content || doc.preview || '');

        return (
          <div key={doc.source_id} className={`doc-viewer-card ${isExpanded ? 'doc-viewer-card-open' : ''}`}>
            <button className="doc-viewer-header" onClick={() => setExpandedId(isExpanded ? null : doc.source_id)}>
              <FileText size={18} className="doc-viewer-icon" />
              <div className="doc-viewer-title-block">
                <div className="doc-viewer-title">{doc.title || 'Untitled Document'}</div>
                <div className="doc-viewer-meta">
                  {doc.date && <span><Calendar size={11} /> {doc.date}</span>}
                  {doc.author && <span><User size={11} /> {doc.author}</span>}
                  <span className="doc-type-badge">{doc.source_type === 'clinical_note' ? 'Clinical Note' : doc.source_type}</span>
                </div>
              </div>
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>

            {!isExpanded && findings.length > 0 && (
              <div className="doc-viewer-findings-preview">
                {findings.slice(0, 3).map((f) => (
                  <span key={f} className="finding-tag">{f}</span>
                ))}
              </div>
            )}

            {isExpanded && (
              <div className="doc-viewer-body">
                {findings.length > 0 && (
                  <div className="doc-viewer-findings">
                    <div className="findings-header"><AlertTriangle size={13} /> AI Extracted Findings</div>
                    <div className="findings-list">
                      {findings.map((f) => (
                        <span key={f} className="finding-tag finding-tag-expanded">{f}</span>
                      ))}
                    </div>
                  </div>
                )}

                {sections.length > 0 ? (
                  sections.map((sec, i) => (
                    <div key={i} className="doc-section">
                      {sec.heading && <div className="doc-section-heading">{sec.heading}</div>}
                      <div className="doc-section-body">{sec.body || '(empty)'}</div>
                    </div>
                  ))
                ) : (
                  <div className="doc-section">
                    <div className="doc-section-body">{doc.content || doc.preview || 'No content available'}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
