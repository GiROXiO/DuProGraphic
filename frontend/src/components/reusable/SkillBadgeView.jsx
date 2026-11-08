export default function SkillBadgeView({ nombre }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md bg-signal-50 px-2.5 py-1 text-xs font-medium text-signal-600">
      <span className="h-1.5 w-1.5 rounded-full bg-signal-600" />
      {nombre}
    </span>
  );
}
