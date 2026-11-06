// Parámetro requerido: $usuario_id
// Sugiere usuarios con habilidades usadas en los proyectos del usuario,
// excluyendo a quienes ya comparten un proyecto con él.
MATCH (usuario:Usuario {id: $usuario_id})-[:PARTICIPA_EN]->(:Proyecto)-[:USA_TECNOLOGIA]->(tecnologia:Habilidad)
WITH usuario, collect(DISTINCT tecnologia) AS tecnologias
MATCH (candidato:Usuario)-[:TIENE_HABILIDAD]->(tecnologia:Habilidad)
WHERE candidato <> usuario
  AND tecnologia IN tecnologias
  AND NOT EXISTS {
    MATCH (usuario)-[:PARTICIPA_EN]->(:Proyecto)<-[:PARTICIPA_EN]-(candidato)
  }
RETURN
  candidato.id AS candidato_id,
  candidato.nombre AS colaborador_recomendado,
  collect(DISTINCT tecnologia.nombre) AS tecnologias_en_comun,
  count(DISTINCT tecnologia) AS cantidad_tecnologias
ORDER BY cantidad_tecnologias DESC, colaborador_recomendado;
