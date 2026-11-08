"""Conexiones profesionales entre usuarios y perfil público (portal de usuario)."""

from datetime import date

from backend_core.portal_common import consultar, escribir

# Campos del perfil que ven otras cuentas. El correo y las preferencias privadas no se publican.
CAMPOS_PUBLICOS = (
    "nombre",
    "perfil_profesional",
    "universidad",
    "ubicacion",
    "acerca_de",
    "educacion_detalle",
    "areas_interes",
    "experiencia",
    "logros",
    "idiomas",
    "sitio_portafolio",
    "anios_experiencia",
)


# --- Lecturas -------------------------------------------------------------------------

def conexiones(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[:CONECTA_CON]-(p:Usuario)
        RETURN DISTINCT p.id AS id, p.nombre AS nombre,
               p.perfil_profesional AS perfil, p.universidad AS universidad
        ORDER BY nombre
        """,
        id=usuario_id,
    ) or []


def solicitudes_recibidas(usuario_id):
    return consultar(
        """
        MATCH (p:Usuario)-[r:SOLICITA_CONEXION]->(:Usuario {id: $id})
        RETURN DISTINCT p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil,
               p.universidad AS universidad, r.fecha AS fecha
        ORDER BY fecha DESC, nombre
        """,
        id=usuario_id,
    ) or []


def solicitudes_enviadas(usuario_id):
    return consultar(
        """
        MATCH (:Usuario {id: $id})-[r:SOLICITA_CONEXION]->(p:Usuario)
        RETURN DISTINCT p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil,
               p.universidad AS universidad, r.fecha AS fecha
        ORDER BY fecha DESC, nombre
        """,
        id=usuario_id,
    ) or []


def estado_relacion(yo_id, otro_id):
    """Devuelve conectado / enviada / recibida / ninguna, o None si alguno no existe."""
    filas = consultar(
        """
        MATCH (a:Usuario {id: $yo}), (b:Usuario {id: $otro})
        RETURN EXISTS { MATCH (a)-[:CONECTA_CON]-(b) } AS conectado,
               EXISTS { MATCH (a)-[:SOLICITA_CONEXION]->(b) } AS enviada,
               EXISTS { MATCH (b)-[:SOLICITA_CONEXION]->(a) } AS recibida
        """,
        yo=yo_id, otro=otro_id,
    )
    if not filas:
        return None
    f = filas[0]
    if f["conectado"]:
        return "conectado"
    if f["recibida"]:
        return "recibida"
    if f["enviada"]:
        return "enviada"
    return "ninguna"


def contactos_comunes(a_id, b_id):
    return consultar(
        """
        MATCH (:Usuario {id: $a})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(:Usuario {id: $b})
        RETURN DISTINCT c.id AS id, c.nombre AS nombre
        ORDER BY nombre
        """,
        a=a_id, b=b_id,
    ) or []


def perfil_publico(persona_id):
    """Perfil visible para otras cuentas, o None si la persona no existe."""
    filas = consultar("MATCH (u:Usuario {id: $id}) RETURN properties(u) AS p", id=persona_id)
    if not filas:
        return None
    props = filas[0]["p"]
    perfil = {"id": persona_id, **{c: props.get(c) for c in CAMPOS_PUBLICOS}}

    perfil["habilidades"] = consultar(
        """
        MATCH (:Usuario {id: $id})-[r:TIENE_HABILIDAD]->(h:Habilidad)
        RETURN h.id AS id, h.nombre AS nombre, h.categoria AS categoria,
               coalesce(r.nivel_dominio, 'básico') AS nivel
        ORDER BY nombre
        """,
        id=persona_id,
    ) or []
    perfil["empresas"] = consultar(
        """
        MATCH (:Usuario {id: $id})-[r:TRABAJA_EN]->(e:Empresa)
        RETURN e.id AS id, e.nombre AS empresa, e.sector AS sector, r.cargo AS cargo,
               coalesce(r.es_actual, false) AS actual, r.periodo AS periodo
        ORDER BY actual DESC, empresa
        """,
        id=persona_id,
    ) or []
    perfil["proyectos"] = consultar(
        """
        MATCH (:Usuario {id: $id})-[r:PARTICIPA_EN]->(p:Proyecto)
        RETURN p.id AS id, p.nombre AS nombre, r.rol AS rol
        ORDER BY nombre
        """,
        id=persona_id,
    ) or []
    perfil["contactos"] = consultar(
        "MATCH (:Usuario {id: $id})-[:CONECTA_CON]-(c:Usuario) RETURN count(DISTINCT c) AS n",
        id=persona_id,
    )[0]["n"]
    return perfil


# --- Escrituras -----------------------------------------------------------------------

def solicitar_conexion(origen_id, destino_id):
    """Crea la solicitud pendiente. Devuelve [] si ya hay conexión o la otra persona ya te escribió.

    Usa MERGE: aunque se envíe dos veces (doble clic, reintentos), solo existe una relación.
    """
    return escribir(
        """
        MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
        WHERE NOT EXISTS { MATCH (a)-[:CONECTA_CON]-(b) }
          AND NOT EXISTS { MATCH (b)-[:SOLICITA_CONEXION]->(a) }
        MERGE (a)-[s:SOLICITA_CONEXION]->(b)
          ON CREATE SET s.fecha = $fecha, s.estado = 'pendiente'
        RETURN b.id AS id
        """,
        a=origen_id, b=destino_id, fecha=date.today().isoformat(),
    )


def aceptar_solicitud(origen_id, destino_id):
    """El destinatario acepta: se crea CONECTA_CON en ambos sentidos. [] si ya no existe la solicitud."""
    return escribir(
        """
        MATCH (a:Usuario {id: $a})-[s:SOLICITA_CONEXION]->(b:Usuario {id: $b})
        DELETE s
        WITH a, b
        MERGE (a)-[ab:CONECTA_CON]->(b)
          ON CREATE SET ab.fuerza_conexion = 'media'
        MERGE (b)-[ba:CONECTA_CON]->(a)
          ON CREATE SET ba.fuerza_conexion = 'media'
        RETURN a.id AS id
        """,
        a=origen_id, b=destino_id,
    )


def retirar_solicitud(origen_id, destino_id):
    """Rechaza (si eres el destinatario) o cancela (si eres quien la envió). [] si no existe."""
    return escribir(
        """
        MATCH (:Usuario {id: $a})-[s:SOLICITA_CONEXION]->(:Usuario {id: $b})
        DELETE s
        RETURN $a AS id
        """,
        a=origen_id, b=destino_id,
    )