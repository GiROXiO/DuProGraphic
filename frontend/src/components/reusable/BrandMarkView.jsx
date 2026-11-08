// Logo de DuProGraphic: tres nodos conectados.
export default function BrandMarkView({ className = "h-9 w-9" }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="#7c5cff" />
      <g stroke="#fff" strokeWidth="1.6" strokeLinecap="round" opacity="0.85">
        <line x1="9" y1="21" x2="16" y2="10" />
        <line x1="16" y1="10" x2="23" y2="21" />
        <line x1="9" y1="21" x2="23" y2="21" />
      </g>
      <circle cx="9" cy="21" r="3" fill="#fff" />
      <circle cx="16" cy="10" r="3" fill="#2be0b0" />
      <circle cx="23" cy="21" r="3" fill="#fff" />
    </svg>
  );
}
