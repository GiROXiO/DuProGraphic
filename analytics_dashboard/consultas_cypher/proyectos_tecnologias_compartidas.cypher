// Encuentra pares de proyectos que utilizan las mismas habilidades/tecnologías.
MATCH (p1:Proyecto)-[:USA_TECNOLOGIA]->(tecnologia:Habilidad)<-[:USA_TECNOLOGIA]-(p2:Proyecto)
WHERE p1.id < p2.id
RETURN
  p1.id AS proyecto1_id,
  p1.nombre AS proyecto1,
  p2.id AS proyecto2_id,
  p2.nombre AS proyecto2,
  collect(DISTINCT tecnologia.nombre) AS tecnologias_compartidas,
  count(DISTINCT tecnologia) AS cantidad_compartida
ORDER BY cantidad_compartida DESC, proyecto1, proyecto2;
