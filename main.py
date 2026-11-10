"""API FastAPI: puente entre el frontend React y Neo4j.

Ejecutar:  uvicorn main:app --reload --port 8000
"""

import os
import uuid
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from backend_core.auth import (
    MAX_PROFILE_LENGTHS,
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    autenticar,
    crear_perfil_con_acceso_admin,
    crear_sesion_persistente,
    registrar_cuenta,
    restaurar_sesion_persistente,
    revocar_sesion_persistente,
    url_http_valida,
)
from backend_core import analytics_data as analitica
from backend_core import network_data as red
from backend_core.company_data import ofertas_empresa
from backend_core import applications_data as postulaciones
from backend_core import links_data as vinculos
from backend_core import admin_data as gestion
from backend_core import company_data as empresas
from backend_core.user_data import (
    actualizar_perfil,
    catalogo_habilidades,
    guardar_habilidad,
    habilidades_usuario,
    ofertas_recomendadas,
    perfil_usuario,
    quitar_habilidad,
    sugerencias,
)

app = FastAPI(title="DuProGraphic API")

# Orígenes extra permitidos, separados por comas, p. ej. el dominio de producción:
#   CORS_ORIGINS=https://miapp.com,https://www.miapp.com
_origenes_extra = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes_extra,
    # Desarrollo local: cualquier puerto en localhost, 127.0.0.1 o [::1]
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|\[::1\]):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConnectionError)
def _sin_base_de_datos(_request, _exc):
    # Neo4j caído o .env incompleto: no se debe confundir con credenciales inválidas.
    return JSONResponse(status_code=503, content={"detail": "No se pudo conectar con Neo4j"})


# --- Autenticación -----------------------------------------------------------
# El login entrega un token aleatorio. Neo4j solo guarda su hash (nodo Sesion) y
# caduca a los 14 días. El frontend lo envía en "Authorization: Bearer <token>".

def _token_de(authorization: str | None) -> str:
    esquema, _, token = (authorization or "").partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Falta el token de sesión")
    return token.strip()


def cuenta_actual(authorization: str | None = Header(default=None)) -> dict:
    """Dependencia: valida el token y devuelve la cuenta de la sesión."""
    estado, cuenta = restaurar_sesion_persistente(_token_de(authorization))
    if estado == "error_bd":
        raise HTTPException(status_code=503, detail="No se pudo conectar con Neo4j")
    if estado != "ok":
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    return cuenta


def _exigir_propietario(cuenta: dict, rol: str, entidad_id: str) -> None:
    """Solo el dueño del perfil (con el rol correcto) o un administrador."""
    if cuenta["rol"] == ROL_ADMIN:
        return
    if cuenta["rol"] != rol or cuenta["entidad_id"] != entidad_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este recurso")


class LoginRequest(BaseModel):
    correo: str
    password: str
    rol: str


@app.post("/api/auth/login")
def login(request: LoginRequest):
    cuenta = autenticar(request.correo, request.password, request.rol)
    if not cuenta:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    sesion = crear_sesion_persistente(cuenta)
    if not sesion:
        raise HTTPException(status_code=503, detail="No se pudo crear la sesión")
    return {
        "status": "success",
        "data": cuenta,
        "token": sesion["token"],
        "expira_epoch": sesion["expira_epoch"],
    }

def _texto(maximo):
    return Annotated[str, StringConstraints(strip_whitespace=True, max_length=maximo)]


class RegistroIn(BaseModel):
    """Registro público. Solo personas y empresas: el rol administrador no se pide aquí."""

    # Sin str_strip_whitespace global: la contraseña no se debe recortar.
    model_config = ConfigDict(extra="forbid")

    rol: Literal["usuario", "empresa"]
    correo: _texto(254)
    password: str = Field(min_length=10, max_length=256)
    nombre: _texto(140) = Field(min_length=1)
    perfil_profesional: _texto(MAX_PROFILE_LENGTHS["perfil_profesional"]) | None = None  # usuario
    universidad: _texto(MAX_PROFILE_LENGTHS["universidad"]) | None = None  # usuario
    sector: _texto(MAX_PROFILE_LENGTHS["sector"]) | None = None  # empresa

    @field_validator("password")
    @classmethod
    def _password_no_vacia(cls, valor):
        if not valor.strip():
            raise ValueError("La contraseña no puede ser solo espacios")
        return valor


