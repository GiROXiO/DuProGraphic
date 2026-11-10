import NavbarView from "./NavbarView";

// Estructura común de las pantallas internas: navegación lateral + contenido.
export default function ShellView({ children }) {
  return (
    <div className="min-h-screen">
      <NavbarView />
      <main className="pt-14 md:pl-64 md:pt-0">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-8">{children}</div>
      </main>
    </div>
  );
}
