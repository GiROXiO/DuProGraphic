// Parámetro requerido: $usuario_id
// Recomienda vacantes abiertas y publicadas según habilidades y contactos postulados.
MATCH (usuario:Usuario {id: $usuario_id})-[:TIENE_HABILIDAD]->(habilidad:Habilidad)<-[:REQUIERE]-(oferta:Oferta)
WHERE toLower(trim(coalesce(oferta.estado, ''))) = 'abierta'
  AND EXISTS { MATCH (:Empresa)-[:PUBLICA]->(oferta) }
  AND NOT EXISTS { MATCH (usuario)-[:POSTULA_A]->(oferta) }
MATCH (empresa:Empresa)-[:PUBLICA]->(oferta)
OPTIONAL MATCH (usuario)-[:CONECTA_CON]-(contacto:Usuario)-[:POSTULA_A]->(oferta)
WITH oferta, empresa,
     collect(DISTINCT habilidad) AS habilidades_coincidentes,
     count(DISTINCT contacto) AS contactos_postulados
RETURN
  oferta.id AS oferta_id,
  oferta.titulo AS oferta,
  empresa.nombre AS empresa,
  [habilidad IN habilidades_coincidentes | habilidad.nombre] AS habilidades_coincidentes,
  size(habilidades_coincidentes) AS cantidad_habilidades,
  contactos_postulados
ORDER BY cantidad_habilidades DESC, contactos_postulados DESC, oferta;
