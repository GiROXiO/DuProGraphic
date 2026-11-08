import { useState } from "react";
import { Search } from "lucide-react";
import ShellView from "../nav_layout/ShellView";
import JobCardView from "../reusable/JobCardView";
import ApplicationCardView from "../reusable/ApplicationCardView";
import { getUser } from "../../api";
import useFetch from "../../useFetch";

export default function JobsView() {
  const user = getUser();
  const esUsuario = user?.rol === "usuario" && user?.entidad_id;
  const [tab, setTab] = useState("ofertas");
  const [busqueda, setBusqueda] = useState("");
  // Al cambiar estos números se vuelve a pedir la lista correspondiente (el parámetro ?v= lo ignora la API).
  const [versionOfertas, setVersionOfertas] = useState(0);
  const [versionPostulaciones, setVersionPostulaciones] = useState(0);

  const {
    data: ofertas,
    loading,
    error,
  } = useFetch(
    esUsuario
      ? `/api/users/${user.entidad_id}/feed/jobs?v=${versionOfertas}`
      : null,
  );
  const postulaciones = useFetch(
    esUsuario
      ? `/api/users/${user.entidad_id}/applications?v=${versionPostulaciones}`
      : null,
  );

  const q = busqueda.trim().toLowerCase();
  const filtradas = (ofertas ?? []).filter(
    (o) =>
      !q ||
      [o.titulo, o.empresa, o.sector, ...(o.habilidades ?? [])]
        .filter(Boolean)
        .some((texto) => texto.toLowerCase().includes(q)),
  );

  const TABS = [
    { id: "ofertas", label: "Para ti" },
    {
      id: "postulaciones",
      label: `Mis postulaciones${postulaciones.data ? ` (${postulaciones.data.length})` : ""}`,
    },
  ];

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Oportunidades
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Ordenadas por afinidad: tus habilidades, tu distancia en el grafo y
          tus contactos.
        </p>
      </header>

      {!esUsuario ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          Las ofertas recomendadas son para cuentas de usuario.
        </div>
      ) : (
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
              </button>
            ))}
          </nav>

          {tab === "ofertas" && (
            <>
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-300" />
                <input
                  type="search"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  placeholder="Filtrar por cargo, empresa o habilidad"
                  className="w-full rounded-xl border border-ink-100 bg-white py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                />
              </div>

              {loading && (
                <p className="text-ink-500">Buscando oportunidades...</p>
              )}
              {error && <p className="text-red-600">{error}</p>}
              {!loading && !error && filtradas.length === 0 && (
                <p className="text-ink-500">
                  {q
                    ? "Ninguna oferta coincide con tu búsqueda."
                    : "No hay ofertas recomendadas todavía."}
                </p>
              )}

              <div className="space-y-4">
                {filtradas.map((oferta) => (
                  <JobCardView
                    key={oferta.id}
                    oferta={oferta}
                    onPostulada={() => setVersionPostulaciones((v) => v + 1)}
                  />
                ))}
              </div>
            </>
          )}

          {tab === "postulaciones" && (
            <>
              {postulaciones.loading && (
                <p className="text-ink-500">Cargando tus postulaciones...</p>
              )}
              {postulaciones.error && (
                <p className="text-red-600">{postulaciones.error}</p>
              )}
              {postulaciones.data?.length === 0 && (
                <p className="text-ink-500">
                  Aún no te has postulado a ninguna oferta. Encuentra una en la
                  pestaña "Para ti".
                </p>
              )}

              <div className="space-y-4">
                {postulaciones.data?.map((p) => (
                  <ApplicationCardView
                    key={p.id}
                    postulacion={p}
                    onRetirada={() => {
                      // La oferta vuelve a recomendarse y la lista se actualiza.
                      setVersionPostulaciones((v) => v + 1);
                      setVersionOfertas((v) => v + 1);
                    }}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </ShellView>
  );
}
