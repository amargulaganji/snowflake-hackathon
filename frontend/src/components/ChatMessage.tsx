import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';
import { EvidenceChain } from './EvidenceChain';
import { RiskBadge } from './RiskBadge';
import { ContradictionBanner } from './ContradictionBanner';
import { EvidenceInspector } from './EvidenceInspector';
import type { Citation } from './EvidenceInspector';

interface ChatMessageProps {
  message: ChatMessage;
  onFollowUp?: (question: string) => void;
}

function generateFollowUps(content: string): string[] {
  const followUps: string[] = [];
  const lower = content.toLowerCase();
  if (lower.includes('polypharmacy') || lower.includes('medication'))
    followUps.push('Check for dangerous drug interactions');
  if (lower.includes('warfarin') || lower.includes('anticoagulant'))
    followUps.push('What is the latest INR result?');
  if (lower.includes('ckd') || lower.includes('kidney') || lower.includes('renal'))
    followUps.push('Are any medications contraindicated for this renal function?');
  if (lower.includes('fall') || lower.includes('orthostatic'))
    followUps.push('What fall prevention measures are in place?');
  if (lower.includes('diabetes') || lower.includes('hba1c') || lower.includes('metformin'))
    followUps.push('What is the latest HbA1c and diabetes management plan?');
  if (lower.includes('compliance') || lower.includes('policy'))
    followUps.push('Are there any prior authorization requirements?');
  if (followUps.length === 0) {
    followUps.push('What are the key risk factors for this member?');
    followUps.push('Check policy compliance for active medications');
  }
  return followUps.slice(0, 3);
}

function buildCitationsFromEvidence(evidence: { source_type: string; source_name: string; content: string; relevance: string | null }[]): Citation[] {
  return evidence.map((e, i) => ({
    index: i + 1,
    source_type: e.source_type,
    source_name: e.source_name,
    source_id: null,
    content_preview: e.content?.slice(0, 300) || '',
    metadata: {},
  }));
}

function renderWithCitations(text: string): string {
  return text.replace(/\[(\d+)\]/g, (match, num) => {
    return `<cite data-idx="${num}">${match}</cite>`;
  });
}

export function ChatMessageBubble({ message, onFollowUp }: ChatMessageProps) {
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [highlightCitation, setHighlightCitation] = useState<number | null>(null);

  if (message.role === 'user') {
    return (
      <div className="message message-user">
        <div className="message-bubble user-bubble">{message.content}</div>
      </div>
    );
  }

  const resp = message.response;
  const followUps = onFollowUp ? generateFollowUps(message.content) : [];
  const citations = resp?.citations
    ? (resp.citations as Citation[])
    : resp?.evidence_chain && resp.evidence_chain.length > 0
    ? buildCitationsFromEvidence(resp.evidence_chain)
    : [];

  const handleCitationClick = (idx: number) => {
    setHighlightCitation(idx);
    setInspectorOpen(true);
  };

  return (
    <div className="message message-assistant">
      <div className="message-bubble assistant-bubble">
        {resp?.contradiction_detected && resp.contradiction_details && (
          <ContradictionBanner details={resp.contradiction_details} />
        )}
        <div className="message-text markdown-content" onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.tagName === 'CITE' && target.dataset.idx) {
            handleCitationClick(parseInt(target.dataset.idx, 10));
          }
        }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children, ...props }) => {
                if (typeof children === 'string' && /\[\d+\]/.test(children)) {
                  return <p {...props} dangerouslySetInnerHTML={{ __html: renderWithCitations(children) }} />;
                }
                return <p {...props}>{children}</p>;
              }
            }}
          >{message.content}</ReactMarkdown>
        </div>
        {resp?.risk_level && <RiskBadge level={resp.risk_level} />}

        {citations.length > 0 && (
          <div className="evidence-actions">
            <button className="evidence-inspector-btn" onClick={() => setInspectorOpen(true)}>
              View Evidence ({citations.length} source{citations.length !== 1 ? 's' : ''})
            </button>
          </div>
        )}

        {resp?.evidence_chain && resp.evidence_chain.length > 0 && (
          <EvidenceChain items={resp.evidence_chain} />
        )}
        {resp?.insufficient_evidence && (
          <div className="insufficient-evidence-note">
            <span className="insufficient-icon">i</span>
            <span>The agent indicated insufficient evidence for a complete answer. Verify with additional clinical sources.</span>
          </div>
        )}
        {followUps.length > 0 && onFollowUp && (
          <div className="follow-ups">
            {followUps.map((q) => (
              <button key={q} className="follow-up-btn" onClick={() => onFollowUp(q)}>{q}</button>
            ))}
          </div>
        )}
      </div>

      {inspectorOpen && (
        <EvidenceInspector
          citations={citations}
          contradictionDetected={resp?.contradiction_detected || false}
          insufficientEvidence={resp?.insufficient_evidence || false}
          onClose={() => { setInspectorOpen(false); setHighlightCitation(null); }}
          highlightIndex={highlightCitation}
        />
      )}
    </div>
  );
}