# Cualquier correo ya presente en la base se rechaza igual, sin pistas sobre el motivo.
_CORREO_REPETIDO = {
    "correo_existente", "codigo_requerido", "perfil_ya_vinculado",
    "correo_perfil_usuario", "correo_perfil_empresa", "correo_perfil_existente",
}

_ERRORES_REGISTRO = {
    "correo_invalido": "Escribe un correo válido",
    "password_corto": "La contraseña debe tener al menos 10 caracteres",
    "password_largo": "La contraseña es demasiado larga",
    "nombre_vacio": "El nombre es obligatorio",
    "perfil_incompleto": "Completa tu titular profesional (persona) o el sector (empresa)",
    "url_invalida": "El enlace debe comenzar con http:// o https://",
    "datos_invalidos": "Revisa los datos: algún campo no es válido",
}


@app.post("/api/auth/register", status_code=201)
def register(datos: RegistroIn):
    """Crea una cuenta nueva y la deja con la sesión iniciada."""
    estado, cuenta = registrar_cuenta(
        datos.rol,
        datos.correo,
        datos.password,
        datos.model_dump(exclude={"rol", "correo", "password"}),
        codigo_activacion="",  # el registro público nunca reclama perfiles existentes
    )
    if estado in _CORREO_REPETIDO:
        raise HTTPException(status_code=409, detail="Ese correo ya está registrado")
    if estado in _ERRORES_REGISTRO:
        raise HTTPException(status_code=422, detail=_ERRORES_REGISTRO[estado])
    if estado == "error_bd":
        raise HTTPException(status_code=503, detail="No se pudo conectar con Neo4j")
    if estado != "creada":
        raise HTTPException(status_code=400, detail="No se pudo crear la cuenta")

    cuenta = {**cuenta, "auth_version": 0}
    sesion = crear_sesion_persistente(cuenta)
    if not sesion:
        raise HTTPException(status_code=503, detail="Cuenta creada, pero no se pudo iniciar sesión")
    return {
        "status": "success",
        "data": cuenta,
        "token": sesion["token"],
        "expira_epoch": sesion["expira_epoch"],
    }

@app.get("/api/auth/me")
def me(cuenta: dict = Depends(cuenta_actual)):
    """Permite al frontend comprobar al recargar si el token sigue vigente."""
    return {"status": "success", "data": cuenta}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    revocar_sesion_persistente(_token_de(authorization))
    return {"status": "success"}


# --- Usuario -------------------------------------------------------------------

_L = MAX_PROFILE_LENGTHS  # límites de longitud definidos en backend_core/auth.py


