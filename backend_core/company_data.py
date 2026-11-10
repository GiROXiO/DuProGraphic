"""Consultas y operaciones del portal de empresa (sin interfaz). Usadas por la API FastAPI."""

import uuid
from datetime import date

from backend_core.portal_common import consultar, escribir

# Campos del perfil de empresa que ven otras cuentas. El correo de contacto no se publica.
CAMPOS_PUBLICOS_EMPRESA = ("nombre", "sector", "descripcion", "ubicacion", "tamano", "sitio_web")


# --- Perfil -----------------------------------------------------------------------

def perfil_empresa(empresa_id):
    """Perfil visible para cualquier cuenta, o None si la empresa no existe."""
    filas = consultar("MATCH (e:Empresa {id: $id}) RETURN properties(e) AS p", id=empresa_id)
    if not filas:
        return None
    props = filas[0]["p"]
    return {"id": empresa_id, **{c: props.get(c) for c in CAMPOS_PUBLICOS_EMPRESA}}


def actualizar_empresa(empresa_id, datos):
    """Reemplaza los campos editables. Devuelve [] si la empresa no existe."""
    return escribir(
        """
        MATCH (e:Empresa {id: $id})
        SET e.nombre = $nombre,
            e.sector = $sector,
            e.descripcion = CASE WHEN trim(coalesce($descripcion, '')) = '' THEN null ELSE trim($descripcion) END,
            e.ubicacion = CASE WHEN trim(coalesce($ubicacion, '')) = '' THEN null ELSE trim($ubicacion) END,
            e.tamano = $tamano,
            e.sitio_web = CASE WHEN trim(coalesce($sitio_web, '')) = '' THEN null ELSE trim($sitio_web) END
        RETURN e.id AS id
        """,
        id=empresa_id,
        **datos,
    )


# --- Ofertas ----------------------------------------------------------------------

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
            OPTIONAL MATCH (o)-[req:REQUIERE]->(h:Habilidad)
            RETURN collect(DISTINCT h.nombre) AS habilidades,
                   collect(DISTINCT CASE WHEN h IS NULL THEN null ELSE
                       {id: h.id, nombre: h.nombre, obligatoria: coalesce(req.es_obligatoria, true)} END)
                       AS habilidades_detalle
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
               postulaciones, habilidades, habilidades_detalle,
               contrataciones_registradas + postulaciones_aceptadas AS personas_contratadas
        ORDER BY titulo
        """,
        id=empresa_id,
    ) or []


def _obligatorias(habilidades):
    return {h["id"]: bool(h["obligatoria"]) for h in habilidades}


def crear_oferta(empresa_id, datos, habilidades):
    """Publica una oferta abierta con sus habilidades requeridas. Devuelve su id (o None)."""
    oferta_id = "O" + uuid.uuid4().hex[:10].upper()
    filas = escribir(
        """
        MATCH (e:Empresa {id: $e})
        CREATE (o:Oferta {id: $id, titulo: $titulo, estado: 'abierta',
                          modalidad: $modalidad, nivel_experiencia: $nivel_experiencia})
        SET o.descripcion = CASE WHEN trim(coalesce($descripcion, '')) = '' THEN null ELSE trim($descripcion) END
        CREATE (e)-[:PUBLICA {fecha_publicacion: $fecha}]->(o)
        WITH o
        OPTIONAL MATCH (h:Habilidad) WHERE h.id IN $ids
        WITH o, collect(h) AS habs
        FOREACH (h IN habs |
            MERGE (o)-[r:REQUIERE]->(h)
              SET r.es_obligatoria = coalesce($obl[h.id], true)
        )
        RETURN o.id AS id
        """,
        e=empresa_id, id=oferta_id, fecha=date.today().isoformat(),
        titulo=datos["titulo"], descripcion=datos.get("descripcion"),
        modalidad=datos["modalidad"], nivel_experiencia=datos["nivel_experiencia"],
        ids=[h["id"] for h in habilidades], obl=_obligatorias(habilidades),
    )
    return filas[0]["id"] if filas else None


def actualizar_oferta(empresa_id, oferta_id, datos, habilidades):
    """Edita la oferta y deja exactamente las habilidades indicadas. [] si no es de esa empresa."""
    return escribir(
        """
        MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})
        SET o.titulo = $titulo, o.modalidad = $modalidad, o.nivel_experiencia = $nivel_experiencia,
            o.descripcion = CASE WHEN trim(coalesce($descripcion, '')) = '' THEN null ELSE trim($descripcion) END
        WITH o
        OPTIONAL MATCH (o)-[viejo:REQUIERE]->(hv:Habilidad)
        WHERE NOT hv.id IN $ids
        DELETE viejo
        WITH DISTINCT o
        OPTIONAL MATCH (h:Habilidad) WHERE h.id IN $ids
        WITH o, collect(h) AS habs
        FOREACH (h IN habs |
            MERGE (o)-[r:REQUIERE]->(h)
              SET r.es_obligatoria = coalesce($obl[h.id], true)
        )
        RETURN o.id AS id
        """,
        e=empresa_id, o=oferta_id,
        titulo=datos["titulo"], descripcion=datos.get("descripcion"),
        modalidad=datos["modalidad"], nivel_experiencia=datos["nivel_experiencia"],
        ids=[h["id"] for h in habilidades], obl=_obligatorias(habilidades),
    )


def cambiar_estado_oferta(empresa_id, oferta_id, estado):
    """Abre o cierra la oferta. [] si no es de esa empresa."""
    return escribir(
        """
        MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})
        SET o.estado = $estado
        RETURN o.id AS id
        """,
        e=empresa_id, o=oferta_id, estado=estado,
    )