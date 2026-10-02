import type { ChatMessage, MemberSummary } from '../types';

interface ExportButtonProps {
  messages: ChatMessage[];
  member: MemberSummary;
}

export function ExportButton({ messages, member }: ExportButtonProps) {
  if (messages.length === 0) return null;

  const handleExport = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const pairs = messages.reduce<{ question: string; answer: string; risk?: string; evidence: number; timestamp: string }[]>(
      (acc, msg) => {
        if (msg.role === 'user') {
          acc.push({ question: msg.content, answer: '', evidence: 0, timestamp: msg.timestamp.toLocaleString() });
        } else if (acc.length > 0) {
          const last = acc[acc.length - 1];
          last.answer = msg.content;
          last.risk = msg.response?.risk_level || undefined;
          last.evidence = msg.response?.evidence_chain?.length || 0;
        }
        return acc;
      },
      [],
    );

    const html = `<!DOCTYPE html>
<html><head><title>Clinical Summary - ${member.first_name} ${member.last_name}</title>
<style>
  body { font-family: 'Inter', system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #212121; }
  .header { border-bottom: 2px solid #387ED1; padding-bottom: 16px; margin-bottom: 24px; }
  .header h1 { color: #387ED1; font-size: 20px; margin: 0 0 4px; }
  .header .meta { font-size: 13px; color: #757575; }
  .qa-pair { margin-bottom: 24px; page-break-inside: avoid; }
  .question { font-weight: 600; font-size: 14px; color: #387ED1; margin-bottom: 6px; }
  .answer { font-size: 13px; line-height: 1.7; white-space: pre-wrap; }
  .badges { margin-top: 6px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .risk-high { background: #FFEBEE; color: #C62828; }
  .risk-moderate { background: #FFF3E0; color: #B26A00; }
  .risk-low { background: #E8F5E9; color: #2E7D32; }
  .footer { border-top: 1px solid #E0E0E0; padding-top: 12px; margin-top: 32px; font-size: 11px; color: #757575; }
  .timestamp { font-size: 11px; color: #9E9E9E; }
  @media print { body { padding: 20px; } }
</style></head><body>
<div class="header">
  <h1>Clinical Summary: ${member.first_name} ${member.last_name}</h1>
  <div class="meta">${member.age}y | ${member.gender} | ${member.plan_type} | ID: ${member.member_id}</div>
  <div class="meta">Generated: ${new Date().toLocaleString()}</div>
</div>
${pairs
  .map(
    (p, i) => `
<div class="qa-pair">
  <div class="timestamp">${p.timestamp}</div>
  <div class="question">Q${i + 1}: ${p.question}</div>
  <div class="answer">${p.answer}</div>
  <div class="badges">
    ${p.risk ? `<span class="badge risk-${p.risk.toLowerCase().includes('high') ? 'high' : p.risk.toLowerCase().includes('moderate') ? 'moderate' : 'low'}">${p.risk}</span>` : ''}
    ${p.evidence > 0 ? `<span class="badge" style="background:#E3F2FD;color:#1565C0;">${p.evidence} evidence sources</span>` : ''}
  </div>
</div>`,
  )
  .join('')}
<div class="footer">
  Clinical Copilot &mdash; AI-generated summary. Verify all clinical information before acting.
  ${member.risk_flags.length > 0 ? `<br>Risk flags: ${member.risk_flags.join(', ')}` : ''}
</div>
</body></html>`;

    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 300);
  };

  return (
    <button className="export-btn" onClick={handleExport} title="Export clinical summary">
      Export Summary
    </button>
  );
}
