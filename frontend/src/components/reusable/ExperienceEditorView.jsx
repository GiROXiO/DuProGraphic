import { useState } from "react";
import { Plus } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";

const ETIQUETAS = { cargo: "Cargo", periodo: "Periodo", actual: "Actual" };

const campo =
  "w-full rounded-lg border border-ink-100 bg-white px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function FilaExperiencia({ item, userId, onLista }) {
  const [editando, setEditando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [cargo, setCargo] = useState(item.cargo ?? "");
  const [periodo, setPeriodo] = useState(item.periodo ?? "");
  const [actual, setActual] = useState(item.actual);

  const guardar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.put(`/api/users/${userId}/experience/${item.id}`, {
        cargo,
        periodo,
        actual,
      });
      onLista(res.data.data);
      setEditando(false);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo guardar"));
    } finally {
      setOcupado(false);
    }
  };

  const quitar = async () => {
    setError("");
    setOcupado(true);
    try {
      const res = await api.delete(
        `/api/users/${userId}/experience/${item.id}`,
      );
      onLista(res.data.data);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo quitar"));
      setOcupado(false);
      setConfirmando(false);
    }
  };

  return (
    <li className="rounded-xl border border-ink-100 px-4 py-3">
      {editando ? (
        <form onSubmit={guardar} className="space-y-3">
          <p className="text-sm font-semibold text-ink-900">{item.empresa}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              required
              maxLength={120}
              value={cargo}
              onChange={(e) => setCargo(e.target.value)}
              placeholder="Cargo"
              aria-label="Cargo"
              className={campo}
            />
            <input
              maxLength={80}
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              placeholder="Periodo (ej. 2021-2023)"
              aria-label="Periodo"
              className={campo}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink-700">
            <input
              type="checkbox"
              checked={actual}
              onChange={(e) => setActual(e.target.checked)}
            />
            Trabajo actualmente aquí
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={ocupado}
              className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
            >
              {ocupado ? "Guardando..." : "Guardar"}
            </button>
            <button
              type="button"
              onClick={() => setEditando(false)}
              disabled={ocupado}
              className="rounded-lg border border-ink-100 px-4 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-ink-900">
              {item.empresa}
              <span
                className={`ml-2 rounded-md px-2 py-0.5 text-xs font-semibold ${
                  item.actual
                    ? "bg-signal-50 text-signal-600"
                    : "bg-ink-100 text-ink-500"
                }`}
              >
                {item.actual ? "Actual" : "Anterior"}
              </span>
            </p>
            <p className="text-xs text-ink-500">
              {[item.cargo, item.sector, item.periodo]
                .filter(Boolean)
                .join(" · ")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {confirmando ? (
              <>
                <span className="text-xs text-ink-500">¿Quitar?</span>
                <button
                  onClick={quitar}
                  disabled={ocupado}
                  className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
                >
                  {ocupado ? "Quitando..." : "Sí, quitar"}
                </button>
                <button
                  onClick={() => setConfirmando(false)}
                  disabled={ocupado}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                >
                  No
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setEditando(true)}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                >
                  Editar
                </button>
                <button
                  onClick={() => setConfirmando(true)}
                  className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-500 transition hover:bg-red-50 hover:text-red-600"
                >
                  Quitar
                </button>
              </>
            )}
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </li>
  );
}

export default function ExperienceEditorView({ userId }) {
  const {
    data: inicial,
    loading,
    error: errorCarga,
  } = useFetch(`/api/users/${userId}/experience`);
  const {
    data: empresas,
    loading: cargandoEmpresas,
    error: errorEmpresas,
    refetch: recargarEmpresas,
  } = useFetch("/api/lookups/companies");

  // Tras cada cambio la API devuelve la lista completa y reemplaza a la inicial.
  const [lista, setLista] = useState(null);
  const [empresaId, setEmpresaId] = useState("");
  const [cargo, setCargo] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [actual, setActual] = useState(true);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const actuales = lista ?? inicial ?? [];
  const disponibles = (empresas ?? []).filter(
    (e) => !actuales.some((a) => a.id === e.id),
  );

  const agregar = async (e) => {
    e.preventDefault();
    setError("");
    setOcupado(true);
    try {
      const res = await api.put(
        `/api/users/${userId}/experience/${empresaId}`,
        {
          cargo,
          periodo,
          actual,
        },
      );
      setLista(res.data.data);
      setEmpresaId("");
      setCargo("");
      setPeriodo("");
      setActual(true);
    } catch (err) {
      setError(mensajeError(err, ETIQUETAS, "No se pudo añadir la empresa"));
    } finally {
      setOcupado(false);
    }
  };

  return (
    <section className="space-y-5 rounded-2xl border border-ink-100 bg-white p-6">
      <div>
        <h2 className="text-lg font-bold text-ink-900">
          Experiencia en empresas
        </h2>
        <p className="mt-1 text-sm text-ink-500">
          Las empresas donde trabajas o trabajaste conectan tu perfil con ellas
          en el grafo y acortan tu ruta hacia sus ofertas.
        </p>
      </div>

      {loading && <p className="text-sm text-ink-500">Cargando...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}
      {cargandoEmpresas && (
        <p className="text-sm text-ink-500">Cargando empresas disponibles...</p>
      )}
      {errorEmpresas && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          <span>No se pudo cargar el catálogo; no es posible añadir empresas por ahora.</span>
          <button
            type="button"
            onClick={recargarEmpresas}
            className="font-semibold underline"
          >
            Reintentar
          </button>
        </div>
      )}
      {!cargandoEmpresas && !errorEmpresas && empresas?.length === 0 && (
        <p className="text-sm text-ink-500">
          No hay empresas disponibles en el catálogo.
        </p>
      )}
      {!loading && !errorCarga && actuales.length === 0 && (
        <p className="text-sm text-ink-500">
          Aún no has añadido ninguna empresa.
        </p>
      )}

      <ul className="space-y-2">
        {actuales.map((item) => (
          <FilaExperiencia
            key={item.id}
            item={item}
            userId={userId}
            onLista={setLista}
          />
        ))}
      </ul>

      {disponibles.length > 0 ? (
        <form
          onSubmit={agregar}
          className="space-y-3 border-t border-ink-100 pt-5"
        >
          <p className="text-sm font-medium text-ink-700">Añadir una empresa</p>
          <div className="grid gap-3 sm:grid-cols-3">
            <select
              required
              value={empresaId}
              onChange={(e) => setEmpresaId(e.target.value)}
              aria-label="Empresa"
              className={campo}
            >
              <option value="">Elegir empresa...</option>
              {disponibles.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>
            <input
              required
              maxLength={120}
              value={cargo}
              onChange={(e) => setCargo(e.target.value)}
              placeholder="Cargo"
              aria-label="Cargo de la nueva empresa"
              className={campo}
            />
            <input
              maxLength={80}
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              placeholder="Periodo (opcional)"
              aria-label="Periodo de la nueva empresa"
              className={campo}
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm text-ink-700">
              <input
                type="checkbox"
                checked={actual}
                onChange={(e) => setActual(e.target.checked)}
              />
              Trabajo actualmente aquí
            </label>
            <button
              type="submit"
              disabled={ocupado || !empresaId}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              {ocupado ? "Añadiendo..." : "Añadir"}
            </button>
          </div>
        </form>
      ) : (
        empresas?.length > 0 && (
          <p className="border-t border-ink-100 pt-5 text-sm text-ink-500">
            Ya añadiste todas las empresas disponibles.
          </p>
        )
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}
    </section>
  );
}
