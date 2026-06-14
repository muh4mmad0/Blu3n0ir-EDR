import { gaugeClass } from "../utils.js";

export default function Gauge({ label, value, displayValue, max = 100 }) {
  const percent = value == null ? null : Math.min(100, (value / max) * 100);

  return (
    <div className="gauge">
      <div className="gauge__label">{label}</div>
      <div className="gauge__value">{displayValue}</div>
      {percent != null && (
        <div className="gauge__bar">
          <div
            className={`gauge__bar-fill ${gaugeClass(percent)}`}
            style={{ width: `${percent}%` }}
          />
        </div>
      )}
    </div>
  );
}
