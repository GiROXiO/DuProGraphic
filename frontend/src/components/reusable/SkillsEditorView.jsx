import { useState } from "react";
import { Plus, X } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";

// Deben coincidir exactamente con los valores que acepta el backend.
const NIVELES = ["básico", "intermedio", "avanzado"];

const select =
  "rounded-lg border border-ink-100 bg-white px-2 py-1.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

export default function SkillsEditorView({ userId }) {
  const {
    data: inicial,
    loading,
    error: errorCarga,
  } = useFetch(`/api/users/${userId}/skills`);
  const {
    data: catalogo,
    loading: cargandoCatalogo,
    error: errorCatalogo,
    refetch: recargarCatalogo,
  } = useFetch("/api/skills");

  // La lista local reemplaza a la inicial después de cada cambio (el backend devuelve la lista nueva).
  const [lista, setLista] = useState(null);
  const [ocupada, setOcupada] = useState(null);
  const [error, setError] = useState("");
  const [nuevaId, setNuevaId] = useState("");
  const [nuevoNivel, setNuevoNivel] = useState("básico");

  const actuales = lista ?? inicial ?? [];
  const disponibles = (catalogo ?? []).filter(
    (h) => !actuales.some((a) => a.id === h.id),
  );

  const ejecutar = async (clave, peticion) => {
    setError("");
    setOcupada(clave);
    try {
      const res = await peticion();
      setLista(res.data.data);
      return true;
    } catch (err) {
      setError(
        err.response?.data?.detail || "No se pudo actualizar la habilidad.",
      );
      return false;
    } finally {
      setOcupada(null);
    }
  };

  const guardar = (id, nivel) =>
    ejecutar(id, () => api.put(`/api/users/${userId}/skills/${id}`, { nivel }));

  const quitar = (id) =>
    ejecutar(id, () => api.delete(`/api/users/${userId}/skills/${id}`));

  const agregar = async (e) => {
    e.preventDefault();
    if (!nuevaId) return;
    if (await guardar(nuevaId, nuevoNivel)) {
      setNuevaId("");
      setNuevoNivel("básico");
    }
  };

  return (
    <section className="space-y-5 rounded-2xl border border-ink-100 bg-white p-6">
      <div>
        <h2 className="text-lg font-bold text-ink-900">Lo que sabes hacer</h2>
        <p className="mt-1 text-sm text-ink-500">
          Tus habilidades determinan qué ofertas te recomendamos y a cuántos
          saltos estás de ellas.
        </p>
      </div>

      {loading && (
        <p className="text-sm text-ink-500">Cargando habilidades...</p>
      )}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}
      {cargandoCatalogo && (
        <p className="text-sm text-ink-500">Cargando catálogo de habilidades...</p>
      )}
      {errorCatalogo && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          <span>No se pudo cargar el catálogo; no es posible añadir habilidades por ahora.</span>
          <button
            type="button"
            onClick={recargarCatalogo}
            className="font-semibold underline"
          >
            Reintentar
          </button>
        </div>
      )}
      {!cargandoCatalogo && !errorCatalogo && catalogo?.length === 0 && (
        <p className="text-sm text-ink-500">
          No hay habilidades disponibles en el catálogo.
        </p>
      )}

      {!loading && !errorCarga && actuales.length === 0 && (
        <p className="text-sm text-ink-500">
          Aún no has añadido habilidades. Agrega la primera para recibir mejores
          recomendaciones.
        </p>
      )}

      <ul className="space-y-2">
        {actuales.map((h) => (
          <li
            key={h.id}
            className="flex flex-wrap items-center gap-3 rounded-xl border border-ink-100 px-4 py-2.5"
          >
            <div className="min-w-0 flex-1">
              <p className="font-medium text-ink-900">{h.nombre}</p>
              {h.categoria && (
                <p className="text-xs text-ink-500">{h.categoria}</p>
              )}
            </div>
            <select
              aria-label={`Nivel de ${h.nombre}`}
              value={h.nivel}
              disabled={ocupada === h.id}
              onChange={(e) => guardar(h.id, e.target.value)}
              className={select}
            >
              {NIVELES.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => quitar(h.id)}
              disabled={ocupada === h.id}
              title={`Quitar ${h.nombre}`}
              className="rounded-lg p-1.5 text-ink-300 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            >
              <X className="h-4 w-4" />
            </button>
          </li>
        ))}
      </ul>

      {disponibles.length > 0 ? (
        <form
          onSubmit={agregar}
          className="flex flex-wrap items-center gap-3 border-t border-ink-100 pt-5"
        >
          <select
            aria-label="Habilidad a añadir"
            value={nuevaId}
            onChange={(e) => setNuevaId(e.target.value)}
            className={`${select} min-w-0 flex-1`}
          >
            <option value="">Elegir habilidad...</option>
            {disponibles.map((h) => (
              <option key={h.id} value={h.id}>
                {h.nombre}
                {h.categoria ? ` · ${h.categoria}` : ""}
              </option>
            ))}
          </select>
          <select
            aria-label="Nivel de la nueva habilidad"
            value={nuevoNivel}
            onChange={(e) => setNuevoNivel(e.target.value)}
            className={select}
          >
            {NIVELES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!nuevaId || ocupada === nuevaId}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Plus className="h-4 w-4" />
            Añadir
          </button>
        </form>
      ) : (
        catalogo?.length > 0 && (
          <p className="border-t border-ink-100 pt-5 text-sm text-ink-500">
            Ya añadiste todas las habilidades del catálogo.
          </p>
        )
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}
    </section>
  );
}
