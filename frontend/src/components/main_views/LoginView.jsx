import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { saveSession } from "../../api";
import { Briefcase, User, Shield, Mail, Lock, Eye, EyeOff } from "lucide-react";
import BrandMarkView from "../reusable/BrandMarkView";

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
    <div className="flex min-h-screen bg-paper">
      {/* Panel de marca (solo escritorio) */}
      <div className="relative hidden flex-1 overflow-hidden bg-ink-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <svg
          className="absolute inset-0 h-full w-full"
          viewBox="0 0 600 800"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <g stroke="#7c5cff" strokeWidth="1.2" opacity="0.55">
            <line x1="90" y1="140" x2="300" y2="260" />
            <line x1="300" y1="260" x2="500" y2="170" />
            <line x1="300" y1="260" x2="210" y2="470" />
            <line x1="500" y1="170" x2="520" y2="400" />
            <line x1="210" y1="470" x2="420" y2="600" />
            <line x1="520" y1="400" x2="420" y2="600" />
            <line x1="90" y1="140" x2="120" y2="360" />
            <line x1="120" y1="360" x2="210" y2="470" />
            <line x1="420" y1="600" x2="300" y2="720" />
          </g>
          <g fill="#7c5cff">
            <circle cx="90" cy="140" r="7" />
            <circle cx="500" cy="170" r="9" />
            <circle cx="120" cy="360" r="6" />
            <circle cx="520" cy="400" r="8" />
            <circle cx="420" cy="600" r="10" />
            <circle cx="300" cy="720" r="6" />
          </g>
          <circle cx="300" cy="260" r="14" fill="#2be0b0" />
          <circle cx="210" cy="470" r="11" fill="#2be0b0" opacity="0.8" />
        </svg>

        <div className="relative flex items-center gap-3">
          <BrandMarkView className="h-10 w-10" />
          <span className="text-xl font-bold tracking-tight">DuProGraphic</span>
        </div>

        <div className="relative max-w-lg">
          <h1 className="text-5xl font-extrabold leading-[1.05] tracking-tight">
            Tu carrera,
            <br />
            vista como un <span className="text-signal-400">grafo</span>.
          </h1>
          <p className="mt-5 text-lg text-ink-300">
            Descubre oportunidades según tus habilidades y qué tan cerca estás
            de ellas en la red de personas, empresas y proyectos.
          </p>
        </div>

        <p className="relative text-sm text-ink-500">
          Proyecto de Bases de Datos · Neo4j
        </p>
      </div>

      {/* Formulario */}
      <div className="flex flex-1 items-center justify-center px-4 py-12 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <BrandMarkView />
            <span className="text-xl font-bold tracking-tight text-ink-900">
              DuProGraphic
            </span>
          </div>

          <h2 className="text-3xl font-bold tracking-tight text-ink-900">
            Iniciar sesión
          </h2>
          <p className="mt-2 text-ink-500">Entra a tu red.</p>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            <div>
              <span className="mb-2 block text-sm font-medium text-ink-700">
                Tipo de acceso
              </span>
              <div className="grid grid-cols-3 gap-2">
                {ROLES.map((opcion) => (
                  <button
                    key={opcion.id}
                    type="button"
                    onClick={() => setRol(opcion.id)}
                    aria-pressed={rol === opcion.id}
                    className={`flex flex-col items-center gap-1 rounded-xl border-2 px-2 py-3 text-sm font-medium transition ${
                      rol === opcion.id
                        ? "border-brand-600 bg-brand-50 text-brand-700"
                        : "border-ink-100 bg-white text-ink-500 hover:border-ink-300"
                    }`}
                  >
                    <opcion.icon className="h-5 w-5" />
                    {opcion.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label
                htmlFor="correo"
                className="mb-1.5 block text-sm font-medium text-ink-700"
              >
                Correo electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-300" />
                <input
                  id="correo"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="tucorreo@ejemplo.com"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  className="w-full rounded-xl border border-ink-100 bg-white py-3 pl-10 pr-3 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-ink-700"
              >
                Contraseña
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-300" />
                <input
                  id="password"
                  type={verPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-ink-100 bg-white py-3 pl-10 pr-11 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                />
                <button
                  type="button"
                  onClick={() => setVerPassword((v) => !v)}
                  aria-label={
                    verPassword ? "Ocultar contraseña" : "Mostrar contraseña"
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-300 hover:text-ink-700"
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
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {cargando && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              )}
              {cargando ? "Ingresando..." : "Entrar"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-ink-500">
            ¿No tienes cuenta?{" "}
            <Link
              to="/register"
              className="font-semibold text-brand-700 hover:underline"
            >
              Crear cuenta
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
