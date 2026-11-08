"""Autenticacion y registro de cuentas para los roles de DuProGraphic."""

import hashlib
import hmac
import os
import re
import secrets
import uuid
import time
import logging
from urllib.parse import urlsplit
from threading import Lock
from datetime import datetime, timedelta, timezone

from backend_core.connection import get_db_connection

logger = logging.getLogger(__name__)

ROL_USUARIO = "usuario"
ROL_EMPRESA = "empresa"
ROL_ADMIN = "administrador"
ROLES_PUBLICOS = {ROL_USUARIO, ROL_EMPRESA}
ITERACIONES_HASH = 310_000
SESSION_TTL_SECONDS = 14 * 24 * 60 * 60
MAX_PASSWORD_LENGTH = 256
MAX_EMAIL_LENGTH = 254
MAX_PROFILE_LENGTHS = {
    "perfil_profesional": 180,
    "universidad": 160,
    "sector": 120,
    "ubicacion": 120,
    "acerca_de": 1200,
    "educacion_detalle": 160,
    "areas_interes": 180,
    "experiencia": 1400,
    "logros": 700,
    "idiomas": 180,
    "sitio_portafolio": 240,
    "descripcion": 1200,
    "sitio_web": 240,
    "tamano": 80,
}

MAX_INTENTOS_LOGIN = 5
VENTANA_LOGIN_SEGUNDOS = 300
BLOQUEO_LOGIN_SEGUNDOS = 300
_INTENTOS_LOGIN = {}
_INTENTOS_LOGIN_LOCK = Lock()
_SAL_DUMMY = bytes(16)
_HASH_DUMMY = hashlib.pbkdf2_hmac(
    "sha256", b"duprographic-invalid-login", _SAL_DUMMY, ITERACIONES_HASH
).hex()


def normalizar_correo(correo):
    return str(correo or "").strip().lower()


def correo_valido(correo):
    correo = normalizar_correo(correo)
    if len(correo) > MAX_EMAIL_LENGTH or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return False
    local, dominio = correo.rsplit("@", 1)
    etiquetas = dominio.split(".")
    return (
        len(local) <= 64
        and not local.startswith(".")
        and not local.endswith(".")
        and ".." not in local
        and all(
            1 <= len(etiqueta) <= 63
            and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", etiqueta)
            for etiqueta in etiquetas
        )
    )


def url_http_valida(url):
    """Acepta enlaces web completos y rechaza esquemas u hosts ambiguos."""
    valor = str(url or "").strip()
    if not valor:
        return True
    if any(caracter.isspace() or ord(caracter) < 32 for caracter in valor):
        return False
    try:
        partes = urlsplit(valor)
        puerto = partes.port
        return (
            len(valor) <= 240
            and partes.scheme.lower() in {"http", "https"}
            and bool(partes.hostname)
            and partes.username is None
            and partes.password is None
            and (puerto is None or 1 <= puerto <= 65535)
        )
    except ValueError:
        return False


def _validar_password(password):
    if not isinstance(password, str) or len(password) < 10:
        return "password_corto"
    if len(password) > MAX_PASSWORD_LENGTH:
        return "password_largo"
    try:
        password.encode("utf-8")
    except UnicodeEncodeError:
        return "datos_invalidos"
    return None


def _validar_perfil(rol, perfil):
    if not isinstance(perfil, dict):
        return "datos_invalidos"
    nombre = str(perfil.get("nombre") or "").strip()
    if not nombre:
        return "nombre_vacio"
    if len(nombre) > 140:
        return "datos_invalidos"

    for propiedad, limite in MAX_PROFILE_LENGTHS.items():
        valor = str(perfil.get(propiedad) or "").strip()
        if len(valor) > limite:
            return "datos_invalidos"
        if propiedad in {"sitio_portafolio", "sitio_web"} and not url_http_valida(valor):
            return "url_invalida"

    if rol == ROL_USUARIO:
        titular = str(perfil.get("perfil_profesional") or "").strip()
        if not titular:
            return "perfil_incompleto"
        modalidad = str(perfil.get("modalidad_preferida") or "").strip()
        if modalidad not in {"", "remoto", "híbrido", "presencial"}:
            return "datos_invalidos"
        try:
            valor_anios = perfil.get("anios_experiencia") or 0
            anios = int(valor_anios)
            if float(valor_anios) != anios:
                return "datos_invalidos"
        except (TypeError, ValueError, OverflowError):
            return "datos_invalidos"
        if anios < 0 or anios > 50:
            return "datos_invalidos"
    elif rol == ROL_EMPRESA:
        if not str(perfil.get("sector") or "").strip():
            return "perfil_incompleto"
    return None


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERACIONES_HASH
    ).hex()


