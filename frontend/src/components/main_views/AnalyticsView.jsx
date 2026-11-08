import { useState } from "react";
import ShellView from "../nav_layout/ShellView";
import BarListView from "../reusable/BarListView";
import SimpleTableView from "../reusable/SimpleTableView";
import PathView from "../reusable/PathView";
import api, { getUser } from "../../api";
import useFetch from "../../useFetch";

const TABS = {
  administrador: [
    { id: "panel", label: "Panel" },
    { id: "relaciones", label: "Relaciones" },
    { id: "rutas", label: "Rutas" },
    { id: "candidatos", label: "Candidatos" },
  ],
  usuario: [
    { id: "rutas", label: "Mi ruta" },
    { id: "recomendaciones", label: "Recomendaciones" },
  ],
  empresa: [{ id: "candidatos", label: "Candidatos" }],
};

const SUBTITULO = {
  administrador:
    "Métricas de toda la red y preguntas que solo un grafo responde con facilidad.",
  usuario:
    "Descubre qué tan cerca estás de una empresa y a quién deberías conocer.",
  empresa:
    "Encuentra candidatos para tus ofertas según habilidades y contactos.",
};

const card = "rounded-2xl border border-ink-100 bg-white p-6";
const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";
const boton =
  "rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50";

function Estado({ loading, error }) {
  if (loading)
    return <p className="text-sm text-ink-500">Consultando el grafo...</p>;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  return null;
}

function Selector({ id, etiqueta, valor, onChange, opciones }) {
  return (
    <div className="min-w-0 flex-1">
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-medium text-ink-700"
      >
        {etiqueta}
      </label>
      <select
        id={id}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        className={campo}
      >
        <option value="">Elegir...</option>
        {opciones.map((o) => (
          <option key={o.id} value={o.id}>
            {o.nombre}
          </option>
        ))}
      </select>
    </div>
  );
}

// ---------------------------------------------------------------- Panel (admin)

