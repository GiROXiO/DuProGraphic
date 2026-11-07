// Parámetros requeridos: $usuario_id y $empresa_id
// Encuentra la ruta más corta de hasta seis relaciones entre usuario y empresa.
MATCH (usuario:Usuario {id: $usuario_id})
MATCH (empresa:Empresa {id: $empresa_id})
MATCH ruta = shortestPath((usuario)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA*..6]-(empresa))
RETURN
  [n IN nodes(ruta) | coalesce(n.nombre, n.titulo, n.id)] AS ruta,
  length(ruta) AS saltos;
