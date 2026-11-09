import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

// Etapas del proceso, en orden. Aceptada y rechazada son definitivas.
const ETAPAS = [
  { id: "aplicado", texto: "Recibida" },
  { id: "en revisión", texto: "En revisión" },
  { id: "entrevista", texto: "Entrevista" },
  { id: "oferta", texto: "Oferta enviada" },
  { id: "aceptado", texto: "Aceptada" },
  { id: "rechazado", texto: "Rechazada" },
];
const FINALES = ["aceptado", "rechazado"];
const textoEtapa = (id) => ETAPAS.find((e) => e.id === id)?.texto ?? id;

const claseEtapa = {
  aplicado: "bg-ink-100 text-ink-700",
  "en revisión": "bg-amber-50 text-amber-700",
  entrevista: "bg-brand-50 text-brand-700",
  oferta: "bg-signal-50 text-signal-600",
  aceptado: "bg-signal-600 text-white",
  rechazado: "bg-red-50 text-red-700",
};

function FilaPostulante({ p, companyId, ofertaId, onLista }) {
  const [pendiente, setPendiente] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const final = FINALES.includes(p.estado);

  const aplicar = async (estado) => {
    setError("");
    setOcupado(true);
    try {
      const res = await api.put(
        `/api/companies/${companyId}/offers/${ofertaId}/applications/${p.id}`,
        { estado },
      );
      onLista(res.data.data);
      setPendiente(null);
    } catch (err) {
      setError(mensajeError(err, {}, "No se pudo cambiar el estado"));
    } finally {
      setOcupado(false);
    }
  };

  const elegir = (estado) => {
    if (estado === p.estado) return;
    if (FINALES.includes(estado)) setPendiente(estado);
    else aplicar(estado);
  };

  const coincide = p.habilidades_coincidentes.length;

  return (
    <li className="rounded-xl border border-ink-100 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={`/people/${p.id}`}
            className="font-semibold text-ink-900 hover:text-brand-700 hover:underline"
          >
            {p.nombre}
          </Link>
          <p className="text-xs text-ink-500">
            {[p.titular, p.ubicacion].filter(Boolean).join(" · ")}
            {p.fecha ? ` · se postuló el ${p.fecha}` : ""}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`whitespace-nowrap rounded-lg px-3 py-1 text-xs font-semibold ${claseEtapa[p.estado] ?? claseEtapa.aplicado}`}
          >
            {textoEtapa(p.estado)}
          </span>
          <select
            aria-label={`Etapa de ${p.nombre}`}
            value={p.estado}
            disabled={ocupado || final}
            onChange={(e) => elegir(e.target.value)}
            title={final ? "La decisión ya es definitiva" : "Cambiar la etapa"}
            className="rounded-lg border border-ink-100 bg-white px-2 py-1.5 text-xs font-medium text-ink-700 outline-none focus:border-brand-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {ETAPAS.map((e) => (
              <option key={e.id} value={e.id}>
                {e.texto}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        {p.total_requeridas > 0 ? (
          <span className="rounded-md bg-brand-50 px-2 py-0.5 font-semibold text-brand-700">
            {coincide} de {p.total_requeridas} habilidades requeridas
          </span>
        ) : (
          <span className="text-ink-500">La oferta no pide habilidades</span>
        )}
        {p.habilidades_coincidentes.map((h) => (
          <span
            key={h}
            className="rounded-md bg-signal-50 px-2 py-0.5 text-signal-600"
          >
            {h}
          </span>
        ))}
        {p.habilidades_faltantes.map((h) => (
          <span
            key={h}
            className="rounded-md border border-dashed border-ink-300 px-2 py-0.5 text-ink-500"
            title="Requerida y no registrada en su perfil"
          >
            falta: {h}
          </span>
        ))}
        {p.contactos_en_empresa > 0 && (
          <span className="rounded-md bg-amber-50 px-2 py-0.5 font-semibold text-amber-700">
            {p.contactos_en_empresa}{" "}
            {p.contactos_en_empresa === 1
              ? "contacto trabaja"
              : "contactos trabajan"}{" "}
            en tu empresa
          </span>
        )}
      </div>

      {pendiente && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg bg-ink-100/60 p-3 text-xs">
          <span className="text-ink-700">
            Marcar a {p.nombre} como <strong>{textoEtapa(pendiente)}</strong> es
            definitivo.
          </span>
          <button
            onClick={() => aplicar(pendiente)}
            disabled={ocupado}
            className="rounded-lg bg-brand-600 px-3 py-1.5 font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {ocupado ? "Guardando..." : "Confirmar"}
          </button>
          <button
            onClick={() => setPendiente(null)}
            disabled={ocupado}
            className="rounded-lg border border-ink-100 bg-white px-3 py-1.5 font-semibold text-ink-700 transition hover:bg-ink-100"
          >
            Cancelar
          </button>
        </div>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </li>
  );
}

