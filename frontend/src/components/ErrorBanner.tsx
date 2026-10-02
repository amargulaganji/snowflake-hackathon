interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorBanner({ message, onRetry, onDismiss }: ErrorBannerProps) {
  return (
    <div className="error-banner">
      <div className="error-banner-content">
        <span className="error-banner-icon">!</span>
        <span className="error-banner-text">{message}</span>
      </div>
      <div className="error-banner-actions">
        {onRetry && (
          <button className="error-retry-btn" onClick={onRetry}>Retry</button>
        )}
        {onDismiss && (
          <button className="error-dismiss-btn" onClick={onDismiss}>Dismiss</button>
        )}
      </div>
    </div>
  );
}
