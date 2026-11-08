import { useState } from "react";
import ShellView from "../nav_layout/ShellView";
import api, { getToken, getUser, saveSession } from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

const TAMANOS = [
  "1-10 personas",
  "11-50 personas",
  "51-200 personas",
  "201-1000 personas",
  "Más de 1000 personas",
];

const ETIQUETAS = {
  nombre: "Nombre",
  sector: "Sector",
  descripcion: "Descripción",
  ubicacion: "Ubicación",
  tamano: "Tamaño",
  sitio_web: "Sitio web",
};

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function Formulario({ perfil, companyId }) {
  const [v, setV] = useState({
    nombre: perfil.nombre ?? "",
    sector: perfil.sector ?? "",
    descripcion: perfil.descripcion ?? "",
    ubicacion: perfil.ubicacion ?? "",
    tamano: perfil.tamano ?? "",
    sitio_web: perfil.sitio_web ?? "",
  });
  const [guardando, setGuardando] = useState(false);
  const [guardado, setGuardado] = useState(false);
  const [error, setError] = useState("");

  const cambiar = (nombre, valor) => {
    setV((x) => ({ ...x, [nombre]: valor }));
    setGuardado(false);
  };

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setGuardado(false);
    setGuardando(true);
    try {
      const res = await api.put(`/api/companies/${companyId}/profile`, {
        ...v,
        tamano: v.tamano || null,
      });
      // Mantiene el nombre de la sesión al día (lo muestra la barra lateral).
      const token = getToken();
      const usuario = getUser();
      if (token && usuario) {
        saveSession(token, { ...usuario, nombre: res.data.data.nombre });
      }
      setGuardado(true);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo guardar el perfil"));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <form
      onSubmit={enviar}
      className="space-y-5 rounded-2xl border border-ink-100 bg-white p-6"
    >
      <div>
        <h2 className="text-lg font-bold text-ink-900">
          Perfil público de la organización
        </h2>
        <p className="mt-1 text-sm text-ink-500">
          Esta información la ven las personas que consultan tu empresa.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div>
          <label
            htmlFor="e-nombre"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Nombre <span className="text-red-500">*</span>
          </label>
          <input
            id="e-nombre"
            required
            maxLength={140}
            value={v.nombre}
            onChange={(e) => cambiar("nombre", e.target.value)}
            className={campo}
          />
        </div>
        <div>
          <label
            htmlFor="e-sector"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Sector <span className="text-red-500">*</span>
          </label>
          <input
            id="e-sector"
            required
            maxLength={120}
            value={v.sector}
            onChange={(e) => cambiar("sector", e.target.value)}
            className={campo}
          />
        </div>
        <div className="md:col-span-2">
          <label
            htmlFor="e-desc"
            className="mb-1.5 flex justify-between text-sm font-medium text-ink-700"
          >
            <span>Descripción</span>
            <span className="text-xs font-normal text-ink-300">
              {v.descripcion.length}/1200
            </span>
          </label>
          <textarea
            id="e-desc"
            rows={4}
            maxLength={1200}
            value={v.descripcion}
            onChange={(e) => cambiar("descripcion", e.target.value)}
            placeholder="A qué se dedica tu organización."
            className={campo}
          />
        </div>
        <div>
          <label
            htmlFor="e-ubi"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Ciudad o ubicación
          </label>
          <input
            id="e-ubi"
            maxLength={120}
            value={v.ubicacion}
            onChange={(e) => cambiar("ubicacion", e.target.value)}
            className={campo}
          />
        </div>
        <div>
          <label
            htmlFor="e-tam"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Tamaño de la organización
          </label>
          <select
            id="e-tam"
            value={v.tamano}
            onChange={(e) => cambiar("tamano", e.target.value)}
            className={campo}
          >
            <option value="">Sin especificar</option>
            {TAMANOS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <label
            htmlFor="e-web"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Sitio web
          </label>
          <input
            id="e-web"
            type="url"
            maxLength={240}
            value={v.sitio_web}
            onChange={(e) => cambiar("sitio_web", e.target.value)}
            placeholder="https://..."
            className={campo}
          />
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={guardando}
          className="rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {guardando ? "Guardando..." : "Guardar perfil"}
        </button>
        {guardado && (
          <span className="text-sm font-medium text-signal-600">
            ✓ Perfil actualizado
          </span>
        )}
      </div>
    </form>
  );
}

export default function CompanyProfileView() {
  const user = getUser();
  const esEmpresa = user?.rol === "empresa" && user?.entidad_id;
  const {
    data: perfil,
    loading,
    error,
  } = useFetch(esEmpresa ? `/api/companies/${user.entidad_id}/profile` : null);

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Perfil de empresa
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Edita la información de tu organización.
        </p>
      </header>

      {!esEmpresa ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          El perfil de empresa es para cuentas de empresa.
        </div>
      ) : (
        <>
          {loading && <p className="text-ink-500">Cargando el perfil...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {perfil && <Formulario perfil={perfil} companyId={user.entidad_id} />}
        </>
      )}
    </ShellView>
  );
}
