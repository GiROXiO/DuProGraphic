import { useState } from "react";
import ShellView from "../nav_layout/ShellView";
import OfferFormView from "../reusable/OfferFormView";
import api, { getUser } from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

export default function OffersView() {
  const user = getUser();
  const esEmpresa = user?.rol === "empresa" && user?.entidad_id;
  const { data, loading, error } = useFetch(
    esEmpresa ? `/api/companies/${user.entidad_id}/offers` : null,
  );

  // Tras cada cambio la API devuelve la lista completa y reemplaza a la inicial.
  const [lista, setLista] = useState(null);
  const [editando, setEditando] = useState(null); // null | "nueva" | id de oferta
  const [ocupada, setOcupada] = useState(null);
  const [errorAccion, setErrorAccion] = useState("");

  const ofertas = lista ?? data ?? [];
  const oferta =
    editando && editando !== "nueva"
      ? ofertas.find((o) => o.id === editando)
      : null;

  const cambiarEstado = async (o) => {
    const abierta = o.estado?.toLowerCase() === "abierta";
    setErrorAccion("");
    setOcupada(o.id);
    try {
      const res = await api.put(
        `/api/companies/${user.entidad_id}/offers/${o.id}/status`,
        { estado: abierta ? "cerrada" : "abierta" },
      );
      setLista(res.data.data);
    } catch (err) {
      setErrorAccion(mensajeError(err, {}, "No se pudo cambiar el estado"));
    } finally {
      setOcupada(null);
    }
  };

  return (
    <ShellView>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">
            Mis ofertas
          </h1>
          <p className="mt-1 text-sm text-ink-500">
            Publica vacantes y define las habilidades que requieren. Los
            usuarios las verán ordenadas por afinidad.
          </p>
        </div>
        {esEmpresa && editando === null && (
          <button
            onClick={() => setEditando("nueva")}
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700"
          >
            Nueva oferta
          </button>
        )}
      </header>

      {!esEmpresa ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          La gestión de ofertas es para cuentas de empresa.
        </div>
      ) : (
        <div className="space-y-6">
          {editando !== null && (
            <OfferFormView
              key={editando}
              companyId={user.entidad_id}
              oferta={oferta}
              onGuardada={(nuevaLista) => {
                setLista(nuevaLista);
                setEditando(null);
              }}
              onCancelar={() => setEditando(null)}
            />
          )}

          {loading && <p className="text-ink-500">Cargando tus ofertas...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {errorAccion && (
            <div
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
              {errorAccion}
            </div>
          )}
          {!loading && !error && ofertas.length === 0 && (
            <p className="rounded-2xl border border-ink-100 bg-white p-6 text-ink-500">
              Aún no has publicado ofertas. Pulsa "Nueva oferta" para crear la
              primera.
            </p>
          )}

          <div className="space-y-4">
            {ofertas.map((o) => {
              const abierta = o.estado?.toLowerCase() === "abierta";
              return (
                <article
                  key={o.id}
                  className="rounded-2xl border border-ink-100 bg-white p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold text-ink-900">{o.titulo}</h2>
                      <p className="mt-0.5 text-xs capitalize text-ink-500">
                        {[o.modalidad, o.experiencia]
                          .filter(Boolean)
                          .join(" · ")}
                        {` · ${o.postulaciones} ${o.postulaciones === 1 ? "postulación" : "postulaciones"}`}
                      </p>
                    </div>
                    <span
                      className={`rounded-lg px-3 py-1 text-xs font-semibold ${
                        abierta
                          ? "bg-signal-50 text-signal-600"
                          : "bg-ink-100 text-ink-500"
                      }`}
                    >
                      {abierta ? "Abierta" : "Cerrada"}
                    </span>
                  </div>

                  {o.descripcion && (
                    <p className="mt-3 whitespace-pre-line text-sm text-ink-700">
                      {o.descripcion}
                    </p>
                  )}

                  {o.habilidades_detalle?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {o.habilidades_detalle.map((h) => (
                        <span
                          key={h.id}
                          className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                            h.obligatoria
                              ? "bg-signal-50 text-signal-600"
                              : "border border-dashed border-ink-300 text-ink-500"
                          }`}
                          title={h.obligatoria ? "Obligatoria" : "Opcional"}
                        >
                          {h.nombre}
                          {!h.obligatoria && " (opcional)"}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      onClick={() => setEditando(o.id)}
                      disabled={editando !== null}
                      className="rounded-xl border border-ink-100 px-4 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100 disabled:opacity-50"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => cambiarEstado(o)}
                      disabled={ocupada === o.id}
                      className="rounded-xl border border-ink-100 px-4 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100 disabled:opacity-50"
                    >
                      {abierta ? "Cerrar oferta" : "Reabrir oferta"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}
    </ShellView>
  );
}
