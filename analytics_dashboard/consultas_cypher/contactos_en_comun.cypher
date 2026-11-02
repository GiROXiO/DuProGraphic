// Usuarios con contactos en común

MATCH (u1:Usuario)-[:CONECTA_CON]-(comun:Usuario)-[:CONECTA_CON]-(u2:Usuario)
WHERE u1.id < u2.id
RETURN
  u1.nombre AS usuario1,
  u2.nombre AS usuario2,
  collect(DISTINCT comun.nombre) AS contactos_en_comun,
  count(DISTINCT comun) AS cantidad_contactos
ORDER BY cantidad_contactos DESC;