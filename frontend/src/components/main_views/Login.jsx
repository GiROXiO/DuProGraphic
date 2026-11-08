import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Briefcase, User, Shield } from "lucide-react";

export default function Login() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("usuario");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const response = await axios.post(
        "http://localhost:8000/api/auth/login",
        {
          correo,
          password,
          rol,
        },
      );

      if (response.data.status === "success") {
        // Guardamos el token/datos del usuario en localStorage
        localStorage.setItem(
          "duprographic_user",
          JSON.stringify(response.data.data),
        );
        navigate("/"); // Redirige al Feed
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Error al iniciar sesión");
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f2ef] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-4xl font-extrabold text-[#0a66c2] tracking-tight">
          DuProGraphic
        </h1>
        <h2 className="mt-3 text-center text-xl text-gray-900">
          Tu red profesional conectada
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-gray-200">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm border border-red-200">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de acceso
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: "usuario", icon: User, label: "Usuario" },
                  { id: "empresa", icon: Briefcase, label: "Empresa" },
                  { id: "administrador", icon: Shield, label: "Admin" },
                ].map((opcion) => (
                  <button
                    key={opcion.id}
                    type="button"
                    onClick={() => setRol(opcion.id)}
                    className={`flex flex-col items-center justify-center p-3 border rounded-md text-sm transition-colors ${
                      rol === opcion.id
                        ? "border-[#0a66c2] bg-blue-50 text-[#0a66c2] font-semibold"
                        : "border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <opcion.icon className="h-5 w-5 mb-1" />
                    {opcion.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Correo / Usuario
              </label>
              <div className="mt-1">
                <input
                  type="text"
                  required
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#0a66c2] focus:border-[#0a66c2]"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#0a66c2] focus:border-[#0a66c2]"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-full shadow-sm text-sm font-bold text-white bg-[#0a66c2] hover:bg-[#004182] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0a66c2] transition-colors"
            >
              Iniciar sesión
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
