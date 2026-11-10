import { useState } from "react";
import { Plus } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";
import BorrarConfirmadoView from "./BorrarConfirmadoView";

const ETIQUETAS = { nombre: "Nombre", descripcion: "Descripción" };

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

// proyecto = null para crear uno nuevo.
function ProyectoForm({ proyecto, onGuardado, onCancelar }) {
  const [nombre, setNombre] = useState(proyecto?.nombre ?? "");
  const [descripcion, setDescripcion] = useState(proyecto?.descripcion ?? "");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const cuerpo = { nombre, descripcion };
      const res = proyecto
        ? await api.put(`/api/admin/projects/${proyecto.id}`, cuerpo)
        : await api.post("/api/admin/projects", cuerpo);
      onGuardado(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo guardar el proyecto"));
      setOcupado(false);
    }
  };

  return (
    <form
      onSubmit={enviar}
      className="space-y-4 rounded-2xl border border-brand-100 bg-white p-5 shadow-sm"
    >
      <h3 className="font-semibold text-ink-900">
        {proyecto ? "Editar proyecto" : "Nuevo proyecto"}
      </h3>
      <input
        required
        maxLength={140}
        placeholder="Nombre del proyecto"
        aria-label="Nombre"
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
        className={campo}
      />
      <textarea
        rows={3}
        maxLength={600}
        placeholder="Descripción (opcional)"
        aria-label="Descripción"
        value={descripcion}
        onChange={(e) => setDescripcion(e.target.value)}
        className={campo}
      />
      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={ocupado}
          className="rounded-xl bg-brand-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
        >
          {ocupado ? "Guardando..." : "Guardar"}
        </button>
        <button
          type="button"
          onClick={onCancelar}
          disabled={ocupado}
          className="rounded-xl border border-ink-100 px-5 py-2 text-sm font-semibold text-ink-700 transition hover:bg-ink-100"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}

export default function AdminProjectsView() {
  const { data, loading, error: errorCarga } = useFetch("/api/admin/projects");
  const [lista, setLista] = useState(null);
  const [formulario, setFormulario] = useState(null); // null | "nuevo" | proyecto
  const [error, setError] = useState("");

  const proyectos = lista ?? data ?? [];

  const eliminar = async (p) => {
    setError("");
    try {
      const res = await api.delete(`/api/admin/projects/${p.id}`);
      setLista(res.data.data);
      if (formulario?.id === p.id) setFormulario(null);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo eliminar el proyecto"));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-500">
          {proyectos.length} proyectos. Eliminar uno quita la participación de
          sus miembros, no a las personas.
        </p>
        {!formulario && (
          <button
            onClick={() => setFormulario("nuevo")}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Nuevo proyecto
          </button>
        )}
      </div>

      {formulario && (
        <ProyectoForm
          key={formulario === "nuevo" ? "nuevo" : formulario.id}
          proyecto={formulario === "nuevo" ? null : formulario}
          onGuardado={(nueva) => {
            setLista(nueva);
            setFormulario(null);
          }}
          onCancelar={() => setFormulario(null)}
        />
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}
      {loading && <p className="text-sm text-ink-500">Cargando proyectos...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}

      <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-ink-100/60 text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th className="px-4 py-2.5 font-semibold">Proyecto</th>
              <th className="px-4 py-2.5 font-semibold">Miembros</th>
              <th className="px-4 py-2.5 font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {proyectos.map((p) => (
              <tr key={p.id} className="align-middle">
                <td className="px-4 py-2.5">
                  <p className="font-medium text-ink-900">{p.nombre}</p>
                  {p.descripcion && (
                    <p className="line-clamp-1 text-xs text-ink-500">
                      {p.descripcion}
                    </p>
                  )}
                </td>
                <td className="px-4 py-2.5 text-ink-700">{p.miembros}</td>
                <td className="px-4 py-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => setFormulario(p)}
                      className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                    >
                      Editar
                    </button>
                    <BorrarConfirmadoView onConfirmar={() => eliminar(p)} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