def _nueva_credencial(password):
    salt = secrets.token_bytes(16)
    return salt.hex(), _hash_password(password, salt)


def _driver():
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j Aura.")
    return conexion.driver


def _asegurar_restriccion(driver):
    with driver.session() as session:
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



def _codigo_activacion_correcto(codigo, perfil_existente):
    if (
        not isinstance(codigo, str)
        or not codigo
        or len(codigo) > 128
        or not perfil_existente["codigo_hash"]
        or not perfil_existente["codigo_expira"]
    ):
        return False
    esperado = hashlib.sha256(codigo.strip().encode("utf-8")).hexdigest()
    try:
        expira = datetime.fromisoformat(perfil_existente["codigo_expira"])
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        activo = expira > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False
    return activo and hmac.compare_digest(esperado, perfil_existente["codigo_hash"])


def registrar_cuenta(rol, correo, password, perfil, codigo_activacion=""):
    """Registra una cuenta nueva o reclama un perfil ya existente con código."""
    if not isinstance(rol, str) or rol not in ROLES_PUBLICOS:
        return "rol_no_permitido", None

    correo = normalizar_correo(correo)
    if not correo_valido(correo):
        return "correo_invalido", None
    error_password = _validar_password(password)
    if error_password:
        return error_password, None
    error_perfil = _validar_perfil(rol, perfil)
    if error_perfil:
        return error_perfil, None

    nombre = str(perfil.get("nombre") or "").strip()

    salt_hex, password_hash = _nueva_credencial(password)
    cuenta_id = uuid.uuid4().hex
    perfil_id = ("U" if rol == ROL_USUARIO else "E") + uuid.uuid4().hex[:10].upper()
    creado = datetime.now(timezone.utc).isoformat()
    etiqueta = "Usuario" if rol == ROL_USUARIO else "Empresa"
    otro_tipo = "Empresa" if rol == ROL_USUARIO else "Usuario"
    if rol == ROL_USUARIO:
        extras = {
            clave: str(perfil.get(clave) or "").strip()
            for clave in (
                "ubicacion", "acerca_de", "educacion_detalle", "areas_interes",
                "experiencia", "logros", "idiomas", "sitio_portafolio",
            )
            if str(perfil.get(clave) or "").strip()
        }
        modalidad = str(perfil.get("modalidad_preferida") or "").strip()
        if modalidad:
            extras["modalidad_preferida"] = modalidad
        try:
            anios = int(perfil.get("anios_experiencia") or 0)
        except (TypeError, ValueError):
            anios = 0
        if perfil.get("anios_experiencia") is not None:
            extras["anios_experiencia"] = max(0, min(50, anios))
    else:
        extras = {
            clave: str(perfil.get(clave) or "").strip()
            for clave in ("ubicacion", "descripcion", "sitio_web", "tamano")
            if str(perfil.get(clave) or "").strip()
        }

    try:
        driver = _driver()
        _asegurar_restriccion(driver)

        def crear(tx):
            existente = tx.run(
                "MATCH (c:Cuenta {email_normalizado: $correo}) RETURN c.id AS id",
                correo=correo,
            ).single()
            if existente:
                return "correo_existente", None

            otro_perfil = tx.run(
                f"MATCH (p:{otro_tipo} {{correo_contacto: $correo}}) RETURN p.id AS id LIMIT 1",
                correo=correo,
            ).single()
            if otro_perfil:
                return "correo_perfil_usuario" if rol == ROL_EMPRESA else "correo_perfil_empresa", None

            preexistente = tx.run(
                f"""
                MATCH (p:{etiqueta} {{correo_contacto: $correo}})
                OPTIONAL MATCH (otra:Cuenta)-[:REPRESENTA_A]->(p)
                RETURN p.id AS id, p.nombre AS nombre, count(otra) AS cuentas,
                       p.codigo_activacion_hash AS codigo_hash,
                       p.codigo_activacion_expira AS codigo_expira
                LIMIT 1
                """,
                correo=correo,
            ).single()

            if preexistente and preexistente["cuentas"]:
                return "perfil_ya_vinculado", None
            if preexistente and not _codigo_activacion_correcto(codigo_activacion, preexistente):
                return "codigo_requerido", None

            if preexistente:
                consulta = f"""
                MATCH (p:{etiqueta} {{id: $perfil_existente}})
                CREATE (c:Cuenta {{
                    id: $cuenta_id, email: $correo, email_normalizado: $correo,
                    password_salt: $salt, password_hash: $hash,
                    rol: $rol, roles: [$rol], activa: true, auth_version: 0,
                    fecha_creacion: $creado
                }})
                CREATE (c)-[:REPRESENTA_A]->(p)
                REMOVE p.codigo_activacion_hash, p.codigo_activacion_expira
                SET p += $extras
                RETURN c.id AS id, c.email_normalizado AS correo, c.rol AS rol,
                       c.roles AS roles, p.id AS entidad_id, p.nombre AS nombre
                """
                parametros = {"perfil_existente": preexistente["id"]}
            elif rol == ROL_USUARIO:
                consulta = """
                CREATE (c:Cuenta {
                    id: $cuenta_id, email: $correo, email_normalizado: $correo,
                    password_salt: $salt, password_hash: $hash,
                    rol: $rol, roles: [$rol], activa: true, auth_version: 0,
                    fecha_creacion: $creado
                })
                CREATE (p:Usuario {
                    id: $perfil_id, nombre: $nombre,
                    perfil_profesional: $detalle, universidad: $universidad,
                    correo_contacto: $correo
                })
                SET p += $extras
                CREATE (c)-[:REPRESENTA_A]->(p)
                RETURN c.id AS id, c.email_normalizado AS correo, c.rol AS rol,
                       c.roles AS roles, p.id AS entidad_id, p.nombre AS nombre
                """
                parametros = {
                    "detalle": (perfil.get("perfil_profesional") or "").strip(),
                    "universidad": (perfil.get("universidad") or "").strip(),
                }
            else:
                consulta = """
                CREATE (c:Cuenta {
                    id: $cuenta_id, email: $correo, email_normalizado: $correo,
                    password_salt: $salt, password_hash: $hash,
                    rol: $rol, roles: [$rol], activa: true, auth_version: 0,
                    fecha_creacion: $creado
                })
                CREATE (p:Empresa {
                    id: $perfil_id, nombre: $nombre, sector: $detalle,
                    correo_contacto: $correo
                })
                    SET p += $extras
                CREATE (c)-[:REPRESENTA_A]->(p)
                RETURN c.id AS id, c.email_normalizado AS correo, c.rol AS rol,
                       c.roles AS roles, p.id AS entidad_id, p.nombre AS nombre
                """
                parametros = {"detalle": (perfil.get("sector") or "").strip()}

            resultado = tx.run(
                consulta,
                cuenta_id=cuenta_id,
                correo=correo,
                salt=salt_hex,
                hash=password_hash,
                rol=rol,
                creado=creado,
                perfil_id=perfil_id,
                nombre=nombre,
                extras=extras,
                **parametros,
            ).single()
            if resultado is None:
                return "error_bd", None
            estado = "creada_perfil_existente" if preexistente else "creada"
            return estado, dict(resultado)

        with driver.session() as session:
            return session.execute_write(crear)
    except Exception:
        return "error_bd", None



