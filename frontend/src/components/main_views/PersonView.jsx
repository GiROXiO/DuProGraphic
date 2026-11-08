import { Link, useParams } from "react-router-dom";
import ShellView from "../nav_layout/ShellView";
import ConnectButtonView from "../reusable/ConnectButtonView";
import useFetch from "../../useFetch";

function Seccion({ titulo, children }) {
  return (
    <section className="rounded-2xl border border-ink-100 bg-white p-6">
      <h2 className="mb-3 font-bold text-ink-900">{titulo}</h2>
      {children}
    </section>
  );
}

function Dato({ etiqueta, valor }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-500">
        {etiqueta}
      </p>
      <p className="mt-0.5 text-sm text-ink-900">
        {valor || "Sin especificar"}
      </p>
    </div>
  );
}

function Perfil({ id }) {
  const { data: p, loading, error } = useFetch(`/api/people/${id}`);

  if (loading) return <p className="text-ink-500">Cargando perfil...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  // Solo se enlaza si es http(s): evita enlaces como javascript: guardados en datos antiguos.
  const portafolioValido = /^https?:\/\//i.test(p.sitio_portafolio ?? "");

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-[linear-gradient(120deg,#0d0f1a_0%,#2b3354_55%,#6844f0_135%)] p-6 text-white sm:p-8">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-2xl bg-brand-500 text-3xl font-bold ring-4 ring-white/10">
            {p.nombre?.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-bold tracking-tight">{p.nombre}</h1>
            <p className="mt-1 text-ink-300">{p.perfil_profesional}</p>
            <p className="mt-1 text-sm text-ink-300">
              {[p.universidad, p.ubicacion].filter(Boolean).join(" · ")}
              {` · ${p.contactos} ${p.contactos === 1 ? "contacto" : "contactos"}`}
            </p>
          </div>
          <ConnectButtonView
            key={p.relacion}
            personaId={p.id}
            relacion={p.relacion}
          />
        </div>
      </section>

      {p.contactos_en_comun.length > 0 && (
        <Seccion titulo={`Contactos en común (${p.contactos_en_comun.length})`}>
          <div className="flex flex-wrap gap-2">
            {p.contactos_en_comun.map((c) => (
              <Link
                key={c.id}
                to={`/people/${c.id}`}
                className="rounded-lg bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700 hover:bg-brand-100"
              >
                {c.nombre}
              </Link>
            ))}
          </div>
        </Seccion>
      )}

      <Seccion titulo="Acerca de">
        <p className="whitespace-pre-line text-sm text-ink-700">
          {p.acerca_de || "Este perfil todavía no incluye una presentación."}
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <Dato
            etiqueta="Formación"
            valor={[p.educacion_detalle, p.universidad]
              .filter(Boolean)
              .join(" · ")}
          />
          <Dato
            etiqueta="Experiencia"
            valor={
              p.anios_experiencia != null ? `${p.anios_experiencia} años` : null
            }
          />
          <Dato etiqueta="Idiomas" valor={p.idiomas} />
        </div>
        {portafolioValido && (
          <a
            href={p.sitio_portafolio}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-block rounded-xl border border-ink-100 px-4 py-2 text-sm font-semibold text-brand-600 hover:bg-brand-50"
          >
            Abrir portafolio
          </a>
        )}
      </Seccion>

      {p.experiencia && (
        <Seccion titulo="Experiencia y objetivos">
          <p className="whitespace-pre-line text-sm text-ink-700">
            {p.experiencia}
          </p>
        </Seccion>
      )}
      {p.logros && (
        <Seccion titulo="Logros destacados">
          <p className="whitespace-pre-line text-sm text-ink-700">{p.logros}</p>
        </Seccion>
      )}
      {p.areas_interes && (
        <Seccion titulo="Áreas de interés">
          <p className="text-sm text-ink-700">{p.areas_interes}</p>
        </Seccion>
      )}

      <Seccion titulo="Habilidades">
        {p.habilidades.length === 0 ? (
          <p className="text-sm text-ink-500">
            Todavía no hay habilidades asociadas.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {p.habilidades.map((h) => (
              <span
                key={h.id}
                className="rounded-lg bg-signal-50 px-3 py-1.5 text-sm font-medium text-signal-600"
              >
                {h.nombre}{" "}
                <span className="text-xs opacity-70">· {h.nivel}</span>
              </span>
            ))}
          </div>
        )}
      </Seccion>

      <div className="grid gap-6 md:grid-cols-2">
        <Seccion titulo="Experiencia en empresas">
          {p.empresas.length === 0 ? (
            <p className="text-sm text-ink-500">
              No hay experiencia empresarial en el perfil.
            </p>
          ) : (
            <ul className="space-y-3">
              {p.empresas.map((e) => (
                <li
                  key={e.id}
                  className="flex items-start justify-between gap-3"
                >
                  <div>
                    <p className="text-sm font-semibold text-ink-900">
                      {e.empresa}
                    </p>
                    <p className="text-xs text-ink-500">
                      {[e.cargo, e.sector, e.periodo]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </div>
                  <span className="rounded-md bg-ink-100 px-2 py-0.5 text-xs text-ink-700">
                    {e.actual ? "Actual" : "Anterior"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Seccion>

        <Seccion titulo="Proyectos">
          {p.proyectos.length === 0 ? (
            <p className="text-sm text-ink-500">No hay proyectos asociados.</p>
          ) : (
            <ul className="space-y-3">
              {p.proyectos.map((pr) => (
                <li key={pr.id}>
                  <p className="text-sm font-semibold text-ink-900">
                    {pr.nombre}
                  </p>
                  <p className="text-xs text-ink-500">
                    {pr.rol || "Participante"}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Seccion>
      </div>
    </div>
  );
}

export default function PersonView() {
  const { id } = useParams();

  return (
    <ShellView>
      {/* key: al navegar de un perfil a otro se vuelve a cargar desde cero */}
      <Perfil key={id} id={id} />
    </ShellView>
  );
}
