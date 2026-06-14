const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options.method || "GET"} ${path} failed: ${res.status} ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listAgents: () => request("/api/agents"),
  getAgent: (id) => request(`/api/agents/${id}`),
  getProcesses: (id) => request(`/api/agents/${id}/processes`),
  listAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/alerts${qs ? `?${qs}` : ""}`);
  },
  resolveAlert: (id) => request(`/api/alerts/${id}/resolve`, { method: "PATCH" }),
};

export default api;
