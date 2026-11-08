import AffinityRingView from "./AffinityRingView";
import SkillBadgeView from "./SkillBadgeView";
import PostularButtonView from "./PostularButtonView";

export default function JobCardView({ oferta, onPostulada }) {
  const meta = [oferta.modalidad, oferta.experiencia].filter(Boolean);
  const saltos = oferta.distancia;

  return (
    <article className="flex gap-4 rounded-2xl border border-ink-100 bg-white p-5 transition hover:border-brand-500/50 hover:shadow-md">
      <AffinityRingView value={oferta.afinidad} />

      <div className="min-w-0 flex-1">
        <h3 className="font-semibold leading-snug text-ink-900">
          {oferta.titulo}
        </h3>
        <p className="mt-0.5 text-sm text-ink-500">
          {oferta.empresa}
          {oferta.sector ? ` · ${oferta.sector}` : ""}
        </p>

        {meta.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {meta.map((m, i) => (
              <span
                key={`${m}-${i}`}
                className="rounded-md bg-ink-100 px-2 py-0.5 text-xs capitalize text-ink-700"
              >
                {m}
              </span>
            ))}
          </div>
        )}

        {oferta.habilidades?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {oferta.habilidades.map((h) => (
              <SkillBadgeView key={h} nombre={h} />
            ))}
          </div>
        )}

        <p className="mt-3 text-xs text-ink-500">
          {saltos != null
            ? `A ${saltos} ${saltos === 1 ? "salto" : "saltos"} de tu red`
            : "Fuera de tu red cercana"}
          {oferta.contactos > 0 &&
            ` · ${oferta.contactos} ${
              oferta.contactos === 1
                ? "contacto ya postuló"
                : "contactos ya postularon"
            }`}
        </p>

        <div className="mt-4">
          <PostularButtonView ofertaId={oferta.id} onPostulada={onPostulada} />
        </div>
      </div>
    </article>
  );
}