def crear_perfil_con_acceso_admin(rol, correo, password, perfil_id, perfil):
    """Crea un perfil con cuenta o recupera una cuenta desactivada sin historial borrado."""
    if not isinstance(rol, str) or rol not in ROLES_PUBLICOS:
        return "rol_no_permitido", None
    correo = normalizar_correo(correo)
    perfil_id = str(perfil_id or "").strip()
    if not correo_valido(correo):
        return "correo_invalido", None
    error_password = _validar_password(password)
    if error_password:
        return error_password, None
    error_perfil = _validar_perfil(rol, perfil)
    if error_perfil:
        return error_perfil, None
    nombre = str(perfil.get("nombre") or "").strip()
    if not perfil_id or not nombre:
        return "datos_incompletos", None

    etiqueta = "Usuario" if rol == ROL_USUARIO else "Empresa"
    prefijo = "U" if rol == ROL_USUARIO else "E"
    if not re.fullmatch(rf"{prefijo}[A-Za-z0-9_-]{{1,63}}", perfil_id):
        return "id_invalido", None
    detalle = (
        (perfil.get("perfil_profesional") or "").strip()
        if rol == ROL_USUARIO
        else (perfil.get("sector") or "").strip()
    )
    universidad = (perfil.get("universidad") or "").strip()
    salt_hex, password_hash = _nueva_credencial(password)
    creado = datetime.now(timezone.utc).isoformat()
    cuenta_id = uuid.uuid4().hex

    try:
        driver = _driver()
        _asegurar_restriccion(driver)

        def crear(tx):
            if tx.run(
                f"MATCH (p:{etiqueta} {{id: $perfil_id}}) RETURN p.id AS id",
                perfil_id=perfil_id,
            ).single():
                return "id_existente", None
            if tx.run(
                """
                MATCH (p)
                WHERE (p:Usuario OR p:Empresa)
                  AND toLower(trim(coalesce(p.correo_contacto, ''))) = $correo
                RETURN p.id AS id LIMIT 1
                """,
                correo=correo,
            ).single():
                return "correo_perfil_existente", None

            anterior = tx.run(
                """
                MATCH (c:Cuenta {email_normalizado: $correo})
                OPTIONAL MATCH (c)-[:REPRESENTA_A]->(p)
                RETURN c.id AS id, coalesce(c.activa, true) AS activa,
                       collect(p.id) AS perfiles
                """,
                correo=correo,
            ).single()
            if anterior and anterior["activa"]:
                return "correo_existente", None
            if anterior and any(anterior["perfiles"]):
                return "correo_existente", None

            if rol == ROL_USUARIO:
                crear_perfil = """
                CREATE (p:Usuario {
                    id: $perfil_id, nombre: $nombre,
                    perfil_profesional: $detalle, universidad: $universidad,
                    correo_contacto: $correo
                })
                """
            else:
                crear_perfil = """
                CREATE (p:Empresa {
                    id: $perfil_id, nombre: $nombre, sector: $detalle,
                    correo_contacto: $correo
                })
                """

            if anterior:
                consulta = crear_perfil + """
                WITH p
                MATCH (c:Cuenta {id: $cuenta_id})
                SET c.email = $correo, c.email_normalizado = $correo,
                    c.password_salt = $salt, c.password_hash = $hash,
                    c.rol = $rol, c.roles = [$rol], c.activa = true,
                    c.auth_version = coalesce(c.auth_version, 0) + 1,
                    c.password_actualizada = $creado
                CREATE (c)-[:REPRESENTA_A]->(p)
                RETURN p.id AS entidad_id, p.nombre AS nombre, c.id AS id
                """
                cuenta_id_uso = anterior["id"]
            else:
                consulta = crear_perfil + """
                WITH p
                CREATE (c:Cuenta {
                    id: $cuenta_id, email: $correo, email_normalizado: $correo,
                    password_salt: $salt, password_hash: $hash,
                    rol: $rol, roles: [$rol], activa: true, auth_version: 0,
                    fecha_creacion: $creado
                })
                CREATE (c)-[:REPRESENTA_A]->(p)
                RETURN p.id AS entidad_id, p.nombre AS nombre, c.id AS id
                """
                cuenta_id_uso = cuenta_id

            resultado = tx.run(
                consulta,
                perfil_id=perfil_id,
                nombre=nombre,
                detalle=detalle,
                universidad=universidad,
                correo=correo,
                cuenta_id=cuenta_id_uso,
                salt=salt_hex,
                hash=password_hash,
                rol=rol,
                creado=creado,
            ).single()
            return ("creada", dict(resultado)) if resultado else ("error_bd", None)

        with driver.session() as session:
            return session.execute_write(crear)
    except Exception:
        return "error_bd", None



