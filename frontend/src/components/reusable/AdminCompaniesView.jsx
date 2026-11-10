import { useState } from "react";
import { Plus } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";
import { Formulario as FormularioEmpresa } from "../main_views/CompanyProfileView";
import BorrarConfirmadoView from "./BorrarConfirmadoView";

const ETIQUETAS = {
  nombre: "Nombre",
  correo: "Correo",
  password: "Contraseña",
  sector: "Sector",
};

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function EditorEmpresa({ companyId, onCerrar }) {
  const {
    data: perfil,
    loading,
    error,
  } = useFetch(`/api/companies/${companyId}/profile`);
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-ink-900">Editar empresa</h3>
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
        <FormularioEmpresa
          key={companyId}
          perfil={perfil}
          companyId={companyId}
        />
      )}
    </div>
  );
}

function NuevaEmpresaForm({ onCreada, onCancelar }) {
  const [v, setV] = useState({
    nombre: "",
    correo: "",
    password: "",
    sector: "",
  });
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const cambiar = (k, valor) => setV((x) => ({ ...x, [k]: valor }));

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.post("/api/admin/companies", v);
      onCreada(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo crear la empresa"));
      setOcupado(false);
    }
  };

  return (
    <form
      onSubmit={enviar}
      className="space-y-4 rounded-2xl border border-brand-100 bg-white p-5 shadow-sm"
    >
      <h3 className="font-semibold text-ink-900">Nueva empresa</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          required
          maxLength={140}
          placeholder="Nombre de la empresa"
          aria-label="Nombre"
          value={v.nombre}
          onChange={(e) => cambiar("nombre", e.target.value)}
          className={campo}
        />
        <input
          required
          maxLength={120}
          placeholder="Sector"
          aria-label="Sector"
          value={v.sector}
          onChange={(e) => cambiar("sector", e.target.value)}
          className={campo}
        />
        <input
          required
          type="email"
          maxLength={254}
          placeholder="Correo de acceso"
          aria-label="Correo"
          value={v.correo}
          onChange={(e) => cambiar("correo", e.target.value)}
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
          {ocupado ? "Creando..." : "Crear empresa"}
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

export default function AdminCompaniesView() {
  const { data, loading, error: errorCarga } = useFetch("/api/admin/companies");
  const [lista, setLista] = useState(null);
  const [editando, setEditando] = useState(null);
  const [creando, setCreando] = useState(false);
  const [error, setError] = useState("");

  const empresas = lista ?? data ?? [];

  const recargar = async () => {
    try {
      const res = await api.get("/api/admin/companies");
      setLista(res.data.data);
    } catch {
      /* la lista anterior sigue siendo válida */
    }
  };

  const eliminar = async (e) => {
    setError("");
    try {
      const res = await api.delete(`/api/admin/companies/${e.id}`);
      setLista(res.data.data);
      if (editando === e.id) setEditando(null);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo eliminar la empresa"));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-500">
          {empresas.length} empresas. Eliminar una borra también sus ofertas y
          las postulaciones recibidas.
        </p>
        {!creando && (
          <button
            onClick={() => setCreando(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Nueva empresa
          </button>
        )}
      </div>

      {creando && (
        <NuevaEmpresaForm
          onCreada={(nueva) => {
            setLista(nueva);
            setCreando(false);
          }}
          onCancelar={() => setCreando(false)}
        />
      )}

      {editando && (
        <EditorEmpresa
          key={editando}
          companyId={editando}
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
      {loading && <p className="text-sm text-ink-500">Cargando empresas...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}

      <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-ink-100/60 text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th className="px-4 py-2.5 font-semibold">Empresa</th>
              <th className="px-4 py-2.5 font-semibold">Sector</th>
              <th className="px-4 py-2.5 font-semibold">Ofertas</th>
              <th className="px-4 py-2.5 font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {empresas.map((e) => (
              <tr key={e.id} className="align-middle">
                <td className="px-4 py-2.5">
                  <p className="font-medium text-ink-900">{e.nombre}</p>
                  <p className="text-xs text-ink-500">{e.correo}</p>
                </td>
                <td className="px-4 py-2.5 text-ink-700">{e.sector || "—"}</td>
                <td className="px-4 py-2.5 text-ink-700">{e.ofertas}</td>
                <td className="px-4 py-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => setEditando(e.id)}
                      className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                    >
                      Editar
                    </button>
                    <BorrarConfirmadoView onConfirmar={() => eliminar(e)} />
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
