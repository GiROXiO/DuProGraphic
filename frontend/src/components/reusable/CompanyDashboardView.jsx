import { Link } from "react-router-dom";
import useFetch from "../../useFetch";
import SkillBadgeView from "./SkillBadgeView";

function Estadistica({ valor, etiqueta }) {
  return (
    <div className="rounded-2xl border border-ink-100 bg-white p-5">
      <p className="text-3xl font-bold text-ink-900">{valor}</p>
      <p className="mt-1 text-sm text-ink-500">{etiqueta}</p>
    </div>
  );
}

// Panel de inicio de una cuenta de empresa.
export default function CompanyDashboardView({ companyId }) {
  const { data: perfil } = useFetch(`/api/companies/${companyId}/profile`);
  const {
    data: ofertas,
    loading,
    error,
  } = useFetch(`/api/companies/${companyId}/offers`);

  const abiertas =
    ofertas?.filter((o) => o.estado?.toLowerCase() === "abierta").length ?? 0;
  const cerradas = (ofertas?.length ?? 0) - abiertas;
  const postulaciones =
    ofertas?.reduce((suma, o) => suma + (o.postulaciones ?? 0), 0) ?? 0;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-[linear-gradient(120deg,#0d0f1a_0%,#2b3354_55%,#6844f0_135%)] p-6 text-white sm:p-8">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-2xl bg-brand-500 text-2xl font-bold ring-4 ring-white/10">
            {perfil?.nombre?.charAt(0).toUpperCase() ?? "…"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-ink-300">Panel de empresa</p>
            <h1 className="truncate text-2xl font-bold tracking-tight">
              {perfil?.nombre ?? "Cargando..."}
            </h1>
            <p className="mt-1 text-sm text-ink-300">
              {[perfil?.sector, perfil?.ubicacion].filter(Boolean).join(" · ")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-semibold">
            <Link
              to="/offers"
              className="rounded-lg bg-signal-400 px-3 py-2 text-ink-950 hover:opacity-90"
            >
              Publicar oferta
            </Link>
            <Link
              to="/company"
              className="rounded-lg bg-white/10 px-3 py-2 hover:bg-white/20"
            >
              Editar perfil
            </Link>
          </div>
        </div>
      </section>

      {loading && <p className="text-ink-500">Cargando tus ofertas...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {ofertas && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Estadistica valor={abiertas} etiqueta="Ofertas abiertas" />
            <Estadistica valor={cerradas} etiqueta="Ofertas cerradas" />
            <Estadistica
              valor={postulaciones}
              etiqueta="Postulaciones recibidas"
            />
          </div>

          <section>
            <div className="mb-4 flex items-end justify-between">
              <h2 className="text-lg font-bold text-ink-900">Tus ofertas</h2>
              <Link
                to="/offers"
                className="text-sm font-medium text-brand-600 hover:underline"
              >
                Gestionar
              </Link>
            </div>

            {ofertas.length === 0 && (
              <p className="rounded-2xl border border-ink-100 bg-white p-6 text-ink-500">
                Aún no has publicado ofertas.{" "}
                <Link
                  to="/offers"
                  className="font-medium text-brand-600 hover:underline"
                >
                  Publica la primera
                </Link>
                .
              </p>
            )}

            <div className="space-y-3">
              {ofertas.map((o) => (
                <article
                  key={o.id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-ink-100 bg-white p-5"
                >
                  <div className="min-w-0">
                    <h3 className="font-semibold text-ink-900">{o.titulo}</h3>
                    <p className="mt-0.5 text-xs capitalize text-ink-500">
                      {[o.modalidad, o.experiencia].filter(Boolean).join(" · ")}
                    </p>
                    {o.habilidades?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {o.habilidades.map((h) => (
                          <SkillBadgeView key={h} nombre={h} />
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-ink-500">
                      {o.postulaciones}{" "}
                      {o.postulaciones === 1 ? "postulación" : "postulaciones"}
                    </span>
                    <span
                      className={`rounded-lg px-3 py-1 text-xs font-semibold ${
                        o.estado?.toLowerCase() === "abierta"
                          ? "bg-signal-50 text-signal-600"
                          : "bg-ink-100 text-ink-500"
                      }`}
                    >
                      {o.estado?.toLowerCase() === "abierta"
                        ? "Abierta"
                        : "Cerrada"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
