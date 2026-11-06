// Cuenta ofertas que requieren cada habilidad y cuántas la marcan como obligatoria.
MATCH (oferta:Oferta)-[requisito:REQUIERE]->(habilidad:Habilidad)
RETURN
  habilidad.id AS habilidad_id,
  habilidad.nombre AS habilidad,
  count(DISTINCT oferta) AS ofertas_que_la_requieren,
  count(DISTINCT CASE WHEN requisito.es_obligatoria = true THEN oferta END) AS ofertas_que_la_exigen
ORDER BY ofertas_que_la_requieren DESC, habilidad;
