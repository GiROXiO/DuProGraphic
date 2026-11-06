// Lista los usuarios y sus conexiones directas para calcular componentes localmente.
// Es de solo lectura y evita búsquedas de rutas entre todos los pares.
MATCH (usuario:Usuario)
OPTIONAL MATCH (usuario)-[:CONECTA_CON]-(contacto:Usuario)
RETURN
  usuario.id AS usuario_id,
  usuario.nombre AS usuario,
  collect(DISTINCT contacto.id) AS contactos_ids
ORDER BY usuario_id;
