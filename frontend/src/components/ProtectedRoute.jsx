import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import api, { clearSession, getToken, getUser, saveSession } from "../api";

// Envuelve las rutas privadas: valida el token contra /api/auth/me al cargar.
export default function ProtectedRoute() {
  const token = getToken();
  const [estado, setEstado] = useState(token ? "verificando" : "sin_sesion");

  useEffect(() => {
    if (!token) return;
    let cancelado = false;

    api
      .get("/api/auth/me")
      .then((res) => {
        if (cancelado) return;
        // Datos frescos de la cuenta (por si cambiaron desde el login)
        saveSession(token, res.data.data);
        setEstado("ok");
      })
      .catch((err) => {
        if (cancelado) return;
        if (err.response?.status === 401) {
          // El interceptor ya limpia y redirige; esto cubre cualquier carrera.
          clearSession();
          setEstado("sin_sesion");
        } else {
          setEstado("error");
        }
      });

    return () => {
      cancelado = true;
    };
  }, [token]);

  if (estado === "sin_sesion" || !getUser()) {
    return <Navigate to="/login" replace />;
  }

  if (estado === "verificando") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-ink-500">
        Verificando sesión...
      </div>
    );
  }

  if (estado === "error") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper px-4 text-center text-red-600">
        No se pudo verificar la sesión. Revisa que el servidor esté activo.
      </div>
    );
  }

  return <Outlet />;
}
