// Convierte los errores de FastAPI (texto o lista de validaciones) en un mensaje legible.
// etiquetas: { nombre_del_campo: "Etiqueta que ve la persona" }
export function mensajeError(
  err,
  etiquetas = {},
  porDefecto = "No se pudieron guardar los cambios.",
) {
  const detalle = err.response?.data?.detail;
  if (Array.isArray(detalle)) {
    return detalle
      .map((d) => {
        const campo = d.loc?.[1];
        const texto = String(d.msg).replace(/^Value error, /, "");
        return `${etiquetas[campo] ?? campo ?? "Dato"}: ${texto}`;
      })
      .join(". ");
  }
  if (typeof detalle === "string") return detalle;
  return err.response?.status
    ? `${porDefecto} (error ${err.response.status}).`
    : "No se pudo conectar con el servidor.";
}