def segundos_bloqueo_login(correo):
    correo = normalizar_correo(correo)
    ahora = time.monotonic()
    with _INTENTOS_LOGIN_LOCK:
        intento = _INTENTOS_LOGIN.get(correo)
        if not intento:
            return 0
        restante = intento.get("bloqueado_hasta", 0) - ahora
        return max(0, int(restante + 0.999))


def _registrar_intento_login(correo, correcto):
    ahora = time.monotonic()
    with _INTENTOS_LOGIN_LOCK:
        if correcto:
            _INTENTOS_LOGIN.pop(correo, None)
            return
        intento = _INTENTOS_LOGIN.setdefault(correo, {"fallos": [], "bloqueado_hasta": 0})
        intento["fallos"] = [
            momento for momento in intento["fallos"]
            if ahora - momento < VENTANA_LOGIN_SEGUNDOS
        ]
        intento["fallos"].append(ahora)
        if len(intento["fallos"]) >= MAX_INTENTOS_LOGIN:
            intento["bloqueado_hasta"] = ahora + BLOQUEO_LOGIN_SEGUNDOS
            intento["fallos"] = []
        if len(_INTENTOS_LOGIN) > 2048:
            expirados = [
                clave for clave, valor in _INTENTOS_LOGIN.items()
                if ahora - max(
                    valor.get("bloqueado_hasta", 0),
                    max(valor.get("fallos", [0])),
                ) > VENTANA_LOGIN_SEGUNDOS
            ]
            for clave in expirados:
                _INTENTOS_LOGIN.pop(clave, None)


