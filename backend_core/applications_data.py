"""Postulaciones de un usuario a ofertas laborales (relación POSTULA_A)."""

from datetime import date

from backend_core.portal_common import consultar, escribir

# Mientras la postulación está en alguno de estos estados, la persona todavía puede retirarla.
# Con una decisión de la empresa (oferta, aceptado, rechazado) ya no.
ESTADOS_RETIRABLES = {"aplicado", "en revisión", "entrevista", "entrevistado"}


# Etapas del proceso de selección, en orden. Con aceptado o rechazado el proceso termina.
ESTADOS_PROCESO = ("aplicado", "en revisión", "entrevista", "oferta", "aceptado", "rechazado")
ESTADOS_FINALES = {"aceptado", "rechazado"}


def normalizar_estado(estado):
    valor = str(estado or "aplicado").strip().lower()
    # Los datos de ejemplo antiguos usan "entrevistado".
    return "entrevista" if valor == "entrevistado" else valor


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



# --- Lado de la empresa: candidatos de una oferta ---------------------------------------

def postulantes_oferta(empresa_id, oferta_id):
    """Personas que se postularon a la oferta, con su afinidad y su estado en el proceso.

    La afinidad sale del grafo: habilidades de la oferta que la persona tiene, las que le
    faltan y cuántos de sus contactos ya trabajan en la empresa.
    """
    filas = consultar(
        """
        MATCH (emp:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})
        MATCH (u:Usuario)-[r:POSTULA_A]->(o)
        WITH emp, o, u, r,
             [(o)-[:REQUIERE]->(h:Habilidad) | h] AS requeridas,
             [(u)-[:TIENE_HABILIDAD]->(h:Habilidad) | h] AS poseidas
        WITH emp, u, r, requeridas,
             [h IN requeridas WHERE h IN poseidas] AS coincidencias
        RETURN u.id AS id, u.nombre AS nombre, u.perfil_profesional AS titular,
               u.ubicacion AS ubicacion,
               coalesce(r.estado_proceso, 'aplicado') AS estado,
               r.fecha_postulacion AS fecha,
               [h IN coincidencias | h.nombre] AS habilidades_coincidentes,
               [h IN requeridas WHERE NOT h IN coincidencias | h.nombre] AS habilidades_faltantes,
               size(requeridas) AS total_requeridas,
               COUNT { MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:TRABAJA_EN]->(emp) RETURN DISTINCT c } AS contactos_en_empresa
        ORDER BY r.fecha_postulacion DESC, u.nombre
        """,
        e=empresa_id, o=oferta_id,
    ) or []
    for fila in filas:
        fila["estado"] = normalizar_estado(fila["estado"])
    return filas


def cambiar_estado_postulacion(oferta_id, usuario_id, estado):
    """Cambia la etapa de la postulación. [] si la persona no se postuló a esa oferta."""
    return escribir(
        """
        MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o})
        SET r.estado_proceso = $estado, r.fecha_actualizacion = $fecha
        RETURN r.estado_proceso AS estado
        """,
        u=usuario_id, o=oferta_id, estado=estado, fecha=date.today().isoformat(),
    )