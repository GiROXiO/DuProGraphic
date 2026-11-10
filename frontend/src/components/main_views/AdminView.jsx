import { useState } from "react";
import ShellView from "../nav_layout/ShellView";
import AdminUsersView from "../reusable/AdminUsersView";
import AdminCompaniesView from "../reusable/AdminCompaniesView";
import AdminOffersView from "../reusable/AdminOffersView";
import AdminProjectsView from "../reusable/AdminProjectsView";
import { getUser } from "../../api";

const PESTANAS = [
  { id: "usuarios", label: "Usuarios", Panel: AdminUsersView },
  { id: "empresas", label: "Empresas", Panel: AdminCompaniesView },
  { id: "ofertas", label: "Ofertas", Panel: AdminOffersView },
  { id: "proyectos", label: "Proyectos", Panel: AdminProjectsView },
];

export default function AdminView() {
  const user = getUser();
  const [activa, setActiva] = useState("usuarios");
  const { Panel } = PESTANAS.find((p) => p.id === activa);

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Administración
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Crea, edita y elimina usuarios, empresas, ofertas y proyectos, y
          decide quién es administrador.
        </p>
      </header>

      {user?.rol !== "administrador" ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          Esta sección es solo para administradores.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex gap-1 border-b border-ink-100" role="tablist">
            {PESTANAS.map((p) => (
              <button
                key={p.id}
                role="tab"
                aria-selected={activa === p.id}
                onClick={() => setActiva(p.id)}
                className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition ${
                  activa === p.id
                    ? "border-brand-600 text-brand-700"
                    : "border-transparent text-ink-500 hover:text-ink-900"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <Panel key={activa} />
        </div>
      )}
    </ShellView>
  );
}
