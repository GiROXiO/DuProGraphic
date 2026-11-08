import { useState } from "react";
import api, { getUser } from "../../api";

const primario =
  "rounded-xl bg-brand-600 font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50";
const secundario =
  "rounded-xl border border-ink-100 bg-white font-semibold text-ink-700 transition hover:bg-ink-100 disabled:cursor-not-allowed disabled:opacity-50";

// Peticiones en curso (a nivel de módulo): evita enviar dos veces la misma acción aunque el
// componente se vuelva a montar o se haga doble clic.
const enVuelo = new Set();

function describirError(err) {
  const detalle = err.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  const estado = err.response?.status;
  return estado
    ? `No se pudo completar la acción (error ${estado}).`
    : "No se pudo conectar con el servidor.";
}

// relacion: "ninguna" | "enviada" | "recibida" | "conectado".
// - Con onChange es controlado: el padre guarda el estado y lo devuelve en "relacion".
// - Sin onChange guarda su propio estado (por ejemplo en el perfil público).
export default function ConnectButtonView({
  personaId,
  relacion,
  onChange,
  compacto = false,
}) {
  const [interno, setInterno] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const yo = getUser()?.entidad_id;
  const estado = onChange ? relacion : (interno ?? relacion);
  const tam = compacto ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm";

  const ejecutar = async (accion, peticion) => {
    const clave = `${yo}:${personaId}:${accion}`;
    if (enVuelo.has(clave)) return;
    enVuelo.add(clave);
    setError("");
    setOcupado(true);
    try {
      const res = await peticion();
      const nuevo = res.data.data.relacion;
      setInterno(nuevo);
      onChange?.(nuevo);
    } catch (err) {
      setError(describirError(err));
    } finally {
      enVuelo.delete(clave);
      setOcupado(false);
    }
  };

  const conectar = () =>
    ejecutar("conectar", () =>
      api.post(`/api/users/${yo}/connections/${personaId}`),
    );
  const aceptar = () =>
    ejecutar("aceptar", () =>
      api.post(`/api/users/${yo}/connection-requests/${personaId}/accept`),
    );
  const retirar = () =>
    ejecutar("retirar", () =>
      api.delete(`/api/users/${yo}/connection-requests/${personaId}`),
    );

  let contenido = null;
  if (estado === "ninguna") {
    contenido = (
      <button
        onClick={conectar}
        disabled={ocupado}
        className={`${primario} ${tam}`}
      >
        {ocupado ? "Enviando..." : "Conectar"}
      </button>
    );
  } else if (estado === "enviada") {
    contenido = (
      <div className="flex items-center gap-2">
        <span
          className={`whitespace-nowrap rounded-xl bg-ink-100 font-semibold text-ink-500 ${tam}`}
        >
          {compacto ? "Enviada" : "Solicitud enviada"}
        </span>
        <button
          onClick={retirar}
          disabled={ocupado}
          className={`${secundario} ${tam}`}
        >
          Cancelar
        </button>
      </div>
    );
  } else if (estado === "recibida") {
    contenido = (
      <div className="flex items-center gap-2">
        <button
          onClick={aceptar}
          disabled={ocupado}
          className={`${primario} ${tam}`}
        >
          {ocupado ? "Aceptando..." : "Aceptar"}
        </button>
        <button
          onClick={retirar}
          disabled={ocupado}
          className={`${secundario} ${tam}`}
        >
          Rechazar
        </button>
      </div>
    );
  } else if (estado === "conectado") {
    contenido = (
      <span
        className={`rounded-xl bg-signal-50 font-semibold text-signal-600 ${tam}`}
      >
        ✓ Conectados
      </span>
    );
  }

  if (!contenido) return null;

  return (
    <div className="flex flex-col items-start gap-1">
      {contenido}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
