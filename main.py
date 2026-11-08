from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Importaciones de tus módulos core (limpios de Streamlit)
from backend_core.auth import autenticar
from backend_core.user_portal import _ofertas_recomendadas, _perfil_usuario, _sugerencias
from backend_core.company_portal import _ofertas_empresa

app = FastAPI(title="Duprographic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar a tu dominio o localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    correo: str
    password: str
    rol: str

# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.post("/api/auth/login")
def login(request: LoginRequest):
    cuenta = autenticar(request.correo, request.password, request.rol)
    if not cuenta:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"status": "success", "data": cuenta}

# --- ENDPOINTS DEL USUARIO (Requieren el ID del usuario en React) ---
@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str):
    """Obtiene los datos del perfil, equivalente a la pestaña 'Mi Perfil'."""
    perfil = _perfil_usuario(user_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return {"status": "success", "data": perfil}

@app.get("/api/users/{user_id}/feed/jobs")
def get_job_feed(user_id: str):
    """Alimenta la pestaña de Ofertas ordenadas por afinidad."""
    ofertas = _ofertas_recomendadas(user_id)
    return {"status": "success", "data": ofertas}

@app.get("/api/users/{user_id}/network/suggestions")
def get_network_suggestions(user_id: str):
    """Alimenta la columna derecha (RightPanel) con sugerencias de la red."""
    personas, empresas, proyectos = _sugerencias(user_id)
    return {
        "status": "success", 
        "data": {
            "personas": personas,
            "empresas": empresas,
            "proyectos": proyectos
        }
    }