"""API FastAPI: puente entre el frontend React y Neo4j.

Ejecutar:  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend_core.auth import autenticar
from backend_core.company_data import ofertas_empresa
from backend_core.user_data import ofertas_recomendadas, perfil_usuario, sugerencias

app = FastAPI(title="DuProGraphic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConnectionError)
def _sin_base_de_datos(_request, _exc):
    # Neo4j caído o .env incompleto: no se debe confundir con credenciales inválidas.
    return JSONResponse(status_code=503, content={"detail": "No se pudo conectar con Neo4j"})


class LoginRequest(BaseModel):
    correo: str
    password: str
    rol: str


@app.post("/api/auth/login")
def login(request: LoginRequest):
    cuenta = autenticar(request.correo, request.password, request.rol)
    if not cuenta:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"status": "success", "data": cuenta}


@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str):
    fila = perfil_usuario(user_id)
    if not fila:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    # Propiedades del nodo Usuario en un solo nivel, más el id de su cuenta.
    return {"status": "success", "data": {**fila["perfil"], "cuenta_id": fila["cuenta_id"]}}


@app.get("/api/users/{user_id}/feed/jobs")
def get_job_feed(user_id: str):
    return {"status": "success", "data": ofertas_recomendadas(user_id)}


@app.get("/api/users/{user_id}/network/suggestions")
def get_network_suggestions(user_id: str):
    personas, empresas, proyectos = sugerencias(user_id)
    return {
        "status": "success",
        "data": {"personas": personas, "empresas": empresas, "proyectos": proyectos},
    }


@app.get("/api/companies/{company_id}/offers")
def get_company_offers(company_id: str):
    return {"status": "success", "data": ofertas_empresa(company_id)}