function Recomendados({ ofertaId, abierta }) {
  const { data, loading, error } = useFetch(
    `/api/offers/${ofertaId}/candidates`,
  );

  if (loading)
    return <p className="text-sm text-ink-500">Buscando en el grafo...</p>;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!data || data.length === 0) {
    return (
      <p className="text-sm text-ink-500">
        {abierta
          ? "No hay personas con las habilidades de esta oferta que aún no se hayan postulado."
          : "Solo se recomiendan candidatos para ofertas abiertas."}
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {data.map((c) => (
        <li
          key={c.candidato_id}
          className="rounded-xl border border-ink-100 p-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Link
              to={`/people/${c.candidato_id}`}
              className="font-semibold text-ink-900 hover:text-brand-700 hover:underline"
            >
              {c.candidato}
            </Link>
            <span className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">
              {c.cantidad_habilidades}{" "}
              {c.cantidad_habilidades === 1
                ? "habilidad coincide"
                : "habilidades coinciden"}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {c.habilidades_coincidentes.map((h) => (
              <span
                key={h}
                className="rounded-md bg-signal-50 px-2 py-0.5 text-signal-600"
              >
                {h}
              </span>
            ))}
            {c.contactos_que_se_postularon > 0 && (
              <span className="rounded-md bg-amber-50 px-2 py-0.5 font-semibold text-amber-700">
                {c.contactos_que_se_postularon}{" "}
                {c.contactos_que_se_postularon === 1
                  ? "contacto suyo ya se postuló"
                  : "contactos suyos ya se postularon"}
              </span>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function CandidatesPanelView({ companyId, oferta }) {
  const { data, loading, error } = useFetch(
    `/api/companies/${companyId}/offers/${oferta.id}/applications`,
  );
  // Tras cada cambio la API devuelve la lista completa y reemplaza a la inicial.
  const [lista, setLista] = useState(null);
  const [pestana, setPestana] = useState("postulados");

  const postulantes = lista ?? data ?? [];
  const abierta = oferta.estado?.toLowerCase() === "abierta";

  const clasePestana = (id) =>
    `-mb-px border-b-2 px-3 py-2 text-xs font-semibold transition ${
      pestana === id
        ? "border-brand-600 text-brand-700"
        : "border-transparent text-ink-500 hover:text-ink-900"
    }`;

  return (
    <div className="mt-4 space-y-4 border-t border-ink-100 pt-4">
      <div className="flex gap-1 border-b border-ink-100" role="tablist">
        <button
          role="tab"
          aria-selected={pestana === "postulados"}
          onClick={() => setPestana("postulados")}
          className={clasePestana("postulados")}
        >
          Postulados ({postulantes.length})
        </button>
        <button
          role="tab"
          aria-selected={pestana === "recomendados"}
          onClick={() => setPestana("recomendados")}
          className={clasePestana("recomendados")}
        >
          Recomendados por el grafo
        </button>
      </div>

      {pestana === "postulados" ? (
        <>
          {loading && (
            <p className="text-sm text-ink-500">Cargando candidatos...</p>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!loading && !error && postulantes.length === 0 && (
            <p className="text-sm text-ink-500">
              Todavía nadie se ha postulado a esta oferta.
            </p>
          )}
          <ul className="space-y-2">
            {postulantes.map((p) => (
              <FilaPostulante
                key={p.id}
                p={p}
                companyId={companyId}
                ofertaId={oferta.id}
                onLista={setLista}
              />
            ))}
          </ul>
        </>
      ) : (
        <Recomendados ofertaId={oferta.id} abierta={abierta} />
      )}
    </div>
  );
}
