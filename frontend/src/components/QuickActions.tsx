import type { MemberSummary } from '../types';

interface QuickActionsProps {
  member: MemberSummary;
  onAsk: (question: string) => void;
}

export function QuickActions({ member, onAsk }: QuickActionsProps) {
  const questions: { label: string; question: string }[] = [
    {
      label: 'Polypharmacy Risk',
      question: `Assess the polypharmacy risk for member ${member.member_id}. Include active medication count, flagged interactions, and clinical reasoning.`,
    },
    {
      label: 'Drug Interactions',
      question: `Check for any dangerous drug interactions among member ${member.member_id}'s current active medications.`,
    },
    {
      label: 'Abnormal Labs',
      question: `What are the recent abnormal lab results for member ${member.member_id}? Explain their clinical significance.`,
    },
    {
      label: 'Policy Compliance',
      question: `Check policy compliance for member ${member.member_id}'s active medications. Flag any Beers Criteria, step therapy, or prior auth issues.`,
    },
    {
      label: 'Clinical Summary',
      question: `Provide a comprehensive clinical summary for member ${member.member_id} including active conditions, current medications, and recent encounters.`,
    },
  ];

  return (
    <div className="quick-actions">
      <div className="quick-actions-label">Quick Actions</div>
      <div className="quick-actions-grid">
        {questions.map((q) => (
          <button
            key={q.label}
            className="quick-action-btn"
            onClick={() => onAsk(q.question)}
          >
            {q.label}
          </button>
        ))}
      </div>
    </div>
  );
}