def autenticar(correo, password, rol_esperado):
    correo = normalizar_correo(correo)
    if not correo_valido(correo) or not isinstance(password, str) or not password:
        return None
    if len(password) > MAX_PASSWORD_LENGTH:
        return None
    if segundos_bloqueo_login(correo):
        return None

    try:
        driver = _driver()
        with driver.session() as session:
            registro = session.run(
                """
                MATCH (c:Cuenta {email_normalizado: $correo})
                OPTIONAL MATCH (c)-[:REPRESENTA_A]->(p)
                RETURN c.id AS id, c.password_salt AS salt, c.password_hash AS hash,
                       c.rol AS rol, c.roles AS roles,
                       c.email_normalizado AS correo,
                       coalesce(c.activa, true) AS activa,
                       coalesce(c.auth_version, 0) AS auth_version,
                       p.id AS entidad_id,
                       coalesce(p.nombre, 'Administrador') AS nombre
                """,
                correo=correo,
            ).single()

        if not registro:
            calculado = _hash_password(password, _SAL_DUMMY)
            hmac.compare_digest(calculado, _HASH_DUMMY)
            _registrar_intento_login(correo, False)
            return None
        if not registro["activa"]:
            _registrar_intento_login(correo, False)
            return None

        calculado = _hash_password(password, bytes.fromhex(registro["salt"]))
        if not hmac.compare_digest(calculado, registro["hash"]):
            _registrar_intento_login(correo, False)
            return None

        roles = list(registro["roles"] or [])
        if registro["rol"] not in roles:
            roles.append(registro["rol"])
        if rol_esperado not in roles:
            _registrar_intento_login(correo, False)
            return None

        _registrar_intento_login(correo, True)
        return {
            "id": registro["id"],
            "correo": registro["correo"],
            "rol": rol_esperado,
            "roles": roles,
            "auth_version": registro["auth_version"],
            "entidad_id": registro["entidad_id"],
            "nombre": registro["nombre"],
        }
    except ConnectionError:
        raise  # que main.py lo convierta en 503
    except Exception:
        logger.exception("Error inesperado en autenticar")
        return None



def validar_sesion(cuenta):
    """Comprueba revocación de cuenta, rol y versión de contraseña en cada rerun."""
    cuenta_id = (cuenta or {}).get("id")
    rol = (cuenta or {}).get("rol")
    if not cuenta_id or rol not in {ROL_USUARIO, ROL_EMPRESA, ROL_ADMIN}:
        return False
    try:
        with _driver().session() as session:
            registro = session.run(
                """
                MATCH (c:Cuenta {id: $id})
                RETURN c.email_normalizado AS correo,
                       coalesce(c.activa, true) AS activa,
                       c.rol AS rol,
                       coalesce(c.roles, [c.rol]) AS roles,
                       coalesce(c.auth_version, 0) AS auth_version
                """,
                id=cuenta_id,
            ).single()
        if not registro or not registro["activa"]:
            return False
        roles = list(registro["roles"] or [])
        if registro["rol"] not in roles:
            roles.append(registro["rol"])
        return (
            registro["correo"] == normalizar_correo(cuenta.get("correo"))
            and rol in roles
            and int(registro["auth_version"]) == int(cuenta.get("auth_version", 0))
        )
    except Exception:
        return None


