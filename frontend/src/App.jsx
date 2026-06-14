import { useEffect, useState, useCallback } from "react";
import DeviceList from "./components/DeviceList.jsx";
import DeviceDetail from "./components/DeviceDetail.jsx";
import api from "./api.js";

const POLL_MS = 5000;

export default function App() {
  const [agents, setAgents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [processes, setProcesses] = useState([]);
  const [deviceAlerts, setDeviceAlerts] = useState([]);
  const [openAlertCount, setOpenAlertCount] = useState(0);
  const [clock, setClock] = useState(new Date());
  const [error, setError] = useState(null);

  // Clock for the top bar.
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // Poll device list + global open-alert count.
  const refreshFleet = useCallback(async () => {
    try {
      const [agentList, openAlerts] = await Promise.all([
        api.listAgents(),
        api.listAlerts({ resolved: false }),
      ]);
      setAgents(agentList);
      setOpenAlertCount(openAlerts.length);
      setError(null);

      // Auto-select the first device once data arrives.
      setSelectedId((current) => {
        if (current && agentList.some((a) => a.id === current)) return current;
        return agentList[0]?.id ?? null;
      });
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refreshFleet();
    const id = setInterval(refreshFleet, POLL_MS);
    return () => clearInterval(id);
  }, [refreshFleet]);

  // Poll processes + alerts for the selected device.
  const refreshDevice = useCallback(async (id) => {
    if (!id) {
      setProcesses([]);
      setDeviceAlerts([]);
      return;
    }
    try {
      const [procList, alertList] = await Promise.all([
        api.getProcesses(id),
        api.listAlerts({ agent_id: id }),
      ]);
      setProcesses(procList);
      setDeviceAlerts(alertList);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refreshDevice(selectedId);
    if (!selectedId) return;
    const id = setInterval(() => refreshDevice(selectedId), POLL_MS);
    return () => clearInterval(id);
  }, [selectedId, refreshDevice]);

  const handleResolve = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
      await Promise.all([refreshDevice(selectedId), refreshFleet()]);
    } catch (err) {
      setError(err.message);
    }
  };

  const onlineCount = agents.filter((a) => a.status === "online").length;
  const selectedAgent = agents.find((a) => a.id === selectedId) || null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__brand-mark">●</span> MINI EDR
        </div>
        <div className="topbar__stats">
          <div className="stat">
            <span className="stat__label">Online</span>
            <span className="stat__value stat__value--accent">
              {onlineCount} / {agents.length}
            </span>
          </div>
          <div className="stat">
            <span className="stat__label">Open Alerts</span>
            <span className={`stat__value ${openAlertCount > 0 ? "stat__value--alert" : ""}`}>
              {openAlertCount}
            </span>
          </div>
          <div className="stat">
            <span className="stat__label">Time</span>
            <span className="stat__value">{clock.toLocaleTimeString()}</span>
          </div>
        </div>
      </header>

      {error && (
        <div className="banner banner--error">
          Couldn't reach the backend ({error}). Retrying every {POLL_MS / 1000}s…
        </div>
      )}

      <div className="layout">
        <DeviceList agents={agents} selectedId={selectedId} onSelect={setSelectedId} />
        <main className="main">
          {selectedAgent ? (
            <DeviceDetail
              agent={selectedAgent}
              processes={processes}
              alerts={deviceAlerts}
              onResolve={handleResolve}
            />
          ) : (
            <div className="empty-state">
              <div className="empty-state__title">No device selected</div>
              <div>
                Start an agent (see <code>agent/agent.py</code>) and it will appear here
                automatically.
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
