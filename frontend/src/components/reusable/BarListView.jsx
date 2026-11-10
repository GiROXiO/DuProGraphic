// Lista de barras horizontales. items: [{ label, value, detalle? }]
export default function BarListView({ items, color = "bg-brand-500" }) {
  const max = Math.max(1, ...items.map((i) => i.value));

  return (
    <ul className="space-y-3">
      {items.map((i) => (
        <li key={i.label}>
          <div className="mb-1 flex justify-between gap-3 text-sm">
            <span className="truncate font-medium text-ink-900">{i.label}</span>
            <span className="flex-shrink-0 text-ink-500">
              {i.value}
              {i.detalle ? ` · ${i.detalle}` : ""}
            </span>
          </div>
          <div className="h-2 rounded-full bg-ink-100">
            <div
              className={`h-2 rounded-full ${color}`}
              style={{ width: `${(i.value / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
