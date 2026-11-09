"""Operaciones del panel de administración: listados, altas, bajas y permisos de administrador."""

import uuid

from backend_core.portal_common import consultar, escribir

# --- Listados ---------------------------------------------------------------------

def usuarios_admin():
    return consultar(
        """
        MATCH (u:Usuario)
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WITH u, collect(c)[0] AS c
        RETURN u.id AS id, u.nombre AS nombre, u.perfil_profesional AS titular,
               u.correo_contacto AS correo, c.id AS cuenta_id,
               c IS NOT NULL AND coalesce(c.activa, true) AS activa,
               'administrador' IN coalesce(c.roles, []) AS es_admin
        ORDER BY toLower(u.nombre)
        """
    ) or []


def empresas_admin():
    return consultar(
        """
        MATCH (e:Empresa)
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        WITH e, collect(c)[0] AS c
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector,
               e.correo_contacto AS correo, c.id AS cuenta_id,
               c IS NOT NULL AND coalesce(c.activa, true) AS activa,
               count(o) AS ofertas
        ORDER BY toLower(e.nombre)
        """
    ) or []


def ofertas_admin():
    return consultar(
        """
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
        OPTIONAL MATCH (:Usuario)-[p:POSTULA_A]->(o)
        RETURN o.id AS id, o.titulo AS titulo, o.estado AS estado,
               o.modalidad AS modalidad, o.nivel_experiencia AS nivel,
               e.id AS empresa_id, e.nombre AS empresa, count(p) AS postulaciones
        ORDER BY toLower(e.nombre), toLower(o.titulo)
        """
    ) or []


def proyectos_admin():
    return consultar(
        """
        MATCH (p:Proyecto)
        OPTIONAL MATCH (u:Usuario)-[:PARTICIPA_EN]->(p)
        RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion,
               count(DISTINCT u) AS miembros
        ORDER BY toLower(p.nombre)
        """
    ) or []


# --- Cuentas y permisos -----------------------------------------------------------

def cuenta_de_usuario(usuario_id):
    """Cuenta que representa al usuario (id y si está activa), o None."""
    filas = consultar(
        """
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(:Usuario {id: $id})
        RETURN c.id AS cuenta_id, coalesce(c.activa, true) AS activa
        LIMIT 1
        """,
        id=usuario_id,
    )
    return filas[0] if filas else None


def fijar_admin(usuario_id, es_admin):
    """Añade o quita el rol 'administrador' de la cuenta activa del usuario. [] si no la tiene."""
    return escribir(
        """
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(:Usuario {id: $id})
        WHERE coalesce(c.activa, true)
        WITH c, [r IN coalesce(c.roles, [c.rol]) WHERE r <> 'administrador'] AS base
        SET c.roles = CASE WHEN $es_admin THEN base + ['administrador'] ELSE base END,
            c.rol = CASE WHEN c.rol = 'administrador' AND NOT $es_admin THEN 'usuario' ELSE c.rol END
        RETURN c.id AS cuenta_id, 'administrador' IN c.roles AS es_admin
        """,
        id=usuario_id, es_admin=bool(es_admin),
    )


# --- Bajas ------------------------------------------------------------------------
# Eliminar un perfil lo borra del grafo con todas sus relaciones, desactiva su cuenta
# (no podrá iniciar sesión) y cierra sus sesiones. El correo queda libre para el
# administrador (crear_perfil_con_acceso_admin reactiva la cuenta desactivada).

def eliminar_usuario(usuario_id):
    return escribir(
        """
        MATCH (u:Usuario {id: $id})
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        SET c.activa = false, c.auth_version = coalesce(c.auth_version, 0) + 1
        WITH u, collect(c.id) AS cuentas
        OPTIONAL MATCH (s:Sesion) WHERE s.cuenta_id IN cuentas
        DELETE s
        WITH DISTINCT u
        DETACH DELETE u
        RETURN $id AS id
        """,
        id=usuario_id,
    )


def eliminar_empresa(empresa_id):
    """Borra la empresa y también sus ofertas (con las postulaciones que recibieron)."""
    return escribir(
        """
        MATCH (e:Empresa {id: $id})
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        SET c.activa = false, c.auth_version = coalesce(c.auth_version, 0) + 1
        WITH e, collect(c.id) AS cuentas
        OPTIONAL MATCH (s:Sesion) WHERE s.cuenta_id IN cuentas
        DELETE s
        WITH DISTINCT e
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        DETACH DELETE o
        WITH DISTINCT e
        DETACH DELETE e
        RETURN $id AS id
        """,
        id=empresa_id,
    )


def eliminar_oferta(oferta_id):
    return escribir(
        "MATCH (o:Oferta {id: $id}) DETACH DELETE o RETURN $id AS id",
        id=oferta_id,
    )


# --- Proyectos --------------------------------------------------------------------

def crear_proyecto(datos):
    proyecto_id = "P" + uuid.uuid4().hex[:10].upper()
    escribir(
        """
        CREATE (p:Proyecto {id: $id, nombre: $nombre})
        SET p.descripcion = CASE WHEN trim(coalesce($descripcion, '')) = '' THEN null ELSE trim($descripcion) END
        RETURN p.id AS id
        """,
        id=proyecto_id, nombre=datos["nombre"], descripcion=datos.get("descripcion"),
    )
    return proyecto_id


def actualizar_proyecto(proyecto_id, datos):
    return escribir(
        """
        MATCH (p:Proyecto {id: $id})
        SET p.nombre = $nombre,
            p.descripcion = CASE WHEN trim(coalesce($descripcion, '')) = '' THEN null ELSE trim($descripcion) END
        RETURN p.id AS id
        """,
        id=proyecto_id, nombre=datos["nombre"], descripcion=datos.get("descripcion"),
    )


def eliminar_proyecto(proyecto_id):
    return escribir(
        "MATCH (p:Proyecto {id: $id}) DETACH DELETE p RETURN $id AS id",
        id=proyecto_id,
    )