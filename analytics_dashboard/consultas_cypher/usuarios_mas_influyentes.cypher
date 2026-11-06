// Aproxima influencia por cantidad de contactos profesionales directos.
MATCH (usuario:Usuario)
OPTIONAL MATCH (usuario)-[:CONECTA_CON]-(contacto:Usuario)
RETURN
  usuario.id AS usuario_id,
  usuario.nombre AS usuario,
  count(DISTINCT contacto) AS contactos_directos
ORDER BY contactos_directos DESC, usuario;
