"""Asocia correos y sincroniza el usuario de Cuenta, si ya existe."""

import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from backend_core.auth import correo_valido, normalizar_correo

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
ASOCIACIONES = [
    ("U2", "Juan Cáceres", "PERFIL_EMAIL_U2"),
    ("U1", "Jerónimo Castro", "PERFIL_EMAIL_U1"),
    ("U3", "Juan Arrieta", "PERFIL_EMAIL_U3"),
    ("U4", "Miguel Carrizosa", "PERFIL_EMAIL_U4"),
]


def asociar(tx, perfiles):
    resultados = []
    for perfil_id, nombre, correo in perfiles:
        actual = tx.run(
            """
            MATCH (u:Usuario {id: $id})
            OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
            RETURN u.nombre AS nombre, u.correo_contacto AS correo,
                   collect(c.id) AS cuentas, collect(c.email_normalizado) AS correos_cuenta
            """,
            id=perfil_id,
        ).single()
        if actual is None or actual["nombre"] != nombre:
            raise ValueError(f"No coincide el perfil esperado para {perfil_id}; no se aplicaron cambios.")
        cuenta_ids = [item for item in actual["cuentas"] if item]
        correos_cuenta = [item for item in actual["correos_cuenta"] if item]
        if len(cuenta_ids) > 1:
            raise ValueError(f"El perfil {perfil_id} tiene varias cuentas asociadas.")

        duplicado_perfil = tx.run(
            """
            MATCH (otro)
            WHERE (otro:Usuario OR otro:Empresa)
              AND toLower(trim(coalesce(otro.correo_contacto, ''))) = $correo
              AND otro.id <> $id
            RETURN otro.id AS id LIMIT 1
            """,
            correo=correo,
            id=perfil_id,
        ).single()
        if duplicado_perfil:
            raise ValueError("Uno de los correos ya pertenece a otro perfil; no se aplicaron cambios.")

        cuenta_destino = tx.run(
            "MATCH (c:Cuenta {email_normalizado: $correo}) RETURN c.id AS id LIMIT 1",
            correo=correo,
        ).single()
        if cuenta_destino and cuenta_destino["id"] not in cuenta_ids:
            raise ValueError("Uno de los correos ya pertenece a otra cuenta; no se aplicaron cambios.")

        cuenta_id = cuenta_ids[0] if cuenta_ids else None
        correo_actual = (actual["correo"] or "").strip().lower()
        correo_cuenta_actual = (correos_cuenta[0] or "").strip().lower() if correos_cuenta else ""
        if cuenta_id and correo_cuenta_actual != correo:
            tx.run(
                """
                MATCH (c:Cuenta {id: $id})
                SET c.email = $correo,
                    c.email_normalizado = $correo,
                    c.auth_version = coalesce(c.auth_version, 0) + 1
                """,
                id=cuenta_id,
                correo=correo,
            ).consume()
        if correo_actual != correo:
            tx.run(
                "MATCH (u:Usuario {id: $id}) SET u.correo_contacto = $correo",
                id=perfil_id,
                correo=correo,
            ).consume()
        resultados.append(perfil_id)
    return resultados


def main():
    if not URI or not all(AUTH):
        raise SystemExit("Faltan NEO4J_URI, NEO4J_USER o NEO4J_PASSWORD en .env.")

    perfiles = []
    for perfil_id, nombre, variable in ASOCIACIONES:
        correo = normalizar_correo(os.getenv(variable))
        if not correo_valido(correo):
            raise SystemExit(f"Configura un correo válido en {variable} antes de ejecutar esta asociacion.")
        perfiles.append((perfil_id, nombre, correo))
    if len({correo for _, _, correo in perfiles}) != len(perfiles):
        raise SystemExit("Las variables PERFIL_EMAIL_U1 a U4 deben contener correos diferentes.")

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT usuario_correo_unico IF NOT EXISTS "
                "FOR (u:Usuario) REQUIRE u.correo_contacto IS UNIQUE"
            ).consume()
            session.run(
                "CREATE CONSTRAINT empresa_correo_unico IF NOT EXISTS "
                "FOR (e:Empresa) REQUIRE e.correo_contacto IS UNIQUE"
            ).consume()
            asociados = session.execute_write(asociar, perfiles)

    for perfil_id in asociados:
        print(f"Correo asociado y sincronizado para el perfil {perfil_id}.")


if __name__ == "__main__":
    main()
