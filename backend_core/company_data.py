"""Consultas de datos del portal de empresa (sin interfaz). Usadas por la API FastAPI."""

from backend_core.portal_common import consultar


def ofertas_empresa(empresa_id):
    return consultar(
        """
        MATCH (:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
        OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
        CALL {
            WITH o
            OPTIONAL MATCH (o)<-[r:POSTULA_A]-(:Usuario)
            RETURN count(DISTINCT r) AS postulaciones
        }
        CALL {
            WITH o
            OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
            RETURN collect(DISTINCT h.nombre) AS habilidades
        }
        CALL {
            WITH o
            OPTIONAL MATCH (u:Usuario)-[:TRABAJO_EN_OFERTA]->(o)
            RETURN collect(DISTINCT u.nombre) AS contrataciones_registradas
        }
        CALL {
            WITH o
            OPTIONAL MATCH (u:Usuario)-[r:POSTULA_A]->(o)
            WHERE toLower(trim(coalesce(r.estado_proceso, ''))) = 'aceptado'
            RETURN collect(DISTINCT u.nombre) AS postulaciones_aceptadas
        }
        RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
               o.estado AS estado, o.modalidad AS modalidad,
               o.nivel_experiencia AS experiencia, p.id AS proyecto_id,
               p.nombre AS proyecto, p.descripcion AS proyecto_descripcion,
               postulaciones, habilidades,
               contrataciones_registradas + postulaciones_aceptadas AS personas_contratadas
        ORDER BY titulo
        """,
        id=empresa_id,
    ) or []

