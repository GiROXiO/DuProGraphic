import { useState } from "react";
import { Plus } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

const ETIQUETAS = { rol: "Rol" };

const campo =
  "w-full rounded-lg border border-ink-100 bg-white px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function FilaProyecto({ item, userId, onLista }) {
  const [editando, setEditando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [rol, setRol] = useState(item.rol ?? "");

  const guardar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.put(`/api/users/${userId}/projects/${item.id}`, {
        rol,
      });
      onLista(res.data.data);
      setEditando(false);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo guardar"));
    } finally {
      setOcupado(false);
    }
  };

  const quitar = async () => {
    setError("");
    setOcupado(true);
    try {
      const res = await api.delete(`/api/users/${userId}/projects/${item.id}`);
      onLista(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo quitar"));
      setOcupado(false);
      setConfirmando(false);
    }
  };

  return (
    <li className="rounded-xl border border-ink-100 px-4 py-3">
      {editando ? (
        <form onSubmit={guardar} className="space-y-3">
          <p className="text-sm font-semibold text-ink-900">{item.nombre}</p>
          <input
            required
            maxLength={120}
            value={rol}
            onChange={(e) => setRol(e.target.value)}
            placeholder="Tu rol o contribución"
            aria-label="Rol"
            className={campo}
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={ocupado}
              className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
            >
              {ocupado ? "Guardando..." : "Guardar"}
            </button>
            <button
              type="button"
              onClick={() => setEditando(false)}
              disabled={ocupado}
              className="rounded-lg border border-ink-100 px-4 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-ink-900">{item.nombre}</p>
            <p className="text-xs text-ink-500">{item.rol || "Participante"}</p>
            {item.descripcion && (
              <p className="mt-1 line-clamp-2 text-xs text-ink-300">
                {item.descripcion}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {confirmando ? (
              <>
                <span className="text-xs text-ink-500">¿Quitar?</span>
                <button
                  onClick={quitar}
                  disabled={ocupado}
                  className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
                >
                  {ocupado ? "Quitando..." : "Sí, quitar"}
                </button>
                <button
                  onClick={() => setConfirmando(false)}
                  disabled={ocupado}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                >
                  No
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setEditando(true)}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                >
                  Editar rol
                </button>
                <button
                  onClick={() => setConfirmando(true)}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-500 transition hover:bg-red-50 hover:text-red-600"
                >
                  Quitar
                </button>
              </>
            )}
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </li>
  );
}

export default function ProjectsEditorView({ userId }) {
  const {
    data: inicial,
    loading,
    error: errorCarga,
  } = useFetch(`/api/users/${userId}/projects`);
  const {
    data: catalogo,
    loading: cargandoCatalogo,
    error: errorCatalogo,
    refetch: recargarCatalogo,
  } = useFetch("/api/projects");

  // Tras cada cambio la API devuelve la lista completa y reemplaza a la inicial.
  const [lista, setLista] = useState(null);
  const [proyectoId, setProyectoId] = useState("");
  const [rol, setRol] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const actuales = lista ?? inicial ?? [];
  const disponibles = (catalogo ?? []).filter(
    (p) => !actuales.some((a) => a.id === p.id),
  );

  const agregar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.put(`/api/users/${userId}/projects/${proyectoId}`, {
        rol,
      });
      setLista(res.data.data);
      setProyectoId("");
      setRol("");
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo añadir el proyecto"));
    } finally {
      setOcupado(false);
    }
  };

  return (
    <section className="space-y-5 rounded-2xl border border-ink-100 bg-white p-6">
      <div>
        <h2 className="text-lg font-bold text-ink-900">Proyectos</h2>
        <p className="mt-1 text-sm text-ink-500">
          Los proyectos en los que participas te conectan con otras personas y
          con las tecnologías que usan.
        </p>
      </div>

      {loading && <p className="text-sm text-ink-500">Cargando...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}
      {cargandoCatalogo && (
        <p className="text-sm text-ink-500">Cargando proyectos disponibles...</p>
      )}
      {errorCatalogo && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          <span>No se pudo cargar el catálogo; no es posible añadir proyectos por ahora.</span>
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
          No hay proyectos disponibles en el catálogo.
        </p>
      )}
      {!loading && !errorCarga && actuales.length === 0 && (
        <p className="text-sm text-ink-500">
          Aún no participas en ningún proyecto.
        </p>
      )}

      <ul className="space-y-2">
        {actuales.map((item) => (
          <FilaProyecto
            key={item.id}
            item={item}
            userId={userId}
            onLista={setLista}
          />
        ))}
      </ul>

      {disponibles.length > 0 ? (
        <form
          onSubmit={agregar}
          className="space-y-3 border-t border-ink-100 pt-5"
        >
          <p className="text-sm font-medium text-ink-700">Añadir un proyecto</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <select
              required
              value={proyectoId}
              onChange={(e) => setProyectoId(e.target.value)}
              aria-label="Proyecto"
              className={campo}
            >
              <option value="">Elegir proyecto...</option>
              {disponibles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
            <input
              required
              maxLength={120}
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              placeholder="Tu rol o contribución"
              aria-label="Rol en el nuevo proyecto"
              className={campo}
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={ocupado || !proyectoId}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              {ocupado ? "Añadiendo..." : "Añadir"}
            </button>
          </div>
        </form>
      ) : (
        catalogo?.length > 0 && (
          <p className="border-t border-ink-100 pt-5 text-sm text-ink-500">
            Ya participas en todos los proyectos disponibles.
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
