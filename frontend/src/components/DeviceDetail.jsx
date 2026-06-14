import Gauge from "./Gauge.jsx";
import ProcessTable from "./ProcessTable.jsx";
import AlertsPanel from "./AlertsPanel.jsx";
import StatusDot from "./StatusDot.jsx";
import { formatRelativeTime, formatUptime } from "../utils.js";

export default function DeviceDetail({ agent, processes, alerts, onResolve }) {
  return (
    <div>
      <div className="detail-header">
        <StatusDot online={agent.status === "online"} />
        <span className="detail-header__hostname">{agent.hostname}</span>
        <span className="detail-header__os">
          {agent.os} {agent.os_version}
        </span>
      </div>
      <div className="detail-subline">
        {agent.ip_address || "no ip"} · agent {agent.id.slice(0, 8)} · last seen{" "}
        {formatRelativeTime(agent.last_seen)}
      </div>

      <div className="gauges">
        <Gauge
          label="CPU"
          value={agent.cpu_percent}
          displayValue={agent.cpu_percent != null ? `${agent.cpu_percent.toFixed(1)}%` : "—"}
        />
        <Gauge
          label="Memory"
          value={agent.ram_percent}
          displayValue={agent.ram_percent != null ? `${agent.ram_percent.toFixed(1)}%` : "—"}
        />
        <Gauge label="Uptime" value={null} displayValue={formatUptime(agent.uptime_seconds)} />
      </div>

      <section>
        <h2 className="section-heading">
          Processes <span className="section-heading__count">{processes.length}</span>
        </h2>
        <ProcessTable processes={processes} />
      </section>

      <section>
        <h2 className="section-heading">
          Alerts{" "}
          <span className="section-heading__count">
            {alerts.filter((a) => !a.resolved).length} open
          </span>
        </h2>
        <AlertsPanel
          alerts={alerts}
          onResolve={onResolve}
          emptyText="No alerts for this device."
        />
      </section>
    </div>
  );
}