function PanelTab() {
  const resumen = useFetch("/api/analytics/summary");
  const influyentes = useFetch("/api/analytics/influential-users");
  const demandadas = useFetch("/api/analytics/demanded-skills");
  const comunidades = useFetch("/api/analytics/communities");

  const etiquetas = {
    Usuario: "Usuarios",
    Empresa: "Empresas",
    Oferta: "Ofertas",
    Habilidad: "Habilidades",
    Proyecto: "Proyectos",
  };

  return (
    <div className="space-y-6">
      <Estado loading={resumen.loading} error={resumen.error} />
      {resumen.data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          {Object.entries(etiquetas).map(([k, nombre]) => (
            <div
              key={k}
              className="rounded-2xl border border-ink-100 bg-white p-4"
            >
              <p className="text-2xl font-bold text-ink-900">
                {resumen.data[k]}
              </p>
              <p className="text-xs text-ink-500">{nombre}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className={card}>
          <h2 className="font-bold text-ink-900">Usuarios más influyentes</h2>
          <p className="mb-4 mt-1 text-xs text-ink-500">
            Por número de contactos profesionales directos.
          </p>
          <Estado loading={influyentes.loading} error={influyentes.error} />
          {influyentes.data && (
            <BarListView
              items={influyentes.data
                .slice(0, 8)
                .map((u) => ({
                  label: u.usuario,
                  value: u.contactos_directos,
                }))}
            />
          )}
        </section>

        <section className={card}>
          <h2 className="font-bold text-ink-900">Habilidades más demandadas</h2>
          <p className="mb-4 mt-1 text-xs text-ink-500">
            Por número de ofertas que las requieren.
          </p>
          <Estado loading={demandadas.loading} error={demandadas.error} />
          {demandadas.data && (
            <BarListView
              color="bg-signal-600"
              items={demandadas.data.slice(0, 8).map((h) => ({
                label: h.habilidad,
                value: h.ofertas_que_la_requieren,
                detalle: `${h.ofertas_que_la_exigen} la exigen`,
              }))}
            />
          )}
        </section>
      </div>

      <section className={card}>
        <h2 className="font-bold text-ink-900">Comunidades detectadas</h2>
        <p className="mb-4 mt-1 text-xs text-ink-500">
          Grupos de personas muy conectadas entre sí (Label Propagation sobre
          CONECTA_CON).
        </p>
        <Estado loading={comunidades.loading} error={comunidades.error} />
        <div className="grid gap-4 md:grid-cols-2">
          {comunidades.data?.map((c) => (
            <div
              key={c.comunidad}
              className="rounded-xl border border-ink-100 p-4"
            >
              <p className="mb-2 text-sm font-semibold text-ink-900">
                Comunidad {c.comunidad} · {c.usuarios}{" "}
                {c.usuarios === 1 ? "persona" : "personas"}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {c.miembros.map((m) => (
                  <span
                    key={m.id}
                    className="rounded-md bg-brand-50 px-2 py-0.5 text-xs text-brand-700"
                  >
                    {m.nombre}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- Relaciones (admin)

const VISTAS = [
  {
    id: "contactos",
    label: "Contactos en común",
    pregunta: "¿Qué contactos en común existen entre dos profesionales?",
    url: "/api/analytics/common-contacts",
    columnas: [
      { key: "usuario1", label: "Persona 1" },
      { key: "usuario2", label: "Persona 2" },
      { key: "contactos_en_comun", label: "Contactos en común" },
      { key: "cantidad_contactos", label: "Cantidad" },
    ],
  },
  {
    id: "habilidades",
    label: "Habilidades similares",
    pregunta: "¿Qué usuarios tienen habilidades similares?",
    url: "/api/analytics/similar-skills",
    columnas: [
      { key: "usuario1", label: "Persona 1" },
      { key: "usuario2", label: "Persona 2" },
      { key: "habilidades_en_comun", label: "Habilidades en común" },
      { key: "cantidad_habilidades", label: "Cantidad" },
    ],
  },
  {
    id: "proy-miembros",
    label: "Proyectos y miembros",
    pregunta: "¿Qué proyectos comparten miembros?",
    url: "/api/analytics/project-overlaps",
    pick: (d) => d.por_miembros,
    columnas: [
      { key: "proyecto1", label: "Proyecto 1" },
      { key: "proyecto2", label: "Proyecto 2" },
      { key: "miembros_compartidos", label: "Miembros compartidos" },
      { key: "cantidad_miembros", label: "Cantidad" },
    ],
  },
  {
    id: "proy-tec",
    label: "Proyectos y tecnologías",
    pregunta: "¿Qué proyectos comparten tecnologías?",
    url: "/api/analytics/project-overlaps",
    pick: (d) => d.por_tecnologias,
    columnas: [
      { key: "proyecto1", label: "Proyecto 1" },
      { key: "proyecto2", label: "Proyecto 2" },
      { key: "tecnologias_compartidas", label: "Tecnologías compartidas" },
      { key: "cantidad_compartida", label: "Cantidad" },
    ],
  },
];

function VistaRelacion({ vista }) {
  const { data, loading, error } = useFetch(vista.url);
  const filas = data ? (vista.pick ? vista.pick(data) : data) : null;

  return (
    <div className="space-y-4">
      <p className="text-sm text-ink-500">{vista.pregunta}</p>
      <Estado loading={loading} error={error} />
      {filas && <SimpleTableView columns={vista.columnas} rows={filas} />}
    </div>
  );
}

function RelacionesTab() {
  const [vistaId, setVistaId] = useState(VISTAS[0].id);
  const vista = VISTAS.find((v) => v.id === vistaId);

  return (
    <section className={`${card} space-y-5`}>
      <div className="flex flex-wrap gap-2">
        {VISTAS.map((v) => (
          <button
            key={v.id}
            onClick={() => setVistaId(v.id)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              v.id === vistaId
                ? "bg-brand-600 text-white"
                : "bg-ink-100 text-ink-700 hover:bg-ink-100/70"
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
      <VistaRelacion key={vista.id} vista={vista} />
    </section>
  );
}

// ---------------------------------------------------------------- Rutas

function RutasTab({ user, esAdmin }) {
  const usuarios = useFetch(esAdmin ? "/api/lookups/users" : null);
  const empresas = useFetch("/api/lookups/companies");
  const [usuarioId, setUsuarioId] = useState(esAdmin ? "" : user.entidad_id);
  const [empresaId, setEmpresaId] = useState("");
  const [ruta, setRuta] = useState(undefined); // undefined = sin buscar, null = sin ruta
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const buscar = async (e) => {
    e.preventDefault();
    setError("");
    setRuta(undefined);
    setCargando(true);
    try {
      const res = await api.get(`/api/users/${usuarioId}/path-to/${empresaId}`);
      setRuta(res.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo consultar la ruta.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <section className={`${card} space-y-6`}>
      <p className="text-sm text-ink-500">
        ¿Cuál es la ruta más corta entre una persona y una empresa? Puede pasar
        por contactos, habilidades, proyectos u ofertas (hasta 6 relaciones).
      </p>

      <form onSubmit={buscar} className="flex flex-wrap items-end gap-4">
        {esAdmin && (
          <Selector
            id="ruta-usuario"
            etiqueta="Persona de origen"
            valor={usuarioId}
            onChange={setUsuarioId}
            opciones={usuarios.data ?? []}
          />
        )}
        <Selector
          id="ruta-empresa"
          etiqueta="Empresa de destino"
          valor={empresaId}
          onChange={setEmpresaId}
          opciones={empresas.data ?? []}
        />
        <button
          type="submit"
          disabled={!usuarioId || !empresaId || cargando}
          className={boton}
        >
          {cargando ? "Buscando..." : "Buscar ruta"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {ruta === null && (
        <p className="text-sm text-ink-500">
          No se encontró una ruta de hasta 6 relaciones.
        </p>
      )}
      {ruta && <PathView ruta={ruta} />}
    </section>
  );
}

// ---------------------------------------------------------------- Candidatos

function CandidatosLista({ ofertaId }) {
  const { data, loading, error } = useFetch(
    `/api/offers/${ofertaId}/candidates`,
  );

  return (
    <div className="space-y-3">
      <Estado loading={loading} error={error} />
      {data && (
        <SimpleTableView
          vacio="No hay candidatos con las habilidades requeridas (o la oferta no está abierta)."
          columns={[
            { key: "candidato", label: "Candidato" },
            {
              key: "habilidades_coincidentes",
              label: "Habilidades que coinciden",
            },
            { key: "cantidad_habilidades", label: "Coinciden" },
            {
              key: "contactos_que_se_postularon",
              label: "Contactos ya postulados",
            },
          ]}
          rows={data}
        />
      )}
    </div>
  );
}

function CandidatosTab({ user, esAdmin }) {
  const ofertas = useFetch(
    esAdmin
      ? "/api/lookups/offers"
      : `/api/companies/${user.entidad_id}/offers`,
  );
  const [ofertaId, setOfertaId] = useState("");

  const opciones = (ofertas.data ?? []).map((o) => ({
    id: o.id,
    nombre: esAdmin
      ? `${o.nombre}${o.empresa ? ` · ${o.empresa}` : ""}`
      : o.titulo,
  }));

  return (
    <section className={`${card} space-y-6`}>
      <p className="text-sm text-ink-500">
        ¿Qué candidatos podrían recomendarse para una oferta según sus
        competencias y sus conexiones con quienes ya se postularon?
      </p>
      <Estado loading={ofertas.loading} error={ofertas.error} />
      <div className="max-w-xl">
        <Selector
          id="oferta"
          etiqueta="Oferta"
          valor={ofertaId}
          onChange={setOfertaId}
          opciones={opciones}
        />
      </div>
      {ofertaId && <CandidatosLista key={ofertaId} ofertaId={ofertaId} />}
    </section>
  );
}

// ---------------------------------------------------------------- Recomendaciones (usuario)

function RecomendacionesTab({ user }) {
  const { data, loading, error } = useFetch(
    `/api/users/${user.entidad_id}/recommendations`,
  );

  return (
    <div className="space-y-6">
      <Estado loading={loading} error={error} />
      {data && (
        <>
          <section className={card}>
            <h2 className="font-bold text-ink-900">Contactos recomendados</h2>
            <p className="mb-4 mt-1 text-xs text-ink-500">
              Contactos de tus contactos con los que aún no estás conectado.
            </p>
            <SimpleTableView
              vacio="Aún no hay recomendaciones de contactos."
              columns={[
                { key: "contacto_recomendado", label: "Persona" },
                { key: "contactos_en_comun", label: "En común" },
                { key: "recomendados_por", label: "Te lo recomiendan" },
              ]}
              rows={data.contactos}
            />
          </section>
          <section className={card}>
            <h2 className="font-bold text-ink-900">Posibles colaboradores</h2>
            <p className="mb-4 mt-1 text-xs text-ink-500">
              Personas con las tecnologías que usan tus proyectos y con quienes
              aún no compartes uno.
            </p>
            <SimpleTableView
              vacio="Aún no hay colaboradores recomendados."
              columns={[
                { key: "colaborador_recomendado", label: "Persona" },
                { key: "tecnologias_en_comun", label: "Tecnologías en común" },
                { key: "cantidad_tecnologias", label: "Cantidad" },
              ]}
              rows={data.colaboradores}
            />
          </section>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Página

export default function AnalyticsView() {
  const user = getUser();
  const tabs = TABS[user?.rol] ?? [];
  const [tab, setTab] = useState(tabs[0]?.id);
  const esAdmin = user?.rol === "administrador";
  const sinPerfil = user?.rol === "usuario" && !user?.entidad_id;

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Análisis del grafo
        </h1>
        <p className="mt-1 text-sm text-ink-500">{SUBTITULO[user?.rol]}</p>
      </header>

      {tabs.length === 0 || sinPerfil ? (
        <div className={`${card} text-center text-ink-500`}>
          No hay análisis disponibles para esta cuenta.
        </div>
      ) : (
        <>
          <nav className="mb-6 flex flex-wrap gap-2 border-b border-ink-100 pb-3">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                  t.id === tab
                    ? "bg-ink-900 text-white"
                    : "text-ink-500 hover:bg-ink-100"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          {tab === "panel" && <PanelTab />}
          {tab === "relaciones" && <RelacionesTab />}
          {tab === "rutas" && <RutasTab user={user} esAdmin={esAdmin} />}
          {tab === "candidatos" && (
            <CandidatosTab user={user} esAdmin={esAdmin} />
          )}
          {tab === "recomendaciones" && <RecomendacionesTab user={user} />}
        </>
      )}
    </ShellView>
  );
}
