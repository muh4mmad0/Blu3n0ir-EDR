export default function StatusDot({ online }) {
  return (
    <span
      className={`status-dot ${online ? "status-dot--online" : "status-dot--offline"}`}
      title={online ? "Online" : "Offline"}
    />
  );
}
