import { useState } from "react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

const MODALIDADES = [
  { value: "remoto", label: "Remoto" },
  { value: "híbrido", label: "Híbrido" },
  { value: "presencial", label: "Presencial" },
];
const NIVELES = ["Junior", "Semi-Senior", "Senior"];

const ETIQUETAS = {
  titulo: "Título",
  descripcion: "Descripción",
  modalidad: "Modalidad",
  nivel_experiencia: "Nivel de experiencia",
  habilidades: "Habilidades",
};

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

// oferta = null para publicar una nueva; con una oferta existente, la edita.
export default function OfferFormView({
  companyId,
  oferta,
  onGuardada,
  onCancelar,
}) {
  const { data: catalogo, loading: cargandoCatalogo } = useFetch("/api/skills");

  const [titulo, setTitulo] = useState(oferta?.titulo ?? "");
  const [descripcion, setDescripcion] = useState(oferta?.descripcion ?? "");
  const [modalidad, setModalidad] = useState(oferta?.modalidad ?? "remoto");
  const [nivel, setNivel] = useState(oferta?.experiencia ?? "Junior");
  // id de habilidad -> obligatoria (true/false). Solo contiene las seleccionadas.
  const [seleccion, setSeleccion] = useState(() =>
    Object.fromEntries(
      (oferta?.habilidades_detalle ?? []).map((h) => [h.id, h.obligatoria]),
    ),
  );
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  const alternar = (id) =>
    setSeleccion((s) => {
      const copia = { ...s };
      if (id in copia) delete copia[id];
      else copia[id] = true;
      return copia;
    });

  const marcarObligatoria = (id, valor) =>
    setSeleccion((s) => ({ ...s, [id]: valor }));

  const enviar = async (e) => {
    e.preventDefault();
    setError("");
    setGuardando(true);
    const cuerpo = {
      titulo,
      descripcion,
      modalidad,
      nivel_experiencia: nivel,
      habilidades: Object.entries(seleccion).map(([id, obligatoria]) => ({
        id,
        obligatoria,
      })),
    };
    try {
      const url = `/api/companies/${companyId}/offers${oferta ? `/${oferta.id}` : ""}`;
      const res = oferta
        ? await api.put(url, cuerpo)
        : await api.post(url, cuerpo);
      onGuardada(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo guardar la oferta"));
      setGuardando(false);
    }
  };

  const seleccionadas = (catalogo ?? []).filter((h) => h.id in seleccion);

  return (
    <form
      onSubmit={enviar}
      className="space-y-5 rounded-2xl border border-brand-100 bg-white p-6 shadow-sm"
    >
      <h2 className="text-lg font-bold text-ink-900">
        {oferta ? "Editar oferta" : "Publicar una oferta"}
      </h2>

      <div>
        <label
          htmlFor="of-titulo"
          className="mb-1.5 block text-sm font-medium text-ink-700"
        >
          Título <span className="text-red-500">*</span>
        </label>
        <input
          id="of-titulo"
          required
          maxLength={160}
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Ej. Ingeniero de datos Neo4j"
          className={campo}
        />
      </div>

      <div>
        <label
          htmlFor="of-desc"
          className="mb-1.5 flex justify-between text-sm font-medium text-ink-700"
        >
          <span>Descripción</span>
          <span className="text-xs font-normal text-ink-300">
            {descripcion.length}/1800
          </span>
        </label>
        <textarea
          id="of-desc"
          rows={4}
          maxLength={1800}
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Responsabilidades del cargo y qué ofreces."
          className={campo}
        />
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label
            htmlFor="of-mod"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Modalidad
          </label>
          <select
            id="of-mod"
            value={modalidad}
            onChange={(e) => setModalidad(e.target.value)}
            className={campo}
          >
            {MODALIDADES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="of-nivel"
            className="mb-1.5 block text-sm font-medium text-ink-700"
          >
            Nivel de experiencia
          </label>
          <select
            id="of-nivel"
            value={nivel}
            onChange={(e) => setNivel(e.target.value)}
            className={campo}
          >
            {NIVELES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-ink-700">
          Habilidades requeridas{" "}
          <span className="font-normal text-ink-500">
            (con ellas se calcula la afinidad de los candidatos)
          </span>
        </p>
        {cargandoCatalogo && (
          <p className="text-sm text-ink-500">Cargando catálogo...</p>
        )}
        <div className="flex flex-wrap gap-2">
          {(catalogo ?? []).map((h) => {
            const activa = h.id in seleccion;
            return (
              <button
                key={h.id}
                type="button"
                onClick={() => alternar(h.id)}
                aria-pressed={activa}
                className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                  activa
                    ? "border-signal-600 bg-signal-50 text-signal-600"
                    : "border-ink-100 bg-white text-ink-500 hover:border-ink-300"
                }`}
              >
                {activa ? "✓ " : "+ "}
                {h.nombre}
              </button>
            );
          })}
        </div>

        {seleccionadas.length > 0 && (
          <ul className="mt-4 divide-y divide-ink-100 rounded-xl border border-ink-100">
            {seleccionadas.map((h) => (
              <li
                key={h.id}
                className="flex items-center justify-between gap-3 px-4 py-2.5"
              >
                <span className="text-sm font-medium text-ink-900">
                  {h.nombre}
                </span>
                <label className="flex items-center gap-2 text-sm text-ink-700">
                  <input
                    type="checkbox"
                    checked={seleccion[h.id]}
                    onChange={(e) => marcarObligatoria(h.id, e.target.checked)}
                  />
                  Obligatoria
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={guardando}
          className="rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {guardando
            ? "Guardando..."
            : oferta
              ? "Guardar cambios"
              : "Publicar oferta"}
        </button>
        <button
          type="button"
          onClick={onCancelar}
          disabled={guardando}
          className="rounded-xl border border-ink-100 px-5 py-2.5 text-sm font-semibold text-ink-700 transition hover:bg-ink-100 disabled:opacity-60"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
