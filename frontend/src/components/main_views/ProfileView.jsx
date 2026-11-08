import ShellView from "../nav_layout/ShellView";
import ProfileFormView from "../reusable/ProfileFormView";
import SkillsEditorView from "../reusable/SkillsEditorView";
import { getUser } from "../../api";
import useFetch from "../../useFetch";

export default function ProfileView() {
  const user = getUser();
  const esUsuario = user?.rol === "usuario" && user?.entidad_id;

  const {
    data: perfil,
    loading,
    error,
  } = useFetch(esUsuario ? `/api/users/${user.entidad_id}/profile` : null);

  return (
    <ShellView>
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Mi perfil
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Edita tu información y tus habilidades. Solo tú puedes modificarlas.
        </p>
      </header>

      {!esUsuario ? (
        <div className="rounded-2xl border border-ink-100 bg-white p-8 text-center text-ink-500">
          La edición de perfil de {user?.rol} se habilitará en la siguiente
          fase.
        </div>
      ) : (
        <div className="space-y-8">
          {loading && <p className="text-ink-500">Cargando tu perfil...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {perfil && (
            <ProfileFormView perfil={perfil} userId={user.entidad_id} />
          )}
          <SkillsEditorView userId={user.entidad_id} />
        </div>
      )}
    </ShellView>
  );
}
