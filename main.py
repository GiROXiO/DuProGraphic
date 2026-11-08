"""API FastAPI: puente entre el frontend React y Neo4j.

Ejecutar:  uvicorn main:app --reload --port 8000
"""

import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend_core.auth import (
    MAX_PROFILE_LENGTHS,
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    autenticar,
    crear_sesion_persistente,
    restaurar_sesion_persistente,
    revocar_sesion_persistente,
    url_http_valida,
)
from backend_core.company_data import ofertas_empresa
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

# --- Empresa -------------------------------------------------------------------

@app.get("/api/companies/{company_id}/offers")
def get_company_offers(company_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_EMPRESA, company_id)
    return {"status": "success", "data": ofertas_empresa(company_id)}
