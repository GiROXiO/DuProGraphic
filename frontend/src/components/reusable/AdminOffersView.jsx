import { useState } from "react";
import { Plus } from "lucide-react";
import api from "../../api";
import useFetch from "../../useFetch";
import { mensajeError } from "../../formErrors";
import OfferFormView from "./OfferFormView";
import BorrarConfirmadoView from "./BorrarConfirmadoView";

const campo =
  "w-full rounded-xl border border-ink-100 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

export default function AdminOffersView() {
  const { data, loading, error: errorCarga } = useFetch("/api/admin/offers");
  const { data: empresas } = useFetch("/api/lookups/companies");
  const [lista, setLista] = useState(null);
  // null | { empresaId, oferta: null (nueva) o el detalle de la oferta }
  const [formulario, setFormulario] = useState(null);
  const [eligiendo, setEligiendo] = useState(false);
  const [empresaNueva, setEmpresaNueva] = useState("");
  const [error, setError] = useState("");

  const ofertas = lista ?? data ?? [];

  const recargar = async () => {
    try {
      const res = await api.get("/api/admin/offers");
      setLista(res.data.data);
    } catch {
      /* la lista anterior sigue siendo válida */
    }
  };

  const editar = async (o) => {
    setError("");
    try {
      // El detalle completo (habilidades requeridas) viene del endpoint de la empresa.
      const res = await api.get(`/api/companies/${o.empresa_id}/offers`);
      const detalle = res.data.data.find((x) => x.id === o.id);
      if (!detalle) {
        setError("La oferta ya no existe.");
        recargar();
        return;
      }
      setEligiendo(false);
      setFormulario({ empresaId: o.empresa_id, oferta: detalle });
    } catch (err) {
      setError(mensajeError(err, {}, "No se pudo abrir la oferta"));
    }
  };

  const eliminar = async (o) => {
    setError("");
    try {
      const res = await api.delete(`/api/admin/offers/${o.id}`);
      setLista(res.data.data);
      if (formulario?.oferta?.id === o.id) setFormulario(null);
    } catch (err) {
      setError(mensajeError(err, {}, "No se pudo eliminar la oferta"));
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-500">
          {ofertas.length} ofertas. Eliminar una borra también sus
          postulaciones.
        </p>
        {!eligiendo && !formulario && (
          <button
            onClick={() => setEligiendo(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Nueva oferta
          </button>
        )}
      </div>

      {eligiendo && (
        <div className="flex flex-wrap items-end gap-3 rounded-2xl border border-brand-100 bg-white p-5 shadow-sm">
          <div className="min-w-60 flex-1">
            <label
              htmlFor="of-empresa"
              className="mb-1.5 block text-sm font-medium text-ink-700"
            >
              ¿En nombre de qué empresa?
            </label>
            <select
              id="of-empresa"
              value={empresaNueva}
              onChange={(e) => setEmpresaNueva(e.target.value)}
              className={campo}
            >
              <option value="">Elegir empresa...</option>
              {(empresas ?? []).map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </div>
          <button
            disabled={!empresaNueva}
            onClick={() => {
              setFormulario({ empresaId: empresaNueva, oferta: null });
              setEligiendo(false);
            }}
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            Continuar
          </button>
          <button
            onClick={() => setEligiendo(false)}
            className="rounded-xl border border-ink-100 px-5 py-2.5 text-sm font-semibold text-ink-700 transition hover:bg-ink-100"
          >
            Cancelar
          </button>
        </div>
      )}

      {formulario && (
        <OfferFormView
          key={formulario.oferta?.id ?? `nueva-${formulario.empresaId}`}
          companyId={formulario.empresaId}
          oferta={formulario.oferta}
          onGuardada={() => {
            setFormulario(null);
            recargar();
          }}
          onCancelar={() => setFormulario(null)}
        />
      )}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}
      {loading && <p className="text-sm text-ink-500">Cargando ofertas...</p>}
      {errorCarga && <p className="text-sm text-red-600">{errorCarga}</p>}

      <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-ink-100/60 text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th className="px-4 py-2.5 font-semibold">Oferta</th>
              <th className="px-4 py-2.5 font-semibold">Empresa</th>
              <th className="px-4 py-2.5 font-semibold">Estado</th>
              <th className="px-4 py-2.5 font-semibold">Postulaciones</th>
              <th className="px-4 py-2.5 font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {ofertas.map((o) => {
              const abierta = o.estado?.toLowerCase() === "abierta";
              return (
                <tr key={o.id} className="align-middle">
                  <td className="px-4 py-2.5">
                    <p className="font-medium text-ink-900">{o.titulo}</p>
                    <p className="text-xs capitalize text-ink-500">
                      {[o.modalidad, o.nivel].filter(Boolean).join(" · ")}
                    </p>
                  </td>
                  <td className="px-4 py-2.5 text-ink-700">{o.empresa}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-md px-2 py-0.5 text-xs font-semibold ${abierta ? "bg-signal-50 text-signal-600" : "bg-ink-100 text-ink-500"}`}
                    >
                      {abierta ? "Abierta" : "Cerrada"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-ink-700">
                    {o.postulaciones}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => editar(o)}
                        className="rounded-lg border border-ink-100 px-3 py-1.5 text-xs font-semibold text-ink-700 transition hover:bg-ink-100"
                      >
                        Editar
                      </button>
                      <BorrarConfirmadoView onConfirmar={() => eliminar(o)} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
