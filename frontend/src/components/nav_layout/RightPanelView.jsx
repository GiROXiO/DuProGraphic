import { useState } from "react";
import { Link } from "react-router-dom";
import useFetch from "../../useFetch";
import ConnectButtonView from "../reusable/ConnectButtonView";

function Fila({ inicial, titulo, detalle, extra, persona, to, accion }) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl font-bold ${
          persona ? "bg-brand-50 text-brand-600" : "bg-ink-100 text-ink-700"
        }`}
      >
        {inicial}
      </div>
      <div className="min-w-0 flex-1">
        {to ? (
          <Link
            to={to}
            className="block truncate text-sm font-semibold text-ink-900 hover:text-brand-600 hover:underline"
          >
            {titulo}
          </Link>
        ) : (
          <p className="truncate text-sm font-semibold text-ink-900">
            {titulo}
          </p>
        )}
        <p className="truncate text-xs text-ink-500">{detalle}</p>
        {accion && <div className="mt-1.5">{accion}</div>}
      </div>
      {extra && (
        <span className="text-xs font-semibold text-brand-600">{extra}</span>
      )}
    </div>
  );
}

export default function RightPanelView({ userId, onCambio }) {
  const { data, loading, error } = useFetch(
    `/api/users/${userId}/network/suggestions`,
  );
  // Cambios hechos desde este panel; si no hay, manda lo que dice el servidor (p.relacion).
  const [estados, setEstados] = useState({});

  const personas = data?.personas?.slice(0, 4) ?? [];
  const empresas = data?.empresas?.slice(0, 4) ?? [];
  const vacio =
    !loading && !error && personas.length === 0 && empresas.length === 0;

  return (
    <aside className="space-y-6 rounded-2xl border border-ink-100 bg-white p-5">
      <h2 className="font-bold text-ink-900">Tu red cercana</h2>

      {loading && (
        <p className="text-sm text-ink-500">Explorando el grafo...</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {vacio && <p className="text-sm text-ink-500">Aún no hay sugerencias.</p>}

      {personas.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
            Personas
          </h3>
          {personas.map((p) => {
            const relacion = estados[p.id] ?? p.relacion ?? "ninguna";
            const base =
              p.contactos > 0
                ? `${p.perfil ?? ""} · ${p.contactos} en común`
                : p.perfil;
            return (
              <Fila
                key={p.id}
                persona
                to={`/people/${p.id}`}
                inicial={p.nombre?.charAt(0).toUpperCase()}
                titulo={p.nombre}
                detalle={
                  relacion === "recibida"
                    ? `${base} · Quiere conectar contigo`
                    : base
                }
                extra={p.afinidad != null ? `${p.afinidad}%` : null}
                accion={
                  <ConnectButtonView
                    personaId={p.id}
                    relacion={relacion}
                    compacto
                    onChange={(nuevo) => {
                      setEstados((e) => ({ ...e, [p.id]: nuevo }));
                      onCambio?.();
                    }}
                  />
                }
              />
            );
          })}
        </div>
      )}

      {empresas.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-500">
            Empresas
          </h3>
          {empresas.map((e) => (
            <Fila
              key={e.id}
              inicial={e.nombre?.charAt(0).toUpperCase()}
              titulo={e.nombre}
              detalle={
                e.distancia != null
                  ? `${e.sector ?? ""} · a ${e.distancia} ${e.distancia === 1 ? "salto" : "saltos"}`
                  : e.sector
              }
              extra={e.afinidad != null ? `${e.afinidad}%` : null}
            />
          ))}
        </div>
      )}
    </aside>
  );
}
