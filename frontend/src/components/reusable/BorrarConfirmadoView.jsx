import { useState } from "react";

// Botón de eliminar en dos pasos. onConfirmar debe devolver una promesa;
// los errores los muestra quien lo usa.
export default function BorrarConfirmadoView({
  onConfirmar,
  etiqueta = "Eliminar",
  deshabilitado = false,
  titulo,
}) {
  const [confirmando, setConfirmando] = useState(false);
  const [ocupado, setOcupado] = useState(false);

  const confirmar = async () => {
    setOcupado(true);
    try {
      await onConfirmar();
    } finally {
      setOcupado(false);
      setConfirmando(false);
    }
  };

  if (confirmando) {
    return (
      <span className="inline-flex items-center gap-2">
        <span className="text-xs text-ink-500">¿Seguro?</span>
        <button
          onClick={confirmar}
          disabled={ocupado}
          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
        >
          {ocupado ? "Eliminando..." : "Sí, eliminar"}
        </button>
        <button
          onClick={() => setConfirmando(false)}
          disabled={ocupado}
          className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
        >
          No
        </button>
      </span>
    );
  }

  return (
    <button
      onClick={() => setConfirmando(true)}
      disabled={deshabilitado}
      title={titulo}
      className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-500 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-ink-500"
    >
      {etiqueta}
    </button>
  );
}
