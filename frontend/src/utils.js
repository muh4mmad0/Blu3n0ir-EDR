export function formatUptime(seconds) {
  if (seconds == null) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  const pad = (n) => String(n).padStart(2, "0");

  if (days > 0) {
    return `${days}d ${pad(hours)}:${pad(minutes)}`;
  }
  return `${pad(hours)}:${pad(minutes)}:${pad(Math.floor(seconds % 60))}`;
}

export function formatRelativeTime(isoString) {
  if (!isoString) return "—";
  // Treat naive timestamps (no timezone info) as UTC.
  const normalized = /Z|[+-]\d\d:\d\d$/.test(isoString) ? isoString : `${isoString}Z`;
  const date = new Date(normalized);
  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.round(diffMs / 1000);

  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

export function severityRank(severity) {
  const idx = SEVERITY_ORDER.indexOf(severity);
  return idx === -1 ? SEVERITY_ORDER.length : idx;
}

export function gaugeClass(percent) {
  if (percent == null) return "";
  if (percent >= 85) return "gauge__bar-fill--danger";
  if (percent >= 60) return "gauge__bar-fill--warn";
  return "";
}
