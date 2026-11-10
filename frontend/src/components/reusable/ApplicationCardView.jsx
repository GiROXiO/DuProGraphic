import { useState } from "react";
import api, { getUser } from "../../api";
import SkillBadgeView from "./SkillBadgeView";

// Cómo se muestra cada estado del proceso de selección.
const ESTADOS = {
  aplicado: { texto: "Enviada", clase: "bg-ink-100 text-ink-700" },
  "en revisión": { texto: "En revisión", clase: "bg-amber-50 text-amber-700" },
  entrevista: { texto: "Entrevista", clase: "bg-brand-50 text-brand-700" },
  entrevistado: { texto: "Entrevista", clase: "bg-brand-50 text-brand-700" },
  oferta: { texto: "Oferta recibida", clase: "bg-signal-50 text-signal-600" },
  aceptado: { texto: "Aceptada", clase: "bg-signal-600 text-white" },
  rechazado: { texto: "Rechazada", clase: "bg-red-50 text-red-700" },
};

export default function ApplicationCardView({ postulacion, onRetirada }) {
  const [confirmando, setConfirmando] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const yo = getUser()?.entidad_id;

  const estado = ESTADOS[String(postulacion.estado).toLowerCase()] ?? {
    texto: postulacion.estado,
    clase: "bg-ink-100 text-ink-700",
  };
  const meta = [postulacion.modalidad, postulacion.experiencia].filter(Boolean);
  const cerrada =
    String(postulacion.oferta_estado ?? "")
      .trim()
      .toLowerCase() !== "abierta";

  const retirar = async () => {
    setError("");
    setOcupado(true);
    try {
      await api.delete(`/api/users/${yo}/applications/${postulacion.id}`);
      onRetirada?.(postulacion.id);
    } catch (err) {
      setError(
        err.response?.data?.detail || "No se pudo retirar la postulación.",
      );
      setOcupado(false);
      setConfirmando(false);
    }
  };

  return (
    <article className="rounded-2xl border border-ink-100 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold leading-snug text-ink-900">
            {postulacion.titulo}
          </h3>
          <p className="mt-0.5 text-sm text-ink-500">
            {postulacion.empresa}
            {postulacion.sector ? ` · ${postulacion.sector}` : ""}
          </p>
        </div>
        <span
          className={`whitespace-nowrap rounded-lg px-3 py-1 text-xs font-semibold ${estado.clase}`}
        >
          {estado.texto}
        </span>
      </div>

      {(meta.length > 0 || cerrada) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {meta.map((m, i) => (
            <span
              key={`${m}-${i}`}
              className="rounded-md bg-ink-100 px-2 py-0.5 text-xs capitalize text-ink-700"
            >
              {m}
            </span>
          ))}
          {cerrada && (
            <span className="rounded-md bg-red-50 px-2 py-0.5 text-xs text-red-700">
              Oferta cerrada
            </span>
          )}
        </div>
      )}

      {postulacion.habilidades?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {postulacion.habilidades.map((h) => (
            <SkillBadgeView key={h} nombre={h} />
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-ink-500">
          Postulaste el {postulacion.fecha ?? "—"}
        </p>

        {postulacion.retirable &&
          (confirmando ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-ink-500">
                ¿Retirar esta postulación?
              </span>
              <button
                onClick={retirar}
                disabled={ocupado}
                className="rounded-xl bg-red-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
              >
                {ocupado ? "Retirando..." : "Sí, retirar"}
              </button>
              <button
                onClick={() => setConfirmando(false)}
                disabled={ocupado}
                className="rounded-xl border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100 disabled:opacity-50"
              >
                No
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmando(true)}
              className="rounded-xl border border-ink-100 px-4 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
            >
              Retirar postulación
            </button>
          ))}
      </div>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </article>
  );
}
