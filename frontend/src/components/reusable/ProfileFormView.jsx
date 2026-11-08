import { useState } from "react";
import api, { getToken, getUser, saveSession } from "../../api";

// Campos de texto editables. "max" coincide con los límites del backend.
const CAMPOS = [
  { name: "nombre", label: "Nombre", max: 140, required: true },
  {
    name: "perfil_profesional",
    label: "Titular profesional",
    max: 180,
    required: true,
    placeholder: "Ej. Desarrolladora backend | Python y Neo4j",
  },
  {
    name: "acerca_de",
    label: "Acerca de",
    max: 1200,
    textarea: true,
    rows: 4,
    ancho: true,
    placeholder:
      "Cuenta qué sabes hacer, qué has construido y qué colaboración buscas.",
  },
  { name: "ubicacion", label: "Ciudad o región", max: 120 },
  {
    name: "areas_interes",
    label: "Áreas de interés",
    max: 180,
    placeholder: "Ej. Datos, educación, energía",
  },
  { name: "universidad", label: "Institución", max: 160 },
  { name: "educacion_detalle", label: "Programa o formación", max: 160 },
  {
    name: "experiencia",
    label: "Experiencia y objetivos",
    max: 1400,
    textarea: true,
    rows: 4,
    ancho: true,
  },
  {
    name: "idiomas",
    label: "Idiomas",
    max: 180,
    placeholder: "Ej. Español nativo, inglés B2",
  },
  {
    name: "sitio_portafolio",
    label: "Portafolio o sitio profesional",
    max: 240,
    type: "url",
    placeholder: "https://...",
  },
  {
    name: "logros",
    label: "Logros destacados",
    max: 700,
    textarea: true,
    rows: 3,
    ancho: true,
  },
];

const MODALIDADES = [
  { value: "", label: "Sin preferencia" },
  { value: "remoto", label: "Remoto" },
  { value: "híbrido", label: "Híbrido" },
  { value: "presencial", label: "Presencial" },
];

const input =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

// Convierte los errores de FastAPI (texto o lista de validaciones) en un mensaje legible.
function mensajeError(err) {
  const detalle = err.response?.data?.detail;
  if (Array.isArray(detalle)) {
    return detalle
      .map((d) => {
        const campo = CAMPOS.find((c) => c.name === d.loc?.at(-1));
        const texto = String(d.msg).replace(/^Value error, /, "");
        return `${campo?.label ?? d.loc?.at(-1) ?? "Dato"}: ${texto}`;
      })
      .join(". ");
  }
  return detalle || "No se pudieron guardar los cambios.";
}

export default function ProfileFormView({ perfil, userId }) {
  const [valores, setValores] = useState(() => ({
    ...Object.fromEntries(CAMPOS.map((c) => [c.name, perfil[c.name] ?? ""])),
    anios_experiencia: perfil.anios_experiencia ?? 0,
    modalidad_preferida: perfil.modalidad_preferida ?? "",
  }));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [guardado, setGuardado] = useState(false);

  const cambiar = (name, valor) => {
    setValores((v) => ({ ...v, [name]: valor }));
    setGuardado(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setGuardado(false);
    setGuardando(true);
    try {
      const res = await api.put(`/api/users/${userId}/profile`, {
        ...valores,
        anios_experiencia: Number(valores.anios_experiencia) || 0,
        modalidad_preferida: valores.modalidad_preferida || null,
      });
      // Mantiene el nombre de la sesión al día (lo muestra la barra lateral).
      const token = getToken();
      const usuario = getUser();
      if (token && usuario) {
        saveSession(token, { ...usuario, nombre: res.data.data.nombre });
      }
      setGuardado(true);
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-2xl border border-ink-100 bg-white p-6"
    >
      <div>
        <h2 className="text-lg font-bold text-ink-900">
          Presentación profesional
        </h2>
        <p className="mt-1 text-sm text-ink-500">
          Una descripción concreta mejora tus recomendaciones y ayuda a otras
          personas a entender qué haces.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {CAMPOS.map((c) => {
          const valor = valores[c.name];
          return (
            <div key={c.name} className={c.ancho ? "md:col-span-2" : ""}>
              <label
                htmlFor={c.name}
                className="mb-1.5 flex justify-between text-sm font-medium text-ink-700"
              >
                <span>
                  {c.label}
                  {c.required && <span className="text-red-500"> *</span>}
                </span>
                {c.textarea && (
                  <span className="text-xs font-normal text-ink-300">
                    {valor.length}/{c.max}
                  </span>
                )}
              </label>
              {c.textarea ? (
                <textarea
                  id={c.name}
                  rows={c.rows}
                  maxLength={c.max}
                  value={valor}
                  placeholder={c.placeholder}
                  onChange={(e) => cambiar(c.name, e.target.value)}
                  className={input}
                />
              ) : (
                <input
                  id={c.name}
                  type={c.type ?? "text"}
                  required={c.required}
                  maxLength={c.max}
                  value={valor}
                  placeholder={c.placeholder}
                  onChange={(e) => cambiar(c.name, e.target.value)}
                  className={input}
                />
              )}
            </div>
          );
        })}

        <div>
          <label
            htmlFor="anios_experiencia"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Años de experiencia
          </label>
          <input
            id="anios_experiencia"
            type="number"
            min={0}
            max={50}
            value={valores.anios_experiencia}
            onChange={(e) => cambiar("anios_experiencia", e.target.value)}
            className={input}
          />
        </div>

        <div>
          <label
            htmlFor="modalidad_preferida"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Modalidad preferida
          </label>
          <select
            id="modalidad_preferida"
            value={valores.modalidad_preferida}
            onChange={(e) => cambiar("modalidad_preferida", e.target.value)}
            className={input}
          >
            {MODALIDADES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
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
          {guardando ? "Guardando..." : "Guardar cambios"}
        </button>
        {guardado && (
          <span className="text-sm font-medium text-signal-600">
            Perfil actualizado
          </span>
        )}
      </div>
    </form>
  );
}
