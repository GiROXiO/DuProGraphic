"""API FastAPI: puente entre el frontend React y Neo4j.

Ejecutar:  uvicorn main:app --reload --port 8000
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend_core.auth import (
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    autenticar,
    crear_sesion_persistente,
    restaurar_sesion_persistente,
    revocar_sesion_persistente,
)
from backend_core.company_data import ofertas_empresa
from backend_core.user_data import ofertas_recomendadas, perfil_usuario, sugerencias

app = FastAPI(title="DuProGraphic API")

app.add_middleware(
    CORSMiddleware,
    # Solo desarrollo local: cualquier puerto en localhost, 127.0.0.1 o [::1]
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

@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str, cuenta: dict = Depends(cuenta_actual)):
    _exigir_propietario(cuenta, ROL_USUARIO, user_id)
    fila = perfil_usuario(user_id)
    if not fila:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    # Propiedades del nodo Usuario en un solo nivel, más el id de su cuenta.
    return {"status": "success", "data": {**fila["perfil"], "cuenta_id": fila["cuenta_id"]}}


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
