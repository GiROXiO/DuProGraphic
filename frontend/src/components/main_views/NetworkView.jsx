import { useState } from "react";
import { Link } from "react-router-dom";
import ShellView from "../nav_layout/ShellView";
import api, { getUser } from "../../api";
import useFetch from "../../useFetch";

const TABS = [
  { id: "conexiones", label: "Conexiones" },
  { id: "recibidas", label: "Recibidas" },
  { id: "enviadas", label: "Enviadas" },
];

const VACIO = {
  conexiones:
    "Aún no tienes conexiones. Busca personas en tu red cercana desde el Inicio.",
  recibidas: "No tienes solicitudes nuevas.",
  enviadas: "No tienes solicitudes pendientes.",
};

const boton =
  "rounded-xl px-4 py-2 text-sm font-semibold transition disabled:opacity-50";
const claro = `${boton} border border-ink-100 bg-white text-ink-700 hover:bg-ink-100`;
const marca = `${boton} bg-brand-600 text-white hover:bg-brand-700`;

function PersonaFila({ persona, detalle, children }) {
  return (
    <li className="flex flex-wrap items-center gap-4 rounded-2xl border border-ink-100 bg-white p-4">
      <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-brand-50 text-lg font-bold text-brand-600">
        {persona.nombre?.charAt(0).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <Link
          to={`/people/${persona.id}`}
          className="font-semibold text-ink-900 hover:text-brand-600 hover:underline"
        >
          {persona.nombre}
        </Link>
        <p className="truncate text-sm text-ink-500">
          {[persona.perfil, persona.universidad].filter(Boolean).join(" · ")}
        </p>
        {detalle && <p className="text-xs text-ink-300">{detalle}</p>}
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </li>
  );
}

// Se vuelve a montar (y a cargar) cada vez que cambia "version", es decir, tras cada acción.
function RedPagina({ userId, tab, setTab, onCambio }) {
  const { data, loading, error } = useFetch(`/api/users/${userId}/connections`);
  const [ocupado, setOcupado] = useState(null);
  const [errorAccion, setErrorAccion] = useState("");

  const ejecutar = async (id, peticion) => {
    setErrorAccion("");
    setOcupado(id);
    try {
      await peticion();
      onCambio();
    } catch (err) {
      setErrorAccion(
        err.response?.data?.detail || "No se pudo completar la acción.",
      );
      setOcupado(null);
    }
  };

  const aceptar = (id) =>
    ejecutar(id, () =>
      api.post(`/api/users/${userId}/connection-requests/${id}/accept`),
    );
  const retirar = (id) =>
    ejecutar(id, () =>
      api.delete(`/api/users/${userId}/connection-requests/${id}`),
    );

  return (
    <>
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-ink-100 pb-3">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              t.id === tab
                ? "bg-ink-900 text-white"
                : "text-ink-500 hover:bg-ink-100"
            }`}
          >
            {t.label}
            {data && ` (${data[t.id].length})`}
          </button>
        ))}
      </nav>

      {loading && <p className="text-ink-500">Cargando tu red...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {errorAccion && (
        <div
          role="alert"
          className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {errorAccion}
        </div>
      )}

      {data && (
        <>
          {data[tab].length === 0 && (
            <p className="text-ink-500">{VACIO[tab]}</p>
          )}
          <ul className="space-y-3">
            {data[tab].map((p) => (
              <PersonaFila
                key={p.id}
                persona={p}
                detalle={
                  p.fecha
                    ? `${tab === "enviadas" ? "Enviada" : "Recibida"} el ${p.fecha}`
                    : null
                }
              >
                {tab === "recibidas" && (
                  <>
                    <button
                      disabled={ocupado === p.id}
                      onClick={() => aceptar(p.id)}
                      className={marca}
                    >
                      Aceptar
                    </button>
                    <button
                      disabled={ocupado === p.id}
                      onClick={() => retirar(p.id)}
                      className={claro}
                    >
                      Rechazar
                    </button>
                  </>
                )}
                {tab === "enviadas" && (
                  <button
                    disabled={ocupado === p.id}
                    onClick={() => retirar(p.id)}
                    className={claro}
                  >
                    Cancelar solicitud
                  </button>
                )}
                {tab === "conexiones" && (
                  <Link to={`/people/${p.id}`} className={claro}>
                    Ver perfil
                  </Link>
                )}
              </PersonaFila>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

export default function NetworkView() {
  const user = getUser();
  const esUsuario = user?.rol === "usuario" && user?.entidad_id;
  const [tab, setTab] = useState("conexiones");
  const [version, setVersion] = useState(0);

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Mi red
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Tus conexiones profesionales y las solicitudes pendientes.
        </p>
      </header>

      {!esUsuario ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          Las conexiones profesionales son para cuentas de usuario.
        </div>
      ) : (
        <RedPagina
          key={version}
          userId={user.entidad_id}
          tab={tab}
          setTab={setTab}
          onCambio={() => setVersion((v) => v + 1)}
        />
      )}
    </ShellView>
  );
}
