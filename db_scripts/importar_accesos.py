"""Importa usuarios y empresas desde un CSV local sin guardar claves en el repositorio."""

import argparse
import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from neo4j import GraphDatabase

from backend_core.auth import (
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    _nueva_credencial,
    correo_valido,
    normalizar_correo,
)


HEADERS = {
    "Tipo de perfil",
    "ID perfil",
    "Nombre",
    "Correo / usuario",
    "Rol(es) habilitados",
    "Contraseña",
}


def parsear_roles(tipo, valor):
    normalizado = " ".join((valor or "").strip().lower().split())
    if tipo == "Usuario":
        if "usuario" not in normalizado:
            raise ValueError("Una fila de tipo Usuario debe incluir el rol Usuario.")
        return [ROL_USUARIO, ROL_ADMIN] if "administrador" in normalizado else [ROL_USUARIO]
    if tipo == "Empresa":
        if normalizado not in {"empresa", "empresa / reclutador"}:
            raise ValueError("Una fila de tipo Empresa solo puede usar el rol Empresa.")
        return [ROL_EMPRESA]
    raise ValueError("Tipo de perfil no válido; usa Usuario o Empresa.")



def leer_csv(ruta):
    filas = []
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo)
        contenido = list(lector)
    encabezado_idx = next(
        (
            indice for indice, fila in enumerate(contenido[:12])
            if HEADERS.issubset({valor.strip() for valor in fila if valor.strip()})
        ),
        None,
    )
    if encabezado_idx is None:
        raise ValueError("No encontré la fila de encabezados requerida en el CSV.")
    encabezados = [valor.strip() for valor in contenido[encabezado_idx]]
    faltantes = sorted(HEADERS - set(encabezados))
    if faltantes:
        raise ValueError("Faltan columnas requeridas: " + ", ".join(faltantes))

    for numero, valores in enumerate(contenido[encabezado_idx + 1:], start=encabezado_idx + 2):
        if not any(valor.strip() for valor in valores):
            break
        fila = dict(zip(encabezados, valores))
        if (fila.get("Tipo de perfil") or "").strip().lower().startswith("nota:"):
            break
        tipo = (fila.get("Tipo de perfil") or "").strip()
        perfil_id = (fila.get("ID perfil") or "").strip()
        nombre = (fila.get("Nombre") or "").strip()
        correo = normalizar_correo(fila.get("Correo / usuario"))
        roles = parsear_roles(tipo, fila.get("Rol(es) habilitados"))
        password = fila.get("Contraseña") or ""
        prefijo = "U" if tipo == "Usuario" else "E"
        if not perfil_id.startswith(prefijo) or not nombre:
            raise ValueError(f"ID o nombre inválido en la fila {numero}.")
        if not correo_valido(correo):
            raise ValueError(f"Correo inválido en la fila {numero}.")
        if len(password) < 10:
            raise ValueError(
                f"La contraseña de la fila {numero} debe tener al menos 10 caracteres."
            )
        filas.append({
            "tipo": tipo,
            "label": tipo,
            "perfil_id": perfil_id,
            "nombre": nombre,
            "correo": correo,
            "roles": roles,
            "rol": ROL_EMPRESA if tipo == "Empresa" else ROL_USUARIO,
            "password": password,
        })

    if not filas:
        raise ValueError("El CSV no contiene cuentas.")
    if len({fila["perfil_id"] for fila in filas}) != len(filas):
        raise ValueError("El CSV contiene IDs de perfil repetidos.")
    if len({fila["correo"] for fila in filas}) != len(filas):
        raise ValueError("El CSV contiene correos repetidos.")
    return filas


def asegurar_restricciones(session):
    session.run(
        "CREATE CONSTRAINT cuenta_email_unico IF NOT EXISTS "
        "FOR (c:Cuenta) REQUIRE c.email_normalizado IS UNIQUE"
    ).consume()
    session.run(
        "CREATE CONSTRAINT usuario_correo_unico IF NOT EXISTS "
        "FOR (u:Usuario) REQUIRE u.correo_contacto IS UNIQUE"
    ).consume()
    session.run(
        "CREATE CONSTRAINT empresa_correo_unico IF NOT EXISTS "
        "FOR (e:Empresa) REQUIRE e.correo_contacto IS UNIQUE"
    ).consume()


