"""Postulaciones de un usuario a ofertas laborales (relación POSTULA_A)."""

from datetime import date

from backend_core.portal_common import consultar, escribir

# Mientras la postulación está en alguno de estos estados, la persona todavía puede retirarla.
# Con una decisión de la empresa (oferta, aceptado, rechazado) ya no.
ESTADOS_RETIRABLES = {"aplicado", "en revisión", "entrevista", "entrevistado"}


def normalizar_estado(estado):
    return str(estado or "aplicado").strip().lower()


def mis_postulaciones(usuario_id):
    filas = consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:POSTULA_A]->(o:Oferta)
        OPTIONAL MATCH (e:Empresa)-[:PUBLICA]->(o)
        OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
        WITH o, e, collect(DISTINCT r)[0] AS post, collect(DISTINCT h.nombre) AS habilidades
        RETURN o.id AS id, o.titulo AS titulo, o.modalidad AS modalidad,
               o.nivel_experiencia AS experiencia, o.estado AS oferta_estado,
               e.id AS empresa_id, e.nombre AS empresa, e.sector AS sector,
               habilidades,
               coalesce(post.estado_proceso, 'aplicado') AS estado,
               post.fecha_postulacion AS fecha
        ORDER BY fecha DESC, titulo
        """,
        id=usuario_id,
    ) or []
    for fila in filas:
        fila["retirable"] = normalizar_estado(fila["estado"]) in ESTADOS_RETIRABLES
    return filas


def oferta_publicada(oferta_id):
    """{'abierta': bool} si la oferta existe y la publica una empresa; None si no."""
    filas = consultar(
        """
        MATCH (:Empresa)-[:PUBLICA]->(o:Oferta {id: $o})
        RETURN toLower(trim(coalesce(o.estado, ''))) = 'abierta' AS abierta
        LIMIT 1
        """,
        o=oferta_id,
    )
    return filas[0] if filas else None


def estado_postulacion(usuario_id, oferta_id):
    """Estado actual de la postulación, o None si la persona no se ha postulado."""
    filas = consultar(
        """
        MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o})
        RETURN coalesce(r.estado_proceso, 'aplicado') AS estado
        LIMIT 1
        """,
        u=usuario_id, o=oferta_id,
    )
    return filas[0]["estado"] if filas else None


def postular(usuario_id, oferta_id):
    """Crea la postulación (estado 'aplicado'). Solo ofertas abiertas.

    Usa MERGE: aunque se envíe dos veces (doble clic), solo existe una relación.
    """
    return escribir(
        """
        MATCH (u:Usuario {id: $u}), (:Empresa)-[:PUBLICA]->(o:Oferta {id: $o})
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
        MERGE (u)-[r:POSTULA_A]->(o)
          ON CREATE SET r.fecha_postulacion = $fecha, r.estado_proceso = 'aplicado'
        RETURN coalesce(r.estado_proceso, 'aplicado') AS estado
        """,
        u=usuario_id, o=oferta_id, fecha=date.today().isoformat(),
    )


def retirar_postulacion(usuario_id, oferta_id):
    return escribir(
        """
        MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(o:Oferta {id: $o})
        DELETE r
        RETURN o.id AS id
        """,
        u=usuario_id, o=oferta_id,
    )