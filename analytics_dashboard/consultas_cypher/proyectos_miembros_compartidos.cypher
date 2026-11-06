// Encuentra pares de proyectos con miembros en común.
MATCH (usuario:Usuario)-[:PARTICIPA_EN]->(p1:Proyecto)
MATCH (usuario)-[:PARTICIPA_EN]->(p2:Proyecto)
WHERE p1.id < p2.id
RETURN
  p1.id AS proyecto1_id,
  p1.nombre AS proyecto1,
  p2.id AS proyecto2_id,
  p2.nombre AS proyecto2,
  collect(DISTINCT usuario.nombre) AS miembros_compartidos,
  count(DISTINCT usuario) AS cantidad_miembros
ORDER BY cantidad_miembros DESC, proyecto1, proyecto2;