def importar(tx, filas, reemplazar_passwords):
    creadas = 0
    existentes = 0
    roles_actualizados = 0
    claves_reemplazadas = 0

    for fila in filas:
        label = fila["label"]
        perfil = tx.run(
            f"MATCH (p:{label} {{id: $id}}) "
            "RETURN p.nombre AS nombre, p.correo_contacto AS correo",
            id=fila["perfil_id"],
        ).single()
        if not perfil:
            raise ValueError(
                f"No existe el perfil {fila['perfil_id']}. Ejecuta primero init_db.py."
            )
        if perfil["nombre"] != fila["nombre"]:
            raise ValueError(
                f"El nombre de {fila['perfil_id']} no coincide con la base; revisa la fila del CSV."
            )
        correo_perfil = normalizar_correo(perfil["correo"])
        if correo_perfil and correo_perfil != fila["correo"]:
            raise ValueError(
                f"El correo del perfil {fila['perfil_id']} no coincide con el CSV."
            )

        enlace = tx.run(
            f"""
            MATCH (p:{label} {{id: $id}})
            OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(p)
            RETURN collect(c.id) AS ids,
                   collect(c.email_normalizado) AS correos,
                   collect(coalesce(c.roles, [c.rol])) AS roles,
                   collect(coalesce(c.activa, true)) AS activas,
                   collect(coalesce(c.password_hash, '')) AS hashes
            """,
            id=fila["perfil_id"],
        ).single()
        ids = [valor for valor in enlace["ids"] if valor]
        if len(ids) > 1:
            raise ValueError(f"El perfil {fila['perfil_id']} está enlazado a varias cuentas.")

        salt, password_hash = _nueva_credencial(fila["password"])
        fecha = datetime.now(timezone.utc).isoformat()

        if ids:
            correo_actual = enlace["correos"][0]
            if correo_actual != fila["correo"]:
                raise ValueError(
                    f"La cuenta de {fila['perfil_id']} ya usa otro correo; no se modificó."
                )
            cuenta_email = tx.run(
                """
                MATCH (c:Cuenta {email_normalizado: $correo})
                RETURN c.id AS id
                """,
                correo=fila["correo"],
            ).single()
            if not cuenta_email or cuenta_email["id"] != ids[0]:
                raise ValueError(f"El correo de {fila['perfil_id']} pertenece a otra cuenta.")

            roles_actuales = list(enlace["roles"][0] or [])
            hash_actual = enlace["hashes"][0]
            cambio_rol = set(roles_actuales) != set(fila["roles"])
            cambio_clave = reemplazar_passwords or not hash_actual
            sets = [
                "c.email = $correo",
                "c.email_normalizado = $correo",
                "p.correo_contacto = $correo",
                "c.rol = $rol",
                "c.roles = $roles",
            ]
            if cambio_rol or cambio_clave:
                sets.append("c.auth_version = coalesce(c.auth_version, 0) + 1")
            if cambio_clave:
                sets.extend([
                    "c.password_salt = $salt",
                    "c.password_hash = $hash",
                    "c.password_actualizada = $fecha",
                ])
            if cambio_rol:
                roles_actualizados += 1
            if cambio_clave:
                claves_reemplazadas += 1
            tx.run(
                f"""
                MATCH (c:Cuenta {{id: $cuenta_id}})-[:REPRESENTA_A]->(p:{label} {{id: $perfil_id}})
                SET {", ".join(sets)}
                """,
                cuenta_id=ids[0],
                perfil_id=fila["perfil_id"],
                correo=fila["correo"],
                rol=fila["rol"],
                roles=fila["roles"],
                salt=salt,
                hash=password_hash,
                fecha=fecha,
            ).consume()
            existentes += 1
            continue

        ocupada = tx.run(
            "MATCH (c:Cuenta {email_normalizado: $correo}) RETURN c.id AS id",
            correo=fila["correo"],
        ).single()
        if ocupada:
            raise ValueError(f"El correo de {fila['perfil_id']} ya está asignado a otra cuenta.")
        duplicado = tx.run(
            """
            MATCH (otro)
            WHERE (otro:Usuario OR otro:Empresa)
              AND toLower(trim(coalesce(otro.correo_contacto, ''))) = $correo
              AND otro.id <> $id
            RETURN otro.id AS id LIMIT 1
            """,
            correo=fila["correo"],
            id=fila["perfil_id"],
        ).single()
        if duplicado:
            raise ValueError(f"El correo de {fila['perfil_id']} pertenece a otro perfil.")

        tx.run(
            f"""
            MATCH (p:{label} {{id: $perfil_id}})
            CREATE (c:Cuenta {{
                id: $cuenta_id,
                email: $correo,
                email_normalizado: $correo,
                password_salt: $salt,
                password_hash: $hash,
                rol: $rol,
                roles: $roles,
                activa: true,
                auth_version: 0,
                fecha_creacion: $fecha
            }})
            SET p.correo_contacto = $correo
            CREATE (c)-[:REPRESENTA_A]->(p)
            """,
            perfil_id=fila["perfil_id"],
            cuenta_id=uuid.uuid4().hex,
            correo=fila["correo"],
            salt=salt,
            hash=password_hash,
            rol=fila["rol"],
            roles=fila["roles"],
            fecha=fecha,
        ).consume()
        creadas += 1

    return creadas, existentes, roles_actualizados, claves_reemplazadas


def main():
    parser = argparse.ArgumentParser(
        description="Relaciona cuentas de usuario y empresa con perfiles ya sembrados en Neo4j."
    )
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(ROOT / "db_scripts" / "accesos_demo.csv"),
        help="CSV local exportado desde la hoja Accesos del Excel.",
    )
    parser.add_argument(
        "--reemplazar-claves",
        action="store_true",
        help="Vuelve a guardar las contraseñas incluidas en el CSV para cuentas ya existentes.",
    )
    args = parser.parse_args()
    ruta = Path(args.csv).expanduser().resolve()
    if not ruta.is_file():
        raise SystemExit(
            f"No se encontró {ruta}. Exporta la hoja Accesos como CSV UTF-8; "
            "el archivo local está excluido de Git."
        )

    load_dotenv(ROOT / ".env")
    uri = os.getenv("NEO4J_URI")
    auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    if not uri or not all(auth):
        raise SystemExit("Faltan NEO4J_URI, NEO4J_USER o NEO4J_PASSWORD en .env.")

    filas = leer_csv(ruta)
    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            asegurar_restricciones(session)
            resultado = session.execute_write(importar, filas, args.reemplazar_claves)

    creadas, existentes, roles_actualizados, claves_reemplazadas = resultado
    print(
        f"Perfiles revisados: {len(filas)}; cuentas creadas: {creadas}; "
        f"cuentas existentes: {existentes}; roles sincronizados: {roles_actualizados}; "
        f"claves reemplazadas: {claves_reemplazadas}."
    )


if __name__ == "__main__":
    main()