def crear_sesion_persistente(cuenta):
    """Crea un token aleatorio de navegador; Neo4j solo conserva su hash."""
    cuenta_id = (cuenta or {}).get("id")
    rol = (cuenta or {}).get("rol")
    if not cuenta_id or rol not in {ROL_USUARIO, ROL_EMPRESA, ROL_ADMIN}:
        return None

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ahora = int(time.time())
    expira = ahora + SESSION_TTL_SECONDS
    version = int((cuenta or {}).get("auth_version", 0))
    try:
        driver = _driver()
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT sesion_token_hash_unico IF NOT EXISTS "
                "FOR (s:Sesion) REQUIRE s.token_hash IS UNIQUE"
            ).consume()
            session.run(
                "MATCH (s:Sesion) WHERE s.expira_epoch <= $ahora DELETE s",
                ahora=ahora,
            ).consume()
            creado = session.run(
                """
                MATCH (c:Cuenta {id: $cuenta_id})
                WHERE coalesce(c.activa, true)
                  AND coalesce(c.auth_version, 0) = $version
                  AND (c.rol = $rol OR $rol IN coalesce(c.roles, []))
                CREATE (s:Sesion {
                    token_hash: $token_hash, cuenta_id: c.id, rol: $rol,
                    auth_version: $version, creada_epoch: $ahora,
                    expira_epoch: $expira
                })
                RETURN s.token_hash AS hash
                """,
                cuenta_id=cuenta_id,
                rol=rol,
                version=version,
                token_hash=token_hash,
                ahora=ahora,
                expira=expira,
            ).single()
        if not creado:
            return None
        return {"token": token, "expira_epoch": expira}
    except Exception:
        return None


def restaurar_sesion_persistente(token):
    """Valida un token del navegador y devuelve la cuenta ligada a él."""
    token = str(token or "")
    if not token or len(token) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        return "invalida", None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ahora = int(time.time())
    try:
        driver = _driver()
        with driver.session() as session:
            registro = session.run(
                """
                MATCH (s:Sesion {token_hash: $token_hash})
                MATCH (c:Cuenta {id: s.cuenta_id})
                WHERE s.expira_epoch > $ahora
                  AND coalesce(c.activa, true)
                  AND coalesce(s.auth_version, 0) = coalesce(c.auth_version, 0)
                  AND (s.rol = c.rol OR s.rol IN coalesce(c.roles, []))
                OPTIONAL MATCH (c)-[:REPRESENTA_A]->(p)
                RETURN c.id AS id, c.email_normalizado AS correo,
                       s.rol AS rol, coalesce(c.roles, [c.rol]) AS roles,
                       coalesce(c.auth_version, 0) AS auth_version,
                       p.id AS entidad_id, coalesce(p.nombre, 'Administrador') AS nombre,
                       s.expira_epoch AS expira_epoch
                LIMIT 1
                """,
                token_hash=token_hash,
                ahora=ahora,
            ).single()
            if registro:
                cuenta = dict(registro)
            else:
                session.run(
                    "MATCH (s:Sesion {token_hash: $token_hash}) DELETE s",
                    token_hash=token_hash,
                ).consume()
                return "invalida", None
        return "ok", cuenta
    except Exception:
        return "error_bd", None


def revocar_sesion_persistente(token):
    token = str(token or "")
    if not token or len(token) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        return False
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    try:
        with _driver().session() as session:
            session.run(
                "MATCH (s:Sesion {token_hash: $token_hash}) DELETE s",
                token_hash=token_hash,
            ).consume()
        return True
    except Exception:
        return False


