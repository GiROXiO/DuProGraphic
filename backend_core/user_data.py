"""Consultas de datos del portal de usuario (sin interfaz). Usadas por la API FastAPI."""

from backend_core.portal_common import consultar

RELACIONES_RUTA = (
    "CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|"
    "POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A"
)


def perfil_usuario(usuario_id):
    filas = consultar(
        """
        MATCH (u:Usuario {id: $id})
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        RETURN properties(u) AS perfil, c.id AS cuenta_id
        LIMIT 1
        """,
        id=usuario_id,
    )
    return filas[0] if filas else None


def sugerencias(usuario_id):
    # Afinidad explicable: personas pondera contactos (20), habilidades (30),
    # proyectos (20), intereses (10), ciudad (10) y formación (10). Las otras
    # dos consultas ponderan encaje con ofertas/tecnologías, actividad y rutas.
    personas = consultar(
        """
        MATCH (yo:Usuario {id: $id})
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(p:Usuario)
        WHERE p <> yo AND coalesce(c.activa, true) = true
          AND NOT EXISTS { MATCH (yo)-[:CONECTA_CON]-(p) }
        OPTIONAL MATCH (yo)-[:CONECTA_CON]-(intermedio:Usuario)-[:CONECTA_CON]-(p)
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(p)
        OPTIONAL MATCH (yo)-[:PARTICIPA_EN]->(proyecto:Proyecto)<-[:PARTICIPA_EN]-(p)
        WITH yo, p, c, count(DISTINCT intermedio) AS contactos,
             collect(DISTINCT h.nombre) AS habilidades,
             count(DISTINCT proyecto) AS proyectos,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         toLower(coalesce(p.areas_interes, '')) CONTAINS trim(tema)]) AS temas
        RETURN p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil,
               p.ubicacion AS ubicacion, p.universidad AS universidad,
               (yo.ubicacion IS NOT NULL AND toLower(yo.ubicacion) = toLower(coalesce(p.ubicacion, ''))) AS misma_ciudad,
               (yo.universidad IS NOT NULL AND toLower(yo.universidad) = toLower(coalesce(p.universidad, ''))) AS misma_formacion,
               c.id AS cuenta_id, contactos, habilidades, proyectos, temas,
               round(
                   CASE WHEN contactos * 7 > 20 THEN 20 ELSE contactos * 7 END +
                   CASE WHEN size(habilidades) * 10 > 30 THEN 30 ELSE size(habilidades) * 10 END +
                   CASE WHEN proyectos * 10 > 20 THEN 20 ELSE proyectos * 10 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END +
                   CASE WHEN yo.ubicacion IS NOT NULL AND toLower(yo.ubicacion) = toLower(coalesce(p.ubicacion, '')) THEN 10 ELSE 0 END +
                   CASE WHEN yo.universidad IS NOT NULL AND toLower(yo.universidad) = toLower(coalesce(p.universidad, '')) THEN 10 ELSE 0 END
               ) AS afinidad
        ORDER BY afinidad DESC, contactos DESC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    empresas = consultar(
        """
        MATCH (yo:Usuario {id: $id}), (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
          AND NOT EXISTS { MATCH (yo)-[:SIGUE_A]->(e) }
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:REQUIERE]-(o)
        WITH yo, e, o, count(DISTINCT h) AS coincidencias
        OPTIONAL MATCH (o)-[:REQUIERE]->(requisito:Habilidad)
        WITH yo, e, o, coincidencias, count(DISTINCT requisito) AS requisitos
        WITH yo, e, count(DISTINCT o) AS ofertas,
             sum(coincidencias) AS coincidencias,
             avg(CASE WHEN requisitos = 0 THEN 0.35 ELSE toFloat(coincidencias) / requisitos END) AS ajuste,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         toLower(coalesce(e.sector, '')) CONTAINS trim(tema)]) AS temas
        OPTIONAL MATCH ruta = shortestPath((yo)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A*..6]-(e))
        WITH yo, e, ofertas, coincidencias, ajuste, temas, length(ruta) AS distancia,
             CASE WHEN coalesce(yo.ubicacion, '') <> '' AND toLower(yo.ubicacion) = toLower(coalesce(e.ubicacion, '')) THEN 8 ELSE 0 END AS ciudad
        RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector,
               ofertas, coincidencias, distancia, temas,
               round(30 * ajuste +
                   CASE WHEN coincidencias * 5 > 20 THEN 20 ELSE coincidencias * 5 END +
                   CASE WHEN ofertas * 5 > 15 THEN 15 ELSE ofertas * 5 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END + ciudad +
                   CASE WHEN distancia IS NULL OR 17 - distancia * 3 < 0 THEN 0 ELSE 17 - distancia * 3 END
               ) AS afinidad
        ORDER BY afinidad DESC, distancia ASC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    proyectos = consultar(
        """
        MATCH (yo:Usuario {id: $id}), (p:Proyecto)
        WHERE NOT EXISTS { MATCH (yo)-[:PARTICIPA_EN]->(p) }
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p)
        WITH yo, p, collect(DISTINCT h.nombre) AS tecnologias,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         (toLower(coalesce(p.nombre, '')) CONTAINS trim(tema) OR
                          toLower(coalesce(p.descripcion, '')) CONTAINS trim(tema))]) AS temas
        OPTIONAL MATCH (miembro:Usuario)-[:PARTICIPA_EN]->(p)
        WITH yo, p, tecnologias, temas, count(DISTINCT miembro) AS miembros
        OPTIONAL MATCH ruta = shortestPath((yo)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A*..6]-(p))
        WITH yo, p, tecnologias, temas, miembros, length(ruta) AS distancia
        RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion,
               tecnologias, size(tecnologias) AS coincidencias, miembros, distancia, temas,
               round(
                   CASE WHEN size(tecnologias) * 16 > 50 THEN 50 ELSE size(tecnologias) * 16 END +
                   CASE WHEN miembros * 2 > 10 THEN 10 ELSE miembros * 2 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END +
                   CASE WHEN distancia IS NULL OR 30 - distancia * 4 < 0 THEN 0 ELSE 30 - distancia * 4 END
               ) AS afinidad
        ORDER BY afinidad DESC, distancia ASC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    return personas, empresas, proyectos



def ofertas_recomendadas(usuario_id):
    return consultar(
        f"""
        MATCH (u:Usuario {{id: $id}}), (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
          AND NOT EXISTS {{ MATCH (u)-[:POSTULA_A]->(o) }}
        OPTIONAL MATCH (u)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:REQUIERE]-(o)
        WITH u, e, o, collect(DISTINCT h) AS habilidades_coincidentes
        OPTIONAL MATCH (o)-[:REQUIERE]->(requerida:Habilidad)
        WITH u, e, o, habilidades_coincidentes,
             count(DISTINCT requerida) AS requisitos
        WITH u, e, o, habilidades_coincidentes, requisitos,
             CASE WHEN requisitos = 0 THEN 0.35
                  ELSE toFloat(size(habilidades_coincidentes)) / requisitos END AS ajuste_habilidades
        OPTIONAL MATCH ruta = shortestPath((u)-[:{RELACIONES_RUTA}*..6]-(e))
        OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
        OPTIONAL MATCH (u)-[:CONECTA_CON]-(contacto:Usuario)-[:POSTULA_A]->(o)
        WITH u, e, o, p, habilidades_coincidentes, ajuste_habilidades,
             length(ruta) AS distancia, count(DISTINCT contacto) AS contactos
        WITH u, e, o, p, habilidades_coincidentes, ajuste_habilidades, distancia, contactos,
             CASE WHEN coalesce(o.modalidad, '') = 'remoto' THEN 10
                  WHEN coalesce(u.modalidad_preferida, '') = o.modalidad THEN 10
                  WHEN coalesce(u.ubicacion, '') <> '' AND toLower(u.ubicacion) = toLower(coalesce(e.ubicacion, '')) THEN 8
                  ELSE 0 END AS ajuste_contexto
        RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
               o.modalidad AS modalidad, o.nivel_experiencia AS experiencia,
               e.id AS empresa_id, e.nombre AS empresa, e.sector AS sector,
               p.id AS proyecto_id, p.nombre AS proyecto,
               [h IN habilidades_coincidentes | h.nombre] AS habilidades,
               distancia, contactos,
               round(
                   55 * ajuste_habilidades + ajuste_contexto +
                   CASE WHEN contactos * 5 > 15 THEN 15 ELSE contactos * 5 END +
                   CASE WHEN distancia IS NULL OR 20 - distancia * 3 < 0 THEN 0 ELSE 20 - distancia * 3 END
               ) AS afinidad
        ORDER BY afinidad DESC, CASE WHEN distancia IS NULL THEN 99 ELSE distancia END,
                 contactos DESC, titulo
        """,
        id=usuario_id,
    ) or []
