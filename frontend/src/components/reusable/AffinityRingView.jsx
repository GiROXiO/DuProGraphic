// Anillo que muestra la afinidad (0 a 100) calculada por el grafo.
export default function AffinityRingView({ value = 0, size = 52 }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const r = 20;
  const c = 2 * Math.PI * r;
  const color = v >= 70 ? "#0ea37c" : v >= 40 ? "#6844f0" : "#b4bad3";

  return (
    <div
      className="relative flex-shrink-0"
      style={{ width: size, height: size }}
      title={`Afinidad ${v} de 100`}
    >
      <svg viewBox="0 0 48 48" className="h-full w-full -rotate-90">
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke="#e6e8f2"
          strokeWidth="4"
        />
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - v / 100)}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-ink-900">
        {v}
      </span>
    </div>
  );
}
