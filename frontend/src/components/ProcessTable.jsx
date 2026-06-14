export default function ProcessTable({ processes }) {
  if (processes.length === 0) {
    return <div className="alert-empty">No process data yet — waiting for the agent's next snapshot.</div>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>PID</th>
          <th>Name</th>
          <th>User</th>
          <th className="num">CPU %</th>
          <th className="num">Mem %</th>
        </tr>
      </thead>
      <tbody>
        {processes.map((p) => (
          <tr key={p.pid}>
            <td>{p.pid}</td>
            <td>{p.name}</td>
            <td>{p.username || "—"}</td>
            <td className="num">{(p.cpu_percent ?? 0).toFixed(1)}</td>
            <td className="num">{(p.memory_percent ?? 0).toFixed(1)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
