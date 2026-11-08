import useFetch from "../../useFetch";

// Cabecera con el resumen del perfil del usuario.
export default function SidebarProfileView({ userId }) {
  const {
    data: perfil,
    loading,
    error,
  } = useFetch(`/api/users/${userId}/profile`);

  return (
    <section className="relative overflow-hidden rounded-3xl bg-[linear-gradient(120deg,#0d0f1a_0%,#2b3354_55%,#6844f0_135%)] p-6 text-white sm:p-8">
      <svg
        className="absolute right-0 top-0 h-full w-1/2 opacity-30"
        viewBox="0 0 200 120"
        preserveAspectRatio="xMaxYMid slice"
        aria-hidden="true"
      >
        <g stroke="#b4bad3" strokeWidth="0.8">
          <line x1="30" y1="90" x2="90" y2="35" />
          <line x1="90" y1="35" x2="150" y2="75" />
          <line x1="150" y1="75" x2="180" y2="20" />
          <line x1="90" y1="35" x2="120" y2="110" />
        </g>
        <circle cx="30" cy="90" r="4" fill="#fff" />
        <circle cx="90" cy="35" r="6" fill="#2be0b0" />
        <circle cx="150" cy="75" r="5" fill="#fff" />
        <circle cx="180" cy="20" r="3.5" fill="#7c5cff" />
        <circle cx="120" cy="110" r="3.5" fill="#fff" />
      </svg>

      {loading && (
        <p className="relative text-ink-300">Cargando tu perfil...</p>
      )}
      {error && <p className="relative text-red-300">{error}</p>}

      {perfil && (
        <div className="relative flex items-center gap-5">
          <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-2xl bg-brand-500 text-2xl font-bold ring-4 ring-white/10">
            {perfil.nombre?.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-sm text-ink-300">Bienvenido de vuelta</p>
            <h1 className="truncate text-2xl font-bold tracking-tight">
              {perfil.nombre}
            </h1>
            <p className="mt-1 text-sm text-ink-300">
              {[perfil.perfil_profesional, perfil.universidad, perfil.ubicacion]
                .filter(Boolean)
                .join(" · ")}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
