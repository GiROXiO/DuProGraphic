import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Briefcase, Eye, EyeOff, Lock, Mail, User } from "lucide-react";
import api, { saveSession } from "../../api";
import { mensajeError } from "../../formErrors";
import BrandMarkView from "../reusable/BrandMarkView";

const TIPOS = [
  { id: "usuario", icon: User, label: "Persona" },
  { id: "empresa", icon: Briefcase, label: "Empresa" },
];

const ETIQUETAS = {
  nombre: "Nombre",
  correo: "Correo",
  password: "Contraseña",
  perfil_profesional: "Titular profesional",
  universidad: "Universidad",
  sector: "Sector",
};

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-3 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

export default function RegisterView() {
  const [rol, setRol] = useState("usuario");
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [repetida, setRepetida] = useState("");
  const [titular, setTitular] = useState("");
  const [universidad, setUniversidad] = useState("");
  const [sector, setSector] = useState("");
  const [verPassword, setVerPassword] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const esPersona = rol === "usuario";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== repetida) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setCargando(true);
    try {
      const cuerpo = esPersona
        ? {
            rol,
            nombre,
            correo,
            password,
            perfil_profesional: titular,
            universidad: universidad || null,
          }
        : { rol, nombre, correo, password, sector };
      const res = await api.post("/api/auth/register", cuerpo);
      saveSession(res.data.token, res.data.data);
      // Cada tipo de cuenta empieza completando lo suyo.
      navigate(esPersona ? "/profile" : "/company", { replace: true });
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo crear la cuenta"));
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center gap-3">
          <BrandMarkView />
          <span className="text-xl font-bold tracking-tight text-ink-900">
            DuProGraphic
          </span>
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-ink-900">
          Crear cuenta
        </h1>
        <p className="mt-2 text-ink-500">
          Únete a la red. Puedes completar el resto de tu perfil después.
        </p>

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
              Tipo de cuenta
            </span>
            <div className="grid grid-cols-2 gap-2">
              {TIPOS.map((tipo) => (
                <button
                  key={tipo.id}
                  type="button"
                  onClick={() => setRol(tipo.id)}
                  aria-pressed={rol === tipo.id}
                  className={`flex flex-col items-center gap-1 rounded-xl border-2 px-2 py-3 text-sm font-medium transition ${
                    rol === tipo.id
                      ? "border-brand-600 bg-brand-50 text-brand-700"
                      : "border-ink-100 bg-white text-ink-500 hover:border-ink-300"
                  }`}
                >
                  <tipo.icon className="h-5 w-5" />
                  {tipo.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label
              htmlFor="nombre"
              className="mb-1.5 block text-sm font-medium text-ink-700"
            >
              {esPersona ? "Nombre completo" : "Nombre de la empresa"}
            </label>
            <input
              id="nombre"
              required
              maxLength={140}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className={campo}
            />
          </div>

          {esPersona ? (
            <>
              <div>
                <label
                  htmlFor="titular"
                  className="mb-1.5 block text-sm font-medium text-ink-700"
                >
                  Titular profesional
                </label>
                <input
                  id="titular"
                  required
                  maxLength={180}
                  placeholder="Ej. Analista de datos"
                  value={titular}
                  onChange={(e) => setTitular(e.target.value)}
                  className={campo}
                />
              </div>
              <div>
                <label
                  htmlFor="universidad"
                  className="mb-1.5 block text-sm font-medium text-ink-700"
                >
                  Universidad{" "}
                  <span className="font-normal text-ink-300">(opcional)</span>
                </label>
                <input
                  id="universidad"
                  maxLength={160}
                  value={universidad}
                  onChange={(e) => setUniversidad(e.target.value)}
                  className={campo}
                />
              </div>
            </>
          ) : (
            <div>
              <label
                htmlFor="sector"
                className="mb-1.5 block text-sm font-medium text-ink-700"
              >
                Sector
              </label>
              <input
                id="sector"
                required
                maxLength={120}
                placeholder="Ej. Fintech"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className={campo}
              />
            </div>
          )}

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
                maxLength={254}
                placeholder="tucorreo@ejemplo.com"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                className={`${campo} pl-10`}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-ink-700"
            >
              Contraseña{" "}
              <span className="font-normal text-ink-300">
                (mínimo 10 caracteres)
              </span>
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-300" />
              <input
                id="password"
                type={verPassword ? "text" : "password"}
                required
                minLength={10}
                maxLength={256}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`${campo} pl-10 pr-11`}
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

          <div>
            <label
              htmlFor="repetida"
              className="mb-1.5 block text-sm font-medium text-ink-700"
            >
              Repite la contraseña
            </label>
            <input
              id="repetida"
              type={verPassword ? "text" : "password"}
              required
              autoComplete="new-password"
              value={repetida}
              onChange={(e) => setRepetida(e.target.value)}
              className={campo}
            />
          </div>

          <button
            type="submit"
            disabled={cargando}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {cargando && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            )}
            {cargando ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-500">
          ¿Ya tienes cuenta?{" "}
          <Link
            to="/login"
            className="font-semibold text-brand-700 hover:underline"
          >
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
