import { useState } from "react";
import { Plus } from "lucide-react";
import api, { getUser } from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";
import ProfileFormView from "./ProfileFormView";
import BorrarConfirmadoView from "./BorrarConfirmadoView";

const ETIQUETAS = {
  nombre: "Nombre",
  correo: "Correo",
  password: "Contraseña",
  perfil_profesional: "Titular profesional",
  universidad: "Universidad",
  es_admin: "Permiso",
};

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function EditorPerfil({ userId, onCerrar }) {
  const {
    data: perfil,
    loading,
    error,
  } = useFetch(`/api/users/${userId}/profile`);
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-ink-900">Editar perfil</h3>
        <button
          onClick={onCerrar}
          className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
        >
          Cerrar
        </button>
      </div>
      {loading && <p className="text-sm text-ink-500">Cargando perfil...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {perfil && (
        <ProfileFormView key={userId} perfil={perfil} userId={userId} />
      )}
    </div>
  );
}

function NuevoUsuarioForm({ onCreado, onCancelar }) {
  const [v, setV] = useState({
    nombre: "",
    correo: "",
    password: "",
    perfil_profesional: "",
    universidad: "",
  });
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const cambiar = (k, valor) => setV((x) => ({ ...x, [k]: valor }));

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.post("/api/admin/users", {
        ...v,
        universidad: v.universidad || null,
      });
      onCreado(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo crear el usuario"));
      setOcupado(false);
    }
  };

  return (
    <form
      onSubmit={enviar}
      className="space-y-4 rounded-2xl border border-brand-100 bg-white p-5 shadow-sm"
    >
      <h3 className="font-semibold text-ink-900">Nuevo usuario</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          required
          maxLength={140}
          placeholder="Nombre completo"
          aria-label="Nombre"
          value={v.nombre}
          onChange={(e) => cambiar("nombre", e.target.value)}
          className={campo}
        />
        <input
          required
          type="email"
          maxLength={254}
          placeholder="Correo"
          aria-label="Correo"
          value={v.correo}
          onChange={(e) => cambiar("correo", e.target.value)}
          className={campo}
        />
        <input
          required
          maxLength={180}
          placeholder="Titular profesional"
          aria-label="Titular profesional"
          value={v.perfil_profesional}
          onChange={(e) => cambiar("perfil_profesional", e.target.value)}
          className={campo}
        />
        <input
          maxLength={160}
          placeholder="Universidad (opcional)"
          aria-label="Universidad"
          value={v.universidad}
          onChange={(e) => cambiar("universidad", e.target.value)}
          className={campo}
        />
        <input
          required
          type="password"
          minLength={10}
          maxLength={256}
          autoComplete="new-password"
          placeholder="Contraseña inicial (mín. 10)"
          aria-label="Contraseña"
          value={v.password}
          onChange={(e) => cambiar("password", e.target.value)}
          className={campo}
        />
      </div>
      <p className="text-xs text-ink-500">
        Comparte la contraseña con la persona por un canal seguro. El resto del
        perfil lo completa ella o puedes editarlo después.
      </p>
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
          {ocupado ? "Creando..." : "Crear usuario"}
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

export default function AdminUsersView() {
  const yo = getUser();
  const { data, loading, error: errorCarga } = useFetch("/api/admin/users");
  const [lista, setLista] = useState(null);
  const [editando, setEditando] = useState(null);
  const [creando, setCreando] = useState(false);
  const [ocupado, setOcupado] = useState(null);
  const [error, setError] = useState("");

  const usuarios = lista ?? data ?? [];

  const recargar = async () => {
    try {
      const res = await api.get("/api/admin/users");
      setLista(res.data.data);
    } catch {
      /* la lista anterior sigue siendo válida */
    }
  };

  const alternarAdmin = async (u) => {
    setError("");
    setOcupado(u.id);
    try {
      const res = await api.put(`/api/admin/users/${u.id}/admin`, {
        es_admin: !u.es_admin,
      });
      setLista(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo cambiar el permiso"));
    } finally {
      setOcupado(null);
    }
  };

  const eliminar = async (u) => {
    setError("");
    try {
      const res = await api.delete(`/api/admin/users/${u.id}`);
      setLista(res.data.data);
      if (editando === u.id) setEditando(null);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo eliminar el usuario"));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-500">
          {usuarios.length} usuarios. Eliminar uno borra su perfil, sus
          relaciones del grafo y su acceso.
        </p>
        {!creando && (
          <button
            onClick={() => setCreando(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Nuevo usuario
          </button>
        )}
      </div>

      {creando && (
        <NuevoUsuarioForm
          onCreado={(nueva) => {
            setLista(nueva);
            setCreando(false);
          }}
          onCancelar={() => setCreando(false)}
        />
      )}

      {editando && (
        <EditorPerfil
          key={editando}
          userId={editando}
          onCerrar={() => {
            setEditando(null);
            recargar();
          }}
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
      {loading && <p className="text-sm text-ink-500">Cargando usuarios...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}

      <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-ink-100/60 text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th className="px-4 py-2.5 font-semibold">Usuario</th>
              <th className="px-4 py-2.5 font-semibold">Titular</th>
              <th className="px-4 py-2.5 font-semibold">Permiso</th>
              <th className="px-4 py-2.5 font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {usuarios.map((u) => {
              const esYo = u.id === yo?.entidad_id;
              return (
                <tr key={u.id} className="align-middle">
                  <td className="px-4 py-2.5">
                    <p className="font-medium text-ink-900">
                      {u.nombre}
                      {esYo && (
                        <span className="ml-2 rounded-md bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">
                          Tú
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-ink-500">{u.correo}</p>
                  </td>
                  <td className="px-4 py-2.5 text-ink-700">
                    {u.titular || "—"}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-md px-2 py-0.5 text-xs font-semibold ${u.es_admin ? "bg-signal-50 text-signal-600" : "bg-ink-100 text-ink-500"}`}
                    >
                      {u.es_admin ? "Administrador" : "Usuario"}
                    </span>
                    {!u.activa && (
                      <span className="ml-2 text-xs text-red-600">
                        sin acceso
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => setEditando(u.id)}
                        className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => alternarAdmin(u)}
                        disabled={
                          ocupado === u.id || !u.activa || (esYo && u.es_admin)
                        }
                        title={
                          esYo && u.es_admin
                            ? "No puedes quitarte tu propio permiso"
                            : undefined
                        }
                        className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {u.es_admin ? "Quitar admin" : "Hacer admin"}
                      </button>
                      <BorrarConfirmadoView
                        onConfirmar={() => eliminar(u)}
                        deshabilitado={esYo}
                        titulo={
                          esYo
                            ? "No puedes eliminar tu propia cuenta"
                            : undefined
                        }
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
