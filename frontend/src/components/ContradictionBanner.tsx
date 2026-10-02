interface ContradictionBannerProps {
  details: string;
}

export function ContradictionBanner({ details }: ContradictionBannerProps) {
  return (
    <div className="contradiction-banner">
      <span className="contradiction-icon">⚠️</span>
      <div className="contradiction-text">
        <strong>Contradiction Detected</strong>
        <p>{details}</p>
      </div>
    </div>
  );
}
