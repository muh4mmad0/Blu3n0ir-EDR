import { formatRelativeTime, severityRank } from "../utils.js";

export default function AlertsPanel({ alerts, onResolve, emptyText = "No alerts." }) {
  const sorted = [...alerts].sort((a, b) => {
    if (a.resolved !== b.resolved) return a.resolved ? 1 : -1;
    const rankDiff = severityRank(a.severity) - severityRank(b.severity);
    if (rankDiff !== 0) return rankDiff;
    return new Date(b.created_at) - new Date(a.created_at);
  });

  if (sorted.length === 0) {
    return <div className="alert-empty">{emptyText}</div>;
  }

  return (
    <div className="alert-list">
      {sorted.map((alert) => (
        <div key={alert.id} className={`alert alert--${alert.severity}`}>
          <span className="alert__severity">{alert.severity}</span>
          <span className="alert__body">
            <div className="alert__message">{alert.message}</div>
            <div className="alert__meta">
              {alert.alert_type} · {formatRelativeTime(alert.created_at)}
            </div>
          </span>
          {alert.resolved ? (
            <span className="alert__resolved-tag">resolved</span>
          ) : (
            <button className="alert__resolve" onClick={() => onResolve(alert.id)}>
              Resolve
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