def asegurar_admin_inicial():
    """Crea una cuenta administradora una sola vez desde variables privadas de entorno."""
    try:
        driver = _driver()
        with driver.session() as session:
            existente_admin = session.run(
                "MATCH (c:Cuenta) "
                "WHERE coalesce(c.activa, true) "
                "AND (c.rol = $rol OR $rol IN coalesce(c.roles, [])) "
                "RETURN count(c) > 0 AS existe",
                rol=ROL_ADMIN,
            ).single()
        if existente_admin and existente_admin["existe"]:
            return "admin_existente"
    except Exception:
        return "error_bd"

    correo = normalizar_correo(os.getenv("ADMIN_EMAIL"))
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not correo or not password:
        return "sin_configurar"
    if not correo_valido(correo) or len(password) < 10 or len(password) > MAX_PASSWORD_LENGTH:
        return "configuracion_invalida"

    salt_hex, password_hash = _nueva_credencial(password)
    try:
        _asegurar_restriccion(driver)

        def crear_admin(tx):
            existente = tx.run(
                "MATCH (c:Cuenta {email_normalizado: $correo}) "
                "RETURN c.id AS id, c.rol AS rol, c.roles AS roles, "
                "coalesce(c.activa, true) AS activa, c.password_salt AS salt, "
                "c.password_hash AS hash",
                correo=correo,
            ).single()
            if existente:
                roles_existentes = list(existente["roles"] or [])
                if existente["rol"] not in roles_existentes:
                    roles_existentes.append(existente["rol"])
                if ROL_ADMIN not in roles_existentes:
                    return "correo_en_uso"
                if existente["activa"]:
                    return "admin_existente"
                try:
                    hash_configurado = _hash_password(password, bytes.fromhex(existente["salt"] or ""))
                except (TypeError, ValueError):
                    return "admin_inactivo_password_distinta"
                if not existente["hash"] or not hmac.compare_digest(hash_configurado, existente["hash"]):
                    return "admin_inactivo_password_distinta"
                tx.run(
                    "MATCH (c:Cuenta {id: $id}) "
                    "SET c.activa = true, c.auth_version = coalesce(c.auth_version, 0) + 1 "
                    "RETURN c.id AS id",
                    id=existente["id"],
                ).consume()
                return "admin_reactivado"

            perfil_existente = tx.run(
                "MATCH (p) WHERE (p:Usuario OR p:Empresa) "
                "AND p.correo_contacto = $correo RETURN p.id AS id LIMIT 1",
                correo=correo,
            ).single()
            if perfil_existente:
                return "correo_en_uso"

            tx.run(
                """
                CREATE (:Cuenta {
                    id: $id, email: $correo, email_normalizado: $correo,
                    password_salt: $salt, password_hash: $hash,
                    rol: $rol, roles: [$rol], activa: true, auth_version: 0,
                    fecha_creacion: $creado
                })
                """,
                id=uuid.uuid4().hex,
                correo=correo,
                salt=salt_hex,
                hash=password_hash,
                rol=ROL_ADMIN,
                creado=datetime.now(timezone.utc).isoformat(),
            ).consume()
            return "admin_creado"

        with driver.session() as session:
            return session.execute_write(crear_admin)
    except Exception:
        return "error_bd"


def restablecer_password_admin(correo):
    """Genera una clave temporal; solo devuelve el valor nuevo una vez al administrador."""
    correo = normalizar_correo(correo)
    if not correo_valido(correo):
        return None

    password_temporal = secrets.token_urlsafe(15)
    salt_hex, password_hash = _nueva_credencial(password_temporal)
    try:
        driver = _driver()
        with driver.session() as session:
            resultado = session.run(
                """
                MATCH (c:Cuenta {email_normalizado: $correo})
                WHERE coalesce(c.activa, true)
                SET c.password_salt = $salt, c.password_hash = $hash,
                    c.auth_version = coalesce(c.auth_version, 0) + 1,
                    c.password_actualizada = $fecha
                RETURN c.email_normalizado AS correo
                """,
                correo=correo,
                salt=salt_hex,
                hash=password_hash,
                fecha=datetime.now(timezone.utc).isoformat(),
            ).single()
        return (resultado["correo"], password_temporal) if resultado else None
    except Exception:
        return None


def generar_codigo_activacion_admin(correo, tipo_perfil="Usuario"):
    """Emite un código de un solo uso para reclamar un perfil existente."""
    correo = normalizar_correo(correo)
    etiqueta = {"Usuario": "Usuario", "Empresa": "Empresa"}.get(tipo_perfil)
    if not correo_valido(correo) or not etiqueta:
        return None
    codigo = secrets.token_urlsafe(18)
    codigo_hash = hashlib.sha256(codigo.encode("utf-8")).hexdigest()
    expira = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    try:
        with _driver().session() as session:
            resultado = session.run(
                f"""
                MATCH (p:{etiqueta} {{correo_contacto: $correo}})
                WHERE NOT EXISTS {{ MATCH (:Cuenta)-[:REPRESENTA_A]->(p) }}
                SET p.codigo_activacion_hash = $hash,
                    p.codigo_activacion_expira = $expira
                RETURN p.id AS id
                """,
                correo=correo,
                hash=codigo_hash,
                expira=expira,
            ).single()
        return (resultado["id"], codigo) if resultado else None
    except Exception:
        return None

