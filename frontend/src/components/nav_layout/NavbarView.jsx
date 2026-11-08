import { NavLink, useNavigate } from "react-router-dom";
import api, { clearSession, getUser } from "../../api";
import BrandMarkView from "../reusable/BrandMarkView";
import {
  Compass,
  Briefcase,
  User,
  Users,
  Network,
  MessageSquare,
  LogOut,
} from "lucide-react";

// to: null = sección que todavía no existe
const ITEMS = [
  { to: "/", label: "Inicio", icon: Compass, end: true },
  { to: "/jobs", label: "Oportunidades", icon: Briefcase },
  { to: "/profile", label: "Mi perfil", icon: User },
  { to: "/analytics", label: "Análisis", icon: Network },
  { to: "/network", label: "Mi red", icon: Users },
  { to: null, label: "Mensajes", icon: MessageSquare },
];

const base =
  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors";

export default function NavbarView() {
  const navigate = useNavigate();
  const user = getUser();

  const handleLogout = async () => {
    try {
      // Revoca el token en el backend; si falla igual cerramos localmente.
      await api.post("/api/auth/logout");
    } catch {
      // sin conexión o token ya vencido: no importa
    }
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-3 bg-ink-950 px-4 text-white md:inset-y-0 md:right-auto md:h-auto md:w-64 md:flex-col md:items-stretch md:gap-0 md:px-5 md:py-6">
      <div className="flex items-center gap-3">
        <BrandMarkView />
        <span className="hidden text-lg font-bold tracking-tight sm:inline">
          DuProGraphic
        </span>
      </div>

      <nav className="ml-auto flex items-center gap-1 md:ml-0 md:mt-10 md:flex-1 md:flex-col md:items-stretch">
        {ITEMS.map(({ to, label, icon: Icon, end }) =>
          to ? (
            <NavLink
              key={label}
              to={to}
              end={end}
              className={({ isActive }) =>
                `${base} ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-ink-300 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span className="hidden md:inline">{label}</span>
            </NavLink>
          ) : (
            <div
              key={label}
              title="Disponible pronto"
              className={`${base} cursor-not-allowed text-ink-500`}
            >
              <Icon className="h-5 w-5" />
              <span className="hidden md:inline">{label}</span>
              <span className="ml-auto hidden rounded bg-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide md:inline">
                Pronto
              </span>
            </div>
          ),
        )}
      </nav>

      <div className="flex items-center gap-3 md:border-t md:border-white/10 md:pt-4">
        {user && (
          <div className="hidden min-w-0 flex-1 items-center gap-3 md:flex">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500 text-sm font-bold">
              {user.nombre?.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user.nombre}</p>
              <p className="text-xs capitalize text-ink-300">{user.rol}</p>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          title="Cerrar sesión"
          className="rounded-xl p-2 text-ink-300 transition-colors hover:bg-white/10 hover:text-white"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </aside>
  );
}
