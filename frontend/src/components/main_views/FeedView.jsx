import { useState } from "react";
import { Link } from "react-router-dom";
import ShellView from "../nav_layout/ShellView";
import SidebarProfileView from "../nav_layout/SidebarProfileView";
import RightPanelView from "../nav_layout/RightPanelView";
import JobCardView from "../reusable/JobCardView";
import { getUser } from "../../api";
import useFetch from "../../useFetch";

export default function FeedView() {
  const user = getUser();
  const esUsuario = user?.rol === "usuario" && user?.entidad_id;
  // Al cambiar la red desde las sugerencias se recarga la cabecera (contactos y solicitudes).
  const [versionRed, setVersionRed] = useState(0);

  // Las ofertas solo aplican al rol usuario; con url null el hook no hace nada.
  const {
    data: ofertas,
    loading,
    error,
  } = useFetch(esUsuario ? `/api/users/${user.entidad_id}/feed/jobs` : null);

  return (
    <ShellView>
      {!esUsuario ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          Hola, {user?.nombre}. La vista de {user?.rol} se habilitará en la
          siguiente fase.
        </div>
      ) : (
        <div className="space-y-8">
          <SidebarProfileView key={versionRed} userId={user.entidad_id} />

          <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <section>
              <div className="mb-4 flex items-end justify-between">
                <h2 className="text-lg font-bold text-ink-900">
                  Ofertas con mayor afinidad
                </h2>
                <Link
                  to="/jobs"
                  className="text-sm font-medium text-brand-600 hover:underline"
                >
                  Ver todas
                </Link>
              </div>

              {loading && (
                <p className="text-ink-500">Buscando oportunidades...</p>
              )}
              {error && <p className="text-red-600">{error}</p>}
              {ofertas?.length === 0 && (
                <p className="text-ink-500">
                  No hay ofertas recomendadas todavía.
                </p>
              )}

              <div className="space-y-4">
                {ofertas?.slice(0, 5).map((oferta) => (
                  <JobCardView key={oferta.id} oferta={oferta} />
                ))}
              </div>
            </section>

            <RightPanelView
              userId={user.entidad_id}
              onCambio={() => setVersionRed((v) => v + 1)}
            />
          </div>
        </div>
      )}
    </ShellView>
  );
}
