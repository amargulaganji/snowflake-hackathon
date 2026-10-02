import { useState } from 'react';
import type { EvidenceItem } from '../types';

interface EvidenceChainProps {
  items: EvidenceItem[];
}

const SOURCE_CONFIG: Record<string, { icon: string; label: string }> = {
  structured: { icon: '\u{1F4CA}', label: 'Structured Data' },
  document: { icon: '\u{1F4DD}', label: 'Clinical Note' },
  policy: { icon: '\u{1F4DC}', label: 'Policy Document' },
  guideline: { icon: '\u{1F48A}', label: 'Drug Guideline' },
  udf: { icon: '\u2699\uFE0F', label: 'Analysis' },
};

export function EvidenceChain({ items }: EvidenceChainProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (items.length === 0) return null;

  return (
    <div className="evidence-chain">
      <div className="evidence-header">Evidence Sources ({items.length})</div>
      {items.map((item, idx) => {
        const config = SOURCE_CONFIG[item.source_type] || SOURCE_CONFIG.structured;
        const isExpanded = expandedIndex === idx;
        const displayName = item.source_name !== 'unknown' ? item.source_name : config.label;

        return (
          <div key={idx} className="evidence-item">
            <button
              className="evidence-toggle"
              onClick={() => setExpandedIndex(isExpanded ? null : idx)}
            >
              <span className="evidence-icon">{config.icon}</span>
              <div className="evidence-info">
                <span className="evidence-source">{displayName}</span>
                <span className="evidence-type-label">{config.label}</span>
              </div>
              <span className="evidence-chevron">{isExpanded ? '\u25BC' : '\u25B6'}</span>
            </button>
            {isExpanded && (
              <div className="evidence-content">{item.content}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
