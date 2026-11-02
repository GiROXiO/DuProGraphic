// Usuarios con habilidades similares

MATCH
  (u1:Usuario)-[:TIENE_HABILIDAD]->
  (h:Habilidad)<-[:TIENE_HABILIDAD]-
  (u2:Usuario)
WHERE u1.id < u2.id
RETURN
  u1.nombre AS usuario1,
  u2.nombre AS usuario2,
  collect(DISTINCT h.nombre) AS habilidades_en_comun,
  count(DISTINCT h) AS cantidad_habilidades
ORDER BY cantidad_habilidades DESC;