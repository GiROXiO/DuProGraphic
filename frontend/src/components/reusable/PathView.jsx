const COLORES = {
  Usuario: "bg-brand-50 text-brand-700 border-brand-100",
  Empresa: "bg-ink-900 text-white border-ink-900",
  Habilidad: "bg-signal-50 text-signal-600 border-signal-400/40",
  Proyecto: "bg-amber-50 text-amber-700 border-amber-200",
  Oferta: "bg-sky-50 text-sky-700 border-sky-200",
};

// Dibuja una ruta del grafo: nodos de color por tipo unidos por el nombre de la relación.
export default function PathView({ ruta }) {
  return (
    <div>
      <div className="flex flex-wrap items-center gap-y-3">
        {ruta.ruta.map((nombre, i) => (
          <div key={i} className="flex items-center">
            <div
              className={`rounded-xl border px-3 py-2 text-sm font-semibold ${
                COLORES[ruta.tipos[i]] ??
                "bg-ink-100 text-ink-700 border-ink-100"
              }`}
            >
              <span className="block text-[10px] font-medium uppercase tracking-wide opacity-70">
                {ruta.tipos[i]}
              </span>
              {nombre}
            </div>
            {i < ruta.relaciones.length && (
              <div className="mx-2 flex items-center text-ink-300">
                <span className="h-px w-4 bg-ink-300" />
                <span className="rounded-full border border-ink-100 bg-white px-2 py-0.5 text-[10px] font-semibold text-ink-500">
                  {ruta.relaciones[i]}
                </span>
                <span className="h-px w-4 bg-ink-300" />
              </div>
            )}
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-ink-500">
        {ruta.saltos} {ruta.saltos === 1 ? "salto" : "saltos"} en el grafo
      </p>
    </div>
  );
}
