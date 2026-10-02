interface RiskBadgeProps {
  level: string;
}

export function RiskBadge({ level }: RiskBadgeProps) {
  const normalized = level.toLowerCase();
  let className = 'risk-badge';

  if (normalized.includes('high') || normalized.includes('contraindicated')) {
    className += ' risk-high';
  } else if (normalized.includes('moderate') || normalized.includes('major')) {
    className += ' risk-moderate';
  } else {
    className += ' risk-low';
  }

  return <span className={className}>{level}</span>;
}
