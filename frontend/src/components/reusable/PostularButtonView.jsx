import { useState } from "react";
import api, { getUser } from "../../api";

// Peticiones en curso (a nivel de módulo): evita enviar dos veces la misma postulación.
const enVuelo = new Set();

function describirError(err) {
  const detalle = err.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  const estado = err.response?.status;
  return estado
    ? `No se pudo enviar la postulación (error ${estado}).`
    : "No se pudo conectar con el servidor.";
}

export default function PostularButtonView({ ofertaId, onPostulada }) {
  const [enviada, setEnviada] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const yo = getUser()?.entidad_id;

  const postular = async () => {
    const clave = `${yo}:${ofertaId}`;
    if (enVuelo.has(clave)) return;
    enVuelo.add(clave);
    setError("");
    setOcupado(true);
    try {
      await api.post(`/api/users/${yo}/applications/${ofertaId}`);
      setEnviada(true);
      onPostulada?.(ofertaId);
    } catch (err) {
      setError(describirError(err));
    } finally {
      enVuelo.delete(clave);
      setOcupado(false);
    }
  };

  if (enviada) {
    return (
      <span className="inline-block rounded-xl bg-signal-50 px-4 py-2 text-sm font-semibold text-signal-600">
        ✓ Postulación enviada
      </span>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        onClick={postular}
        disabled={ocupado}
        className="rounded-xl bg-brand-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {ocupado ? "Enviando..." : "Postular"}
      </button>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
