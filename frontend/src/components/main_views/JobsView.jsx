import { useState } from "react";
import { Search } from "lucide-react";
import ShellView from "../nav_layout/ShellView";
import JobCardView from "../reusable/JobCardView";
import { getUser } from "../../api";
import useFetch from "../../useFetch";

export default function JobsView() {
  const user = getUser();
  const esUsuario = user?.rol === "usuario" && user?.entidad_id;
  const [busqueda, setBusqueda] = useState("");

  const {
    data: ofertas,
    loading,
    error,
  } = useFetch(esUsuario ? `/api/users/${user.entidad_id}/feed/jobs` : null);

  const q = busqueda.trim().toLowerCase();
  const filtradas = (ofertas ?? []).filter(
    (o) =>
      !q ||
      [o.titulo, o.empresa, o.sector, ...(o.habilidades ?? [])]
        .filter(Boolean)
        .some((texto) => texto.toLowerCase().includes(q)),
  );

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

          {loading && <p className="text-ink-500">Buscando oportunidades...</p>}
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
              <JobCardView key={oferta.id} oferta={oferta} />
            ))}
          </div>
        </>
      )}
    </ShellView>
  );
}
