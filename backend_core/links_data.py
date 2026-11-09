"""Vínculos de un usuario con empresas (TRABAJA_EN) y proyectos (PARTICIPA_EN)."""

from backend_core.portal_common import consultar, escribir


# --- Experiencia en empresas ------------------------------------------------------

def experiencia_usuario(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:TRABAJA_EN]->(e:Empresa)
        RETURN DISTINCT e.id AS id, e.nombre AS empresa, e.sector AS sector,
               r.cargo AS cargo, coalesce(r.es_actual, false) AS actual, r.periodo AS periodo
        ORDER BY actual DESC, empresa
        """,
        id=usuario_id,
    ) or []


def guardar_experiencia(usuario_id, empresa_id, datos):
    """Añade o actualiza el vínculo. Devuelve [] si el usuario o la empresa no existen.

    Usa MERGE: solo puede haber una relación por usuario y empresa.
    """
    return escribir(
        """
        MATCH (u:Usuario {id: $u}), (e:Empresa {id: $e})
        MERGE (u)-[r:TRABAJA_EN]->(e)
        SET r.cargo = $cargo,
            r.es_actual = $actual,
            r.periodo = CASE WHEN trim(coalesce($periodo, '')) = '' THEN null ELSE trim($periodo) END
        RETURN e.id AS id
        """,
        u=usuario_id, e=empresa_id,
        cargo=datos["cargo"], actual=bool(datos["actual"]), periodo=datos.get("periodo"),
    )


def quitar_experiencia(usuario_id, empresa_id):
    """Elimina el vínculo (aunque hubiera repetidos). [] si no existía."""
    return escribir(
        """
        MATCH (:Usuario {id: $u})-[r:TRABAJA_EN]->(e:Empresa {id: $e})
        DELETE r
        RETURN e.id AS id
        """,
        u=usuario_id, e=empresa_id,
    )


# --- Proyectos --------------------------------------------------------------------

def catalogo_proyectos():
    return consultar(
        "MATCH (p:Proyecto) RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion ORDER BY nombre"
    ) or []


def proyectos_usuario(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:PARTICIPA_EN]->(p:Proyecto)
        RETURN DISTINCT p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion, r.rol AS rol
        ORDER BY nombre
        """,
        id=usuario_id,
    ) or []


def guardar_proyecto(usuario_id, proyecto_id, rol):
    """Añade o actualiza la participación. [] si el usuario o el proyecto no existen."""
    return escribir(
        """
        MATCH (u:Usuario {id: $u}), (p:Proyecto {id: $p})
        MERGE (u)-[r:PARTICIPA_EN]->(p)
        SET r.rol = $rol
        RETURN p.id AS id
        """,
        u=usuario_id, p=proyecto_id, rol=rol,
    )


def quitar_proyecto(usuario_id, proyecto_id):
    return escribir(
        """
        MATCH (:Usuario {id: $u})-[r:PARTICIPA_EN]->(p:Proyecto {id: $p})
        DELETE r
        RETURN p.id AS id
        """,
        u=usuario_id, p=proyecto_id,
    )