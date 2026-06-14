import StatusDot from "./StatusDot.jsx";
import { formatRelativeTime } from "../utils.js";

export default function DeviceList({ agents, selectedId, onSelect }) {
  return (
    <nav className="sidebar" aria-label="Devices">
      <div className="sidebar__heading">Devices ({agents.length})</div>
      {agents.map((agent) => (
        <button
          key={agent.id}
          className={`device-row ${agent.id === selectedId ? "device-row--active" : ""}`}
          onClick={() => onSelect(agent.id)}
        >
          <StatusDot online={agent.status === "online"} />
          <span className="device-row__info">
            <span className="device-row__hostname">{agent.hostname}</span>
            <span className="device-row__meta">
              {agent.os || "unknown"} · {agent.ip_address || "no ip"} ·{" "}
              {formatRelativeTime(agent.last_seen)}
            </span>
          </span>
          <span className="device-row__chevron">›</span>
        </button>
      ))}
      {agents.length === 0 && (
        <div className="alert-empty" style={{ padding: "0 20px" }}>
          No agents have checked in yet.
        </div>
      )}
    </nav>
  );
}
