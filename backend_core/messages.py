"""Operaciones de mensajes privados entre cuentas del grafo."""

import hashlib
import uuid
from datetime import datetime, timezone

from backend_core.connection import get_db_connection


def _driver():
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j Aura.")
    return conexion.driver


def _asegurar_restricciones(driver):
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT conversacion_clave_unica IF NOT EXISTS "
            "FOR (c:Conversacion) REQUIRE c.clave IS UNIQUE"
        ).consume()
        session.run(
            "CREATE CONSTRAINT mensaje_id_unico IF NOT EXISTS "
            "FOR (m:Mensaje) REQUIRE m.id IS UNIQUE"
        ).consume()


def listar_destinatarios(cuenta_id):
    with _driver().session() as session:
        return session.run(
            """
            MATCH (c:Cuenta)
            WHERE c.id <> $id
              AND coalesce(c.activa, true)
              AND c.rol IN ['usuario', 'empresa']
            OPTIONAL MATCH (c)-[:REPRESENTA_A]->(perfil)
            RETURN c.id AS id, c.rol AS rol,
                   coalesce(perfil.nombre, c.email_normalizado) AS nombre,
                   perfil.id AS perfil_id
            ORDER BY nombre
            """,
            id=cuenta_id,
        ).data()


def listar_contextos(tipo):
    if tipo == "Proyecto":
        consulta = "MATCH (n:Proyecto) RETURN n.id AS id, n.nombre AS nombre ORDER BY nombre"
    elif tipo == "Oferta":
        consulta = "MATCH (n:Oferta) RETURN n.id AS id, n.titulo AS nombre ORDER BY nombre"
    else:
        return []
    with _driver().session() as session:
        return session.run(consulta).data()


def iniciar_conversacion(origen_id, destino_id, contexto_tipo="General", contexto_id=""):
    if origen_id == destino_id:
        return "destinatario_invalido", None
    if contexto_tipo not in {"General", "Proyecto", "Oferta"}:
        return "contexto_invalido", None
    if contexto_tipo == "General":
        contexto_id = ""
    elif not contexto_id:
        return "contexto_invalido", None

    participantes = "|".join(sorted([origen_id, destino_id]))
    clave = hashlib.sha256(
        f"{participantes}|{contexto_tipo}|{contexto_id}".encode("utf-8")
    ).hexdigest()
    nueva_id = uuid.uuid4().hex
    creada = datetime.now(timezone.utc).isoformat()

    try:
        driver = _driver()
        _asegurar_restricciones(driver)
        if contexto_tipo == "Proyecto":
            contexto_match = "MATCH (ref:Proyecto {id: $contexto_id})"
        elif contexto_tipo == "Oferta":
            contexto_match = "MATCH (ref:Oferta {id: $contexto_id})"
        else:
            contexto_match = ""

        consulta = f"""
        MATCH (origen:Cuenta {{id: $origen_id}}), (destino:Cuenta {{id: $destino_id}})
        {contexto_match}
        WHERE coalesce(origen.activa, true)
          AND coalesce(destino.activa, true)
          AND origen.rol IN ['usuario', 'empresa']
          AND destino.rol IN ['usuario', 'empresa']
        MERGE (c:Conversacion {{clave: $clave}})
        ON CREATE SET c.id = $id, c.creada = $creada,
                      c.contexto_tipo = $contexto_tipo,
                      c.contexto_id = $contexto_id
        MERGE (c)-[:INCLUYE]->(origen)
        MERGE (c)-[:INCLUYE]->(destino)
        """
        if contexto_tipo != "General":
            consulta += "MERGE (c)-[:SOBRE]->(ref)\n"
        consulta += "RETURN c.id AS id"

        with driver.session() as session:
            resultado = session.run(
                consulta,
                origen_id=origen_id,
                destino_id=destino_id,
                contexto_id=contexto_id,
                contexto_tipo=contexto_tipo,
                clave=clave,
                id=nueva_id,
                creada=creada,
            ).single()
        return ("abierta", resultado["id"]) if resultado else ("no_encontrada", None)
    except Exception:
        return "error_bd", None


def obtener_conversaciones(cuenta_id):
    with _driver().session() as session:
        return session.run(
            """
            MATCH (c:Conversacion)-[:INCLUYE]->(:Cuenta {id: $id})
            MATCH (c)-[:INCLUYE]->(otro:Cuenta)
            WHERE otro.id <> $id
            OPTIONAL MATCH (otro)-[:REPRESENTA_A]->(perfil)
            OPTIONAL MATCH (c)-[:SOBRE]->(tema)
            OPTIONAL MATCH (c)-[:CONTIENE]->(m:Mensaje)
            WITH c, otro, perfil, tema, m ORDER BY m.fecha DESC
            WITH c, otro, perfil, tema, head(collect(m)) AS ultimo
            RETURN c.id AS id, c.contexto_tipo AS contexto_tipo,
                   c.contexto_id AS contexto_id,
                   coalesce(tema.nombre, tema.titulo, c.contexto_id) AS contexto_nombre,
                   coalesce(perfil.nombre, otro.email_normalizado) AS contacto,
                   otro.rol AS rol_contacto,
                   ultimo.texto AS ultimo_mensaje,
                   coalesce(ultimo.fecha, c.creada) AS actividad
            ORDER BY actividad DESC
            """,
            id=cuenta_id,
        ).data()


def obtener_mensajes(conversacion_id, cuenta_id):
    with _driver().session() as session:
        filas = session.run(
            """
            MATCH (c:Conversacion {id: $conversacion_id})-[:INCLUYE]->(:Cuenta {id: $cuenta_id})
            OPTIONAL MATCH (c)-[:CONTIENE]->(m:Mensaje)
            OPTIONAL MATCH (m)-[:ENVIADO_POR]->(autor:Cuenta)
            OPTIONAL MATCH (autor)-[:REPRESENTA_A]->(perfil)
            RETURN m.id AS id, m.texto AS texto, m.fecha AS fecha,
                   autor.id AS autor_id,
                   coalesce(perfil.nombre, autor.email_normalizado, '') AS autor
            ORDER BY fecha
            """,
            conversacion_id=conversacion_id,
            cuenta_id=cuenta_id,
        ).data()
    return [fila for fila in filas if fila["id"]]


def enviar_mensaje(conversacion_id, cuenta_id, texto):
    texto = (texto or "").strip()
    if not texto:
        return "vacio"
    if len(texto) > 3000:
        return "largo"

    try:
        with _driver().session() as session:
            resultado = session.run(
                """
                MATCH (c:Conversacion {id: $conversacion_id})-[:INCLUYE]->(autor:Cuenta {id: $cuenta_id})
                WHERE coalesce(autor.activa, true)
                CREATE (m:Mensaje {
                    id: $id, texto: $texto,
                    fecha: $fecha
                })
                CREATE (c)-[:CONTIENE]->(m)
                CREATE (m)-[:ENVIADO_POR]->(autor)
                RETURN m.id AS id
                """,
                conversacion_id=conversacion_id,
                cuenta_id=cuenta_id,
                id=uuid.uuid4().hex,
                texto=texto,
                fecha=datetime.now(timezone.utc).isoformat(),
            ).single()
        return "enviado" if resultado else "sin_acceso"
    except Exception:
        return "error_bd"