class PerfilUsuarioIn(BaseModel):
    """Campos que el propio usuario puede editar. Cualquier otro campo se rechaza."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=140)
    perfil_profesional: str = Field(min_length=1, max_length=_L["perfil_profesional"])
    universidad: str | None = Field(default=None, max_length=_L["universidad"])
    ubicacion: str | None = Field(default=None, max_length=_L["ubicacion"])
    acerca_de: str | None = Field(default=None, max_length=_L["acerca_de"])
    experiencia: str | None = Field(default=None, max_length=_L["experiencia"])
    areas_interes: str | None = Field(default=None, max_length=_L["areas_interes"])
    educacion_detalle: str | None = Field(default=None, max_length=_L["educacion_detalle"])
    anios_experiencia: int = Field(default=0, ge=0, le=50)
    modalidad_preferida: Literal["remoto", "híbrido", "presencial"] | None = None
    sitio_portafolio: str | None = Field(default=None, max_length=_L["sitio_portafolio"])
    idiomas: str | None = Field(default=None, max_length=_L["idiomas"])
    logros: str | None = Field(default=None, max_length=_L["logros"])

    @field_validator("sitio_portafolio")
    @classmethod
    def _enlace_valido(cls, valor):
        if valor and not url_http_valida(valor):
            raise ValueError("Escribe un enlace completo que comience con http:// o https://")
        return valor


class HabilidadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nivel: Literal["básico", "intermedio", "avanzado"]


def _perfil_respuesta(user_id: str) -> dict:
    fila = perfil_usuario(user_id)
    if not fila:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    # Propiedades del nodo Usuario en un solo nivel, más el id de su cuenta.
    return {"status": "success", "data": {**fila["perfil"], "cuenta_id": fila["cuenta_id"]}}


@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return _perfil_respuesta(user_id)


@app.put("/api/users/{user_id}/profile")
def update_user_profile(
    user_id: str, datos: PerfilUsuarioIn, cuenta: dict = Depends(cuenta_actual)
):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not actualizar_perfil(user_id, datos.model_dump()):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return _perfil_respuesta(user_id)


@app.get("/api/skills")
def get_skill_catalog(cuenta: dict = Depends(cuenta_actual)):
    """Catálogo de habilidades disponibles (lo puede leer cualquier cuenta con sesión)."""
    return {"status": "success", "data": catalogo_habilidades()}


@app.get("/api/users/{user_id}/skills")
def get_user_skills(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {"status": "success", "data": habilidades_usuario(user_id)}


@app.put("/api/users/{user_id}/skills/{skill_id}")
def put_user_skill(
    user_id: str, skill_id: str, datos: HabilidadIn, cuenta: dict = Depends(cuenta_actual)
):
    """Añade la habilidad al perfil o cambia su nivel de dominio."""
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not guardar_habilidad(user_id, skill_id, datos.nivel):
        raise HTTPException(status_code=404, detail="Usuario o habilidad no encontrados")
    return {"status": "success", "data": habilidades_usuario(user_id)}


@app.delete("/api/users/{user_id}/skills/{skill_id}")
def delete_user_skill(user_id: str, skill_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not quitar_habilidad(user_id, skill_id):
        raise HTTPException(status_code=404, detail="El usuario no tiene esa habilidad")
    return {"status": "success", "data": habilidades_usuario(user_id)}
  
@app.get("/api/users/{user_id}/feed/jobs")
def get_job_feed(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {"status": "success", "data": ofertas_recomendadas(user_id)}


@app.get("/api/users/{user_id}/network/suggestions")
def get_network_suggestions(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    personas, empresas, proyectos = sugerencias(user_id)
    return {
        "status": "success",
        "data": {"personas": personas, "empresas": empresas, "proyectos": proyectos},
    }

# --- Conexiones profesionales y perfil público ------------------------------------

def _exigir_dueno(cuenta: dict, user_id: str) -> None:
    """Acciones de red: solo la propia persona. El administrador no crea ni gestiona conexiones."""
    if cuenta["rol"] != ROL_USUARIO or cuenta["entidad_id"] != user_id:
        raise HTTPException(status_code=403, detail="Solo puedes gestionar tu propia red")


@app.get("/api/users/{user_id}/connections")
def get_connections(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {
        "status": "success",
        "data": {
            "conexiones": red.conexiones(user_id),
            "recibidas": red.solicitudes_recibidas(user_id),
            "enviadas": red.solicitudes_enviadas(user_id),
        },
    }


@app.post("/api/users/{user_id}/connections/{other_id}", status_code=201)
def send_connection_request(user_id: str, other_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Conectar con alguien. Es idempotente y nunca falla por un estado previo:

    - ya conectados -> devuelve 'conectado'
    - ya enviaste una solicitud -> devuelve 'enviada' (sin duplicarla)
    - esa persona ya te había escrito -> se acepta y devuelve 'conectado'
    - si no -> crea la solicitud y devuelve 'enviada'
    """
    _exigir_dueno(cuenta, user_id)
    if user_id == other_id:
        raise HTTPException(status_code=400, detail="No puedes conectarte contigo mismo")
    estado = red.estado_relacion(user_id, other_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    if estado in ("conectado", "enviada"):
        return {"status": "success", "data": {"relacion": estado}}
    if estado == "recibida":
        if not red.aceptar_solicitud(other_id, user_id):
            raise HTTPException(status_code=404, detail="La solicitud ya no está disponible")
        return {"status": "success", "data": {"relacion": "conectado"}}
    red.solicitar_conexion(user_id, other_id)
    return {"status": "success", "data": {"relacion": "enviada"}}


@app.post("/api/users/{user_id}/connection-requests/{other_id}/accept")
def accept_connection_request(user_id: str, other_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Acepta la solicitud que other_id le envió a user_id."""
    _exigir_dueno(cuenta, user_id)
    if not red.aceptar_solicitud(other_id, user_id):
        raise HTTPException(status_code=404, detail="La solicitud ya no está disponible")
    return {"status": "success", "data": {"relacion": "conectado"}}


@app.delete("/api/users/{user_id}/connection-requests/{other_id}")
def withdraw_connection_request(user_id: str, other_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Rechaza la solicitud recibida de other_id, o cancela la que user_id le envió."""
    _exigir_dueno(cuenta, user_id)
    if not (red.retirar_solicitud(other_id, user_id) or red.retirar_solicitud(user_id, other_id)):
        raise HTTPException(status_code=404, detail="La solicitud ya no está disponible")
    return {"status": "success", "data": {"relacion": "ninguna"}}


@app.get("/api/people/{person_id}")
def get_public_profile(person_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Perfil público de una persona; lo puede ver cualquier cuenta con sesión."""
    perfil = red.perfil_publico(person_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    relacion = None
    comunes = []
    if cuenta["rol"] == ROL_USUARIO and cuenta.get("entidad_id"):
        yo = cuenta["entidad_id"]
        if yo == person_id:
            relacion = "propio"
        else:
            relacion = red.estado_relacion(yo, person_id)
            comunes = red.contactos_comunes(yo, person_id)
    return {"status": "success", "data": {**perfil, "relacion": relacion, "contactos_en_comun": comunes}}

# --- Vínculos del usuario: empresas y proyectos -----------------------------------
# Versión simple: el usuario declara sus vínculos sin aprobación de la empresa.

class ExperienciaIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    cargo: str = Field(min_length=1, max_length=120)
    periodo: str | None = Field(default=None, max_length=80)
    actual: bool = False


class ParticipacionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rol: str = Field(min_length=1, max_length=120)


@app.get("/api/users/{user_id}/experience")
def get_user_experience(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {"status": "success", "data": vinculos.experiencia_usuario(user_id)}


@app.put("/api/users/{user_id}/experience/{company_id}")
def put_user_experience(
    user_id: str, company_id: str, datos: ExperienciaIn, cuenta: dict = Depends(cuenta_actual)
):
    """Añade la empresa a tu experiencia o actualiza el cargo, el periodo y si es actual."""
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not vinculos.guardar_experiencia(user_id, company_id, datos.model_dump()):
        raise HTTPException(status_code=404, detail="Usuario o empresa no encontrados")
    return {"status": "success", "data": vinculos.experiencia_usuario(user_id)}


@app.delete("/api/users/{user_id}/experience/{company_id}")
def delete_user_experience(user_id: str, company_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not vinculos.quitar_experiencia(user_id, company_id):
        raise HTTPException(status_code=404, detail="No tienes esa empresa en tu experiencia")
    return {"status": "success", "data": vinculos.experiencia_usuario(user_id)}


@app.get("/api/projects")
def get_project_catalog(cuenta: dict = Depends(cuenta_actual)):
    """Catálogo de proyectos (lo puede leer cualquier cuenta con sesión)."""
    return {"status": "success", "data": vinculos.catalogo_proyectos()}


@app.get("/api/users/{user_id}/projects")
def get_user_projects(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {"status": "success", "data": vinculos.proyectos_usuario(user_id)}


@app.put("/api/users/{user_id}/projects/{project_id}")
def put_user_project(
    user_id: str, project_id: str, datos: ParticipacionIn, cuenta: dict = Depends(cuenta_actual)
):
    """Añade el proyecto a tu trayectoria o actualiza tu rol en él."""
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not vinculos.guardar_proyecto(user_id, project_id, datos.rol):
        raise HTTPException(status_code=404, detail="Usuario o proyecto no encontrados")
    return {"status": "success", "data": vinculos.proyectos_usuario(user_id)}


@app.delete("/api/users/{user_id}/projects/{project_id}")
def delete_user_project(user_id: str, project_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    if not vinculos.quitar_proyecto(user_id, project_id):
        raise HTTPException(status_code=404, detail="No participas en ese proyecto")
    return {"status": "success", "data": vinculos.proyectos_usuario(user_id)}



# --- Postulaciones a ofertas ------------------------------------------------------

@app.get("/api/users/{user_id}/applications")
def get_applications(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return {"status": "success", "data": postulaciones.mis_postulaciones(user_id)}


@app.post("/api/users/{user_id}/applications/{offer_id}", status_code=201)
def apply_to_offer(user_id: str, offer_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Postularse a una oferta abierta. Es idempotente: si ya existe, devuelve su estado."""
    _exigir_dueno(cuenta, user_id)
    oferta = postulaciones.oferta_publicada(offer_id)
    if oferta is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    actual = postulaciones.estado_postulacion(user_id, offer_id)
    if actual is not None:
        return {"status": "success", "data": {"estado": actual, "ya_postulado": True}}
    if not oferta["abierta"]:
        raise HTTPException(status_code=409, detail="La oferta ya no está abierta")
    filas = postulaciones.postular(user_id, offer_id)
    if not filas:
        raise HTTPException(status_code=404, detail="Usuario u oferta no encontrados")
    return {"status": "success", "data": {"estado": filas[0]["estado"], "ya_postulado": False}}


@app.delete("/api/users/{user_id}/applications/{offer_id}")
def withdraw_application(user_id: str, offer_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Retirar la postulación, mientras la empresa no haya tomado una decisión."""
    _exigir_dueno(cuenta, user_id)
    actual = postulaciones.estado_postulacion(user_id, offer_id)
    if actual is None:
        raise HTTPException(status_code=404, detail="No tienes una postulación a esta oferta")
    if postulaciones.normalizar_estado(actual) not in postulaciones.ESTADOS_RETIRABLES:
        raise HTTPException(
            status_code=409,
            detail="Esta postulación ya tiene una decisión y no se puede retirar",
        )
    postulaciones.retirar_postulacion(user_id, offer_id)
    return {"status": "success", "data": {"retirada": True}}



# --- Analítica y recorridos del grafo (solo lectura) ----------------------------
# Los scripts Cypher están en analytics_dashboard/consultas_cypher/.

def _exigir_admin(cuenta: dict) -> None:
    if cuenta["rol"] != ROL_ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede ver este análisis")


def _ok(data):
    return {"status": "success", "data": data}


@app.get("/api/analytics/summary")
def analytics_summary(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.resumen())


@app.get("/api/analytics/influential-users")
def analytics_influential_users(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.usuarios_influyentes())


@app.get("/api/analytics/demanded-skills")
def analytics_demanded_skills(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.habilidades_demandadas())


@app.get("/api/analytics/communities")
def analytics_communities(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.comunidades())


@app.get("/api/analytics/common-contacts")
def analytics_common_contacts(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.contactos_en_comun())


@app.get("/api/analytics/similar-skills")
def analytics_similar_skills(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.habilidades_similares())


@app.get("/api/analytics/project-overlaps")
def analytics_project_overlaps(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(
        {
            "por_miembros": analitica.proyectos_por_miembros(),
            "por_tecnologias": analitica.proyectos_por_tecnologias(),
        }
    )


@app.get("/api/lookups/users")
def lookup_users(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.usuarios_opciones())


@app.get("/api/lookups/companies")
def lookup_companies(cuenta: dict = Depends(cuenta_actual)):
    """Lista de empresas (nombre e id) para los selectores; cualquier cuenta con sesión."""
    return _ok(analitica.empresas_opciones())


@app.get("/api/lookups/offers")
def lookup_offers(cuenta: dict = Depends(cuenta_actual)):
    _exigir_admin(cuenta)
    return _ok(analitica.ofertas_opciones())


@app.get("/api/users/{user_id}/path-to/{company_id}")
def get_path_to_company(user_id: str, company_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Ruta más corta (hasta 6 relaciones) entre un usuario y una empresa; null si no hay."""
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return _ok(analitica.ruta_mas_corta(user_id, company_id))


@app.get("/api/users/{user_id}/recommendations")
def get_user_recommendations(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    return _ok(
        {
            "contactos": analitica.recomendaciones_contactos(user_id),
            "colaboradores": analitica.recomendaciones_colaboradores(user_id),
        }
    )


@app.get("/api/offers/{offer_id}/candidates")
def get_offer_candidates(offer_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Candidatos recomendados para una oferta: el administrador o la empresa que la publica."""
    es_admin = cuenta["rol"] == ROL_ADMIN
    es_duena = cuenta["rol"] == ROL_EMPRESA and analitica.empresa_publica_oferta(
        cuenta["entidad_id"], offer_id
    )
    if not (es_admin or es_duena):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta oferta")
    return _ok(analitica.candidatos_para_oferta(offer_id))



# --- Empresa -------------------------------------------------------------------

class EmpresaIn(BaseModel):
    """Campos que la propia empresa puede editar. Cualquier otro campo se rechaza."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=140)
    sector: str = Field(min_length=1, max_length=_L["sector"])
    descripcion: str | None = Field(default=None, max_length=_L["descripcion"])
    ubicacion: str | None = Field(default=None, max_length=_L["ubicacion"])
    tamano: Literal[
        "1-10 personas",
        "11-50 personas",
        "51-200 personas",
        "201-1000 personas",
        "Más de 1000 personas",
    ] | None = None
    sitio_web: str | None = Field(default=None, max_length=_L["sitio_web"])

    @field_validator("sitio_web")
    @classmethod
    def _enlace_valido(cls, valor):
        if valor and not url_http_valida(valor):
            raise ValueError("Escribe un enlace completo que comience con http:// o https://")
        return valor


class HabilidadRequerida(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=40)
    obligatoria: bool = True


class OfertaIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=160)
    descripcion: str | None = Field(default=None, max_length=1800)
    modalidad: Literal["remoto", "híbrido", "presencial"]
    nivel_experiencia: Literal["Junior", "Semi-Senior", "Senior"]
    habilidades: list[HabilidadRequerida] = Field(default_factory=list, max_length=20)

    @field_validator("habilidades")
    @classmethod
    def _sin_repetidas(cls, valor):
        ids = [h.id for h in valor]
        if len(ids) != len(set(ids)):
            raise ValueError("Hay habilidades repetidas")
        return valor


class EstadoOfertaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["abierta", "cerrada"]


def _exigir_habilidades_existentes(habilidades: list[HabilidadRequerida]) -> None:
    catalogo = {h["id"] for h in catalogo_habilidades()}
    desconocidas = [h.id for h in habilidades if h.id not in catalogo]
    if desconocidas:
        raise HTTPException(
            status_code=422,
            detail=f"Habilidades que no existen en el catálogo: {', '.join(desconocidas)}",
        )


def _ofertas_respuesta(company_id: str) -> dict:
    return {"status": "success", "data": empresas.ofertas_empresa(company_id)}


@app.get("/api/companies/{company_id}/profile")
def get_company_profile(company_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Perfil público de una empresa; lo puede ver cualquier cuenta con sesión."""
    perfil = empresas.perfil_empresa(company_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return {"status": "success", "data": perfil}


@app.put("/api/companies/{company_id}/profile")
def update_company_profile(
    company_id: str, datos: EmpresaIn, cuenta: dict = Depends(cuenta_actual)
):
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    if not empresas.actualizar_empresa(company_id, datos.model_dump()):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return {"status": "success", "data": empresas.perfil_empresa(company_id)}


@app.get("/api/companies/{company_id}/offers")
def get_company_offers(company_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    return {"status": "success", "data": ofertas_empresa(company_id)}


@app.post("/api/companies/{company_id}/offers", status_code=201)
def create_company_offer(
    company_id: str, datos: OfertaIn, cuenta: dict = Depends(cuenta_actual)
):
    """Publica una oferta (queda abierta) con sus habilidades requeridas."""
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    _exigir_habilidades_existentes(datos.habilidades)
    cuerpo = datos.model_dump()
    oferta_id = empresas.crear_oferta(company_id, cuerpo, cuerpo["habilidades"])
    if not oferta_id:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return _ofertas_respuesta(company_id)


@app.put("/api/companies/{company_id}/offers/{offer_id}")
def update_company_offer(
    company_id: str, offer_id: str, datos: OfertaIn, cuenta: dict = Depends(cuenta_actual)
):
    """Edita una oferta de la empresa y deja exactamente las habilidades indicadas."""
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    _exigir_habilidades_existentes(datos.habilidades)
    cuerpo = datos.model_dump()
    if not empresas.actualizar_oferta(company_id, offer_id, cuerpo, cuerpo["habilidades"]):
        raise HTTPException(status_code=404, detail="Oferta no encontrada en tu empresa")
    return _ofertas_respuesta(company_id)


@app.put("/api/companies/{company_id}/offers/{offer_id}/status")
def set_company_offer_status(
    company_id: str, offer_id: str, datos: EstadoOfertaIn, cuenta: dict = Depends(cuenta_actual)
):
    """Cierra o reabre una oferta de la empresa."""
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    if not empresas.cambiar_estado_oferta(company_id, offer_id, datos.estado):
        raise HTTPException(status_code=404, detail="Oferta no encontrada en tu empresa")
    return _ofertas_respuesta(company_id)



# --- Administración -----------------------------------------------------------------
# Solo cuentas con rol administrador. Para editar perfiles, empresas y ofertas existentes
# el administrador usa los mismos endpoints que sus dueños (_exigir_propietario lo permite).

def _solo_admin(cuenta: dict) -> None:
    if cuenta["rol"] != ROL_ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede gestionar esto")


class CuentaNuevaIn(BaseModel):
    """Datos mínimos para crear un perfil con acceso; el resto lo completa su dueño."""

    model_config = ConfigDict(extra="forbid")

    nombre: _texto(140) = Field(min_length=1)
    correo: _texto(254)
    password: str = Field(min_length=10, max_length=256)

    @field_validator("password")
    @classmethod
    def _password_no_vacia(cls, valor):
        if not valor.strip():
            raise ValueError("La contraseña no puede ser solo espacios")
        return valor


class UsuarioNuevoIn(CuentaNuevaIn):
    perfil_profesional: _texto(MAX_PROFILE_LENGTHS["perfil_profesional"]) = Field(min_length=1)
    universidad: _texto(MAX_PROFILE_LENGTHS["universidad"]) | None = None


class EmpresaNuevaIn(CuentaNuevaIn):
    sector: _texto(MAX_PROFILE_LENGTHS["sector"]) = Field(min_length=1)


class PermisoAdminIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    es_admin: bool


class ProyectoIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=140)
    descripcion: str | None = Field(default=None, max_length=600)


def _alta_con_acceso(rol: str, prefijo: str, datos: CuentaNuevaIn) -> None:
    perfil = datos.model_dump(exclude={"correo", "password"})
    estado, _ = crear_perfil_con_acceso_admin(
        rol, datos.correo, datos.password, prefijo + uuid.uuid4().hex[:10].upper(), perfil
    )
    if estado == "creada":
        return
    if estado in _CORREO_REPETIDO:
        raise HTTPException(status_code=409, detail="Ese correo ya está registrado")
    if estado == "id_existente":
        raise HTTPException(status_code=409, detail="Intenta de nuevo")
    if estado == "error_bd":
        raise HTTPException(status_code=503, detail="No se pudo conectar con Neo4j")
    raise HTTPException(
        status_code=422, detail=_ERRORES_REGISTRO.get(estado, "Revisa los datos del formulario")
    )


# Usuarios

@app.get("/api/admin/users")
def admin_list_users(cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    return _ok(gestion.usuarios_admin())


@app.post("/api/admin/users", status_code=201)
def admin_create_user(datos: UsuarioNuevoIn, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    _alta_con_acceso(ROL_USUARIO, "U", datos)
    return _ok(gestion.usuarios_admin())


@app.put("/api/admin/users/{user_id}/admin")
def admin_set_admin(user_id: str, datos: PermisoAdminIn, cuenta: dict = Depends(cuenta_actual)):
    """Concede o retira el permiso de administrador a la cuenta de un usuario."""
    _solo_admin(cuenta)
    destino = gestion.cuenta_de_usuario(user_id)
    if not destino or not destino["activa"]:
        raise HTTPException(status_code=404, detail="Ese usuario no tiene una cuenta activa")
    if not datos.es_admin and destino["cuenta_id"] == cuenta["id"]:
        raise HTTPException(
            status_code=409, detail="No puedes quitarte a ti mismo el permiso de administrador"
        )
    gestion.fijar_admin(user_id, datos.es_admin)
    return _ok(gestion.usuarios_admin())


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    destino = gestion.cuenta_de_usuario(user_id)
    if destino and destino["cuenta_id"] == cuenta["id"]:
        raise HTTPException(status_code=409, detail="No puedes eliminar tu propia cuenta")
    if not gestion.eliminar_usuario(user_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _ok(gestion.usuarios_admin())


# Empresas

@app.get("/api/admin/companies")
def admin_list_companies(cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    return _ok(gestion.empresas_admin())


@app.post("/api/admin/companies", status_code=201)
def admin_create_company(datos: EmpresaNuevaIn, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    _alta_con_acceso(ROL_EMPRESA, "E", datos)
    return _ok(gestion.empresas_admin())


@app.delete("/api/admin/companies/{company_id}")
def admin_delete_company(company_id: str, cuenta: dict = Depends(cuenta_actual)):
    """Elimina la empresa junto con sus ofertas."""
    _solo_admin(cuenta)
    if not gestion.eliminar_empresa(company_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return _ok(gestion.empresas_admin())


# Ofertas (se publican y editan con los endpoints de la empresa; aquí se listan y borran)

@app.get("/api/admin/offers")
def admin_list_offers(cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    return _ok(gestion.ofertas_admin())


@app.delete("/api/admin/offers/{offer_id}")
def admin_delete_offer(offer_id: str, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    if not gestion.eliminar_oferta(offer_id):
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return _ok(gestion.ofertas_admin())


# Proyectos

@app.get("/api/admin/projects")
def admin_list_projects(cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    return _ok(gestion.proyectos_admin())


@app.post("/api/admin/projects", status_code=201)
def admin_create_project(datos: ProyectoIn, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    gestion.crear_proyecto(datos.model_dump())
    return _ok(gestion.proyectos_admin())


@app.put("/api/admin/projects/{project_id}")
def admin_update_project(project_id: str, datos: ProyectoIn, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    if not gestion.actualizar_proyecto(project_id, datos.model_dump()):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _ok(gestion.proyectos_admin())


@app.delete("/api/admin/projects/{project_id}")
def admin_delete_project(project_id: str, cuenta: dict = Depends(cuenta_actual)):
    _solo_admin(cuenta)
    if not gestion.eliminar_proyecto(project_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _ok(gestion.proyectos_admin())



# --- Candidatos de una oferta (lado de la empresa) -----------------------------------

class EstadoPostulacionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["aplicado", "en revisión", "entrevista", "oferta", "aceptado", "rechazado"]


def _exigir_oferta_de_la_empresa(cuenta: dict, company_id: str, offer_id: str) -> None:
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    if not analitica.empresa_publica_oferta(company_id, offer_id):
        raise HTTPException(status_code=404, detail="Oferta no encontrada en tu empresa")


@app.get("/api/companies/{company_id}/offers/{offer_id}/applications")
def get_offer_applications(
    company_id: str, offer_id: str, cuenta: dict = Depends(cuenta_actual)
):
    """Quiénes se postularon a la oferta, con afinidad y estado."""
    _exigir_oferta_de_la_empresa(cuenta, company_id, offer_id)
    return _ok(postulaciones.postulantes_oferta(company_id, offer_id))


@app.put("/api/companies/{company_id}/offers/{offer_id}/applications/{user_id}")
def update_application_status(
    company_id: str,
    offer_id: str,
    user_id: str,
    datos: EstadoPostulacionIn,
    cuenta: dict = Depends(cuenta_actual),
):
    """La empresa mueve a la persona por las etapas del proceso. Aceptado y rechazado son finales."""
    _exigir_oferta_de_la_empresa(cuenta, company_id, offer_id)
    actual = postulaciones.estado_postulacion(user_id, offer_id)
    if actual is None:
        raise HTTPException(status_code=404, detail="Esa persona no se postuló a esta oferta")
    actual = postulaciones.normalizar_estado(actual)
    if actual in postulaciones.ESTADOS_FINALES and datos.estado != actual:
        raise HTTPException(
            status_code=409, detail="Esta postulación ya tiene una decisión final y no se puede cambiar"
        )
    postulaciones.cambiar_estado_postulacion(offer_id, user_id, datos.estado)
    return _ok(postulaciones.postulantes_oferta(company_id, offer_id))