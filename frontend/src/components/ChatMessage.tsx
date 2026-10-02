import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';
import { EvidenceChain } from './EvidenceChain';
import { RiskBadge } from './RiskBadge';
import { ContradictionBanner } from './ContradictionBanner';

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

export function ChatMessageBubble({ message, onFollowUp }: ChatMessageProps) {
  if (message.role === 'user') {
    return (
      <div className="message message-user">
        <div className="message-bubble user-bubble">{message.content}</div>
      </div>
    );
  }

  const resp = message.response;
  const followUps = onFollowUp ? generateFollowUps(message.content) : [];

  return (
    <div className="message message-assistant">
      <div className="message-bubble assistant-bubble">
        {resp?.contradiction_detected && resp.contradiction_details && (
          <ContradictionBanner details={resp.contradiction_details} />
        )}
        <div className="message-text markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
        {resp?.risk_level && <RiskBadge level={resp.risk_level} />}
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
              <button key={q} className="follow-up-btn" onClick={() => onFollowUp(q)}>
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
