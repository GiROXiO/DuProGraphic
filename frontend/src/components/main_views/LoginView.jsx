import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { saveSession } from "../../api";
import {
  Briefcase,
  User,
  Shield,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Network,
} from "lucide-react";

const ROLES = [
  { id: "usuario", icon: User, label: "Usuario" },
  { id: "empresa", icon: Briefcase, label: "Empresa" },
  { id: "administrador", icon: Shield, label: "Admin" },
];

export default function LoginView() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("usuario");
  const [verPassword, setVerPassword] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const response = await api.post("/api/auth/login", {
        correo,
        password,
        rol,
      });

      if (response.data.status === "success") {
        saveSession(response.data.token, response.data.data);
        navigate("/", { replace: true });
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "No se pudo conectar con el servidor. Intenta de nuevo.",
      );
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-[#f3f2ef]">
      {/* Panel de marca (solo escritorio) */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-[linear-gradient(135deg,#004182,#0a66c2_60%,#378fe9)] text-white items-center justify-center p-12">
        <svg
          className="absolute inset-0 w-full h-full opacity-20"
          viewBox="0 0 400 400"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <g stroke="white" strokeWidth="1.2" fill="none">
            <line x1="60" y1="80" x2="180" y2="150" />
            <line x1="180" y1="150" x2="320" y2="90" />
            <line x1="180" y1="150" x2="140" y2="290" />
            <line x1="320" y1="90" x2="350" y2="230" />
            <line x1="140" y1="290" x2="290" y2="330" />
            <line x1="350" y1="230" x2="290" y2="330" />
            <line x1="60" y1="80" x2="90" y2="220" />
            <line x1="90" y1="220" x2="140" y2="290" />
          </g>
          <g fill="white">
            <circle cx="60" cy="80" r="7" />
            <circle cx="180" cy="150" r="11" />
            <circle cx="320" cy="90" r="8" />
            <circle cx="140" cy="290" r="10" />
            <circle cx="350" cy="230" r="7" />
            <circle cx="290" cy="330" r="9" />
            <circle cx="90" cy="220" r="6" />
          </g>
        </svg>

        <div className="relative max-w-md">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur px-3 py-1.5 rounded-full text-sm font-medium mb-6">
            <Network className="h-4 w-4" />
            Red profesional en grafos
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight leading-tight">
            DuProGraphic
          </h1>
          <p className="mt-4 text-lg text-blue-100">
            Conecta con personas, empresas y oportunidades a través de las
            relaciones que realmente importan.
          </p>
        </div>
      </div>

      {/* Panel del formulario */}
      <div className="flex-1 flex items-center justify-center px-4 py-12 sm:px-8">
        <div className="w-full max-w-md">
          <h1 className="lg:hidden text-center text-3xl font-extrabold text-[#0a66c2] mb-8">
            DuProGraphic
          </h1>

          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
            <h2 className="text-2xl font-bold text-gray-900">Bienvenido</h2>
            <p className="mt-1 text-sm text-gray-500">
              Inicia sesión para continuar
            </p>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              {error && (
                <div
                  role="alert"
                  className="bg-red-50 text-red-700 p-3 rounded-lg text-sm border border-red-200"
                >
                  {error}
                </div>
              )}

              {/* Selector de rol */}
              <div>
                <span className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de acceso
                </span>
                <div className="grid grid-cols-3 gap-1 p-1 bg-gray-100 rounded-xl">
                  {ROLES.map((opcion) => (
                    <button
                      key={opcion.id}
                      type="button"
                      onClick={() => setRol(opcion.id)}
                      aria-pressed={rol === opcion.id}
                      className={`flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm transition-all ${
                        rol === opcion.id
                          ? "bg-white text-[#0a66c2] font-semibold shadow"
                          : "text-gray-500 hover:text-gray-800"
                      }`}
                    >
                      <opcion.icon className="h-4 w-4" />
                      {opcion.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Correo */}
              <div>
                <label
                  htmlFor="correo"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Correo electrónico
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    id="correo"
                    type="email"
                    required
                    autoComplete="email"
                    placeholder="tucorreo@ejemplo.com"
                    value={correo}
                    onChange={(e) => setCorreo(e.target.value)}
                    className="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0a66c2] focus:border-transparent transition"
                  />
                </div>
              </div>

              {/* Contraseña */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Contraseña
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    id="password"
                    type={verPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-11 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0a66c2] focus:border-transparent transition"
                  />
                  <button
                    type="button"
                    onClick={() => setVerPassword((v) => !v)}
                    aria-label={
                      verPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                    }
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
                  >
                    {verPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={cargando}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-full text-sm font-bold text-white bg-[#0a66c2] hover:bg-[#004182] disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0a66c2] transition-colors"
              >
                {cargando && (
                  <span className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                )}
                {cargando ? "Ingresando..." : "Iniciar sesión"}
              </button>
            </form>
          </div>

          <p className="mt-6 text-center text-xs text-gray-400">
            © DuProGraphic · Proyecto de Bases de Datos
          </p>
        </div>
      </div>
    </div>
  );
}
