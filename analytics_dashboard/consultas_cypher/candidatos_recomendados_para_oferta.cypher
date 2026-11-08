// Parámetro requerido: $oferta_id
// Recomienda candidatos con habilidades requeridas y contactos conectados a postulantes.
MATCH (oferta:Oferta {id: $oferta_id})
WHERE toLower(trim(coalesce(oferta.estado, ''))) = 'abierta'
  AND EXISTS { MATCH (:Empresa)-[:PUBLICA]->(oferta) }
OPTIONAL MATCH (oferta)-[:REQUIERE]->(requerida:Habilidad)
WITH oferta, collect(DISTINCT requerida) AS habilidades_requeridas
MATCH (candidato:Usuario)
WHERE NOT EXISTS { MATCH (candidato)-[:POSTULA_A]->(oferta) }
OPTIONAL MATCH (candidato)-[:TIENE_HABILIDAD]->(poseida:Habilidad)
WITH oferta, candidato, habilidades_requeridas,
     collect(DISTINCT poseida) AS habilidades_candidato
WITH oferta, candidato, habilidades_requeridas,
     [h IN habilidades_requeridas WHERE h IN habilidades_candidato] AS coincidencias
WHERE size(coincidencias) > 0
OPTIONAL MATCH (candidato)-[:CONECTA_CON]-(contacto:Usuario)-[:POSTULA_A]->(oferta)
RETURN
  candidato.id AS candidato_id,
  candidato.nombre AS candidato,
  [h IN coincidencias | h.nombre] AS habilidades_coincidentes,
  size(coincidencias) AS cantidad_habilidades,
  count(DISTINCT contacto) AS contactos_que_se_postularon
ORDER BY cantidad_habilidades DESC, contactos_que_se_postularon DESC;
