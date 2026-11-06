// Parámetro requerido: $usuario_id
// Sugiere contactos de segundo grado que aún no están conectados directamente.
MATCH (usuario:Usuario {id: $usuario_id})-[:CONECTA_CON]-(contacto:Usuario)-[:CONECTA_CON]-(sugerido:Usuario)
WHERE sugerido <> usuario
  AND NOT EXISTS {
    MATCH (usuario)-[:CONECTA_CON]-(sugerido)
  }
RETURN
  sugerido.id AS usuario_id,
  sugerido.nombre AS contacto_recomendado,
  count(DISTINCT contacto) AS contactos_en_comun,
  collect(DISTINCT contacto.nombre) AS recomendados_por
ORDER BY contactos_en_comun DESC, contacto_recomendado;
