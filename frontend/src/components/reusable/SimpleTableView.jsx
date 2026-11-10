// Tabla sencilla. columns: [{ key, label }]; si un valor es una lista se muestra como etiquetas.
export default function SimpleTableView({
  columns,
  rows,
  vacio = "Sin resultados.",
  limite = 20,
}) {
  if (!rows || rows.length === 0) {
    return <p className="text-sm text-ink-500">{vacio}</p>;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-ink-100">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-ink-100/60 text-xs uppercase tracking-wide text-ink-500">
          <tr>
            {columns.map((c) => (
              <th key={c.key} className="px-4 py-2.5 font-semibold">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-100">
          {rows.slice(0, limite).map((fila, i) => (
            <tr key={i} className="align-top">
              {columns.map((c) => {
                const valor = fila[c.key];
                return (
                  <td key={c.key} className="px-4 py-2.5 text-ink-900">
                    {Array.isArray(valor) ? (
                      <div className="flex flex-wrap gap-1.5">
                        {valor.map((v) => (
                          <span
                            key={v}
                            className="rounded-md bg-brand-50 px-2 py-0.5 text-xs text-brand-700"
                          >
                            {v}
                          </span>
                        ))}
                      </div>
                    ) : (
                      valor
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > limite && (
        <p className="border-t border-ink-100 px-4 py-2 text-xs text-ink-500">
          Mostrando {limite} de {rows.length} resultados.
        </p>
      )}
    </div>
  );
}
