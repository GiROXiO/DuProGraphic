import streamlit as st

from backend_core.auth import (
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    asegurar_admin_inicial,
    autenticar,
    registrar_cuenta,
    segundos_bloqueo_login,
)


ROLES = {
    ROL_USUARIO: ("Usuario", "Perfil profesional, habilidades, conexiones y postulaciones."),
    ROL_EMPRESA: ("Empresa / reclutador", "Perfil de empresa, ofertas y postulaciones recibidas."),
    ROL_ADMIN: ("Administrador", "Gestion completa de datos, relaciones y analitica."),
}


@st.cache_data(ttl=30, show_spinner=False)
def _preparar_admin():
    return asegurar_admin_inicial()


def _seleccionar_rol(rol):
    st.session_state["rol_entrada"] = rol


def _activar_sesion(cuenta):
    st.session_state["cuenta_autenticada"] = cuenta
    st.session_state["pagina_activa"] = "Inicio"
    st.session_state.pop("rol_entrada", None)
    st.rerun()


def limpiar_claves_credenciales():
    """Limpia contraseñas despues del rerun que confirma el acceso."""
    for clave in list(st.session_state.keys()):
        if clave.startswith(("login_password_", "registro_password_", "registro_confirmacion_")):
            st.session_state.pop(clave, None)


def cerrar_sesion():
    st.session_state.clear()
    st.rerun()


def renderizar_acceso():
    estado_admin = _preparar_admin()
    st.markdown(
        """
        <section class="home-hero">
          <h1>DuProGraphic</h1>
          <p>Entra a tu espacio de la red profesional o crea una cuenta.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    rol = st.session_state.get("rol_entrada")
    if rol not in ROLES:
        st.subheader("Elige cómo quieres entrar")
        columnas = st.columns(3, gap="medium")
        for columna, (clave, (nombre, descripcion)) in zip(columnas, ROLES.items()):
            with columna:
                st.markdown(
                    f'<div class="feature-card"><h3>{nombre}</h3><p>{descripcion}</p></div>',
                    unsafe_allow_html=True,
                )
                st.button(
                    f"Continuar como {nombre}",
                    key=f"elegir_rol_{clave}",
                    width="stretch",
                    on_click=_seleccionar_rol,
                    args=(clave,),
                )
        st.caption("El administrador no puede crear una cuenta desde el registro publico.")
        return

    nombre_rol, _ = ROLES[rol]
    if st.button("Cambiar tipo de acceso", key="cambiar_rol_entrada"):
        st.session_state.pop("rol_entrada", None)
        st.rerun()

    st.subheader(f"Acceso: {nombre_rol}")
    if rol == ROL_ADMIN:
        if estado_admin == "sin_configurar":
            st.warning(
                "El administrador inicial se configura en el archivo .env con "
                "ADMIN_EMAIL y ADMIN_PASSWORD. No hay registro publico para este rol."
            )
        elif estado_admin == "configuracion_invalida":
            st.warning("Revisa ADMIN_EMAIL y usa una contraseña de al menos 10 caracteres en .env.")
        elif estado_admin == "correo_en_uso":
            st.warning("El correo configurado para administrador ya pertenece a otro rol.")
        elif estado_admin == "error_bd":
            st.error("No se pudo preparar el acceso de administrador. Revisa la conexión con Neo4j Aura.")

    pestañas = st.tabs(["Iniciar sesión"] if rol == ROL_ADMIN else ["Iniciar sesión", "Crear cuenta"])
    with pestañas[0]:
        with st.form(f"form_login_{rol}", clear_on_submit=True):
            correo = st.text_input("Correo", key=f"login_correo_{rol}")
            password = st.text_input("Contraseña", type="password", key=f"login_password_{rol}")
            entrar = st.form_submit_button("Entrar", width="stretch")
        if entrar:
            cuenta = autenticar(correo, password, rol)
            if cuenta:
                _activar_sesion(cuenta)
            restante = segundos_bloqueo_login(correo)
            if restante:
                st.error(
                    f"Demasiados intentos. Espera {restante} segundos antes de volver a probar."
                )
            else:
                st.error("No se pudo iniciar sesión. Revisa el correo, la contraseña y el tipo de acceso.")

    if rol != ROL_ADMIN:
        with pestañas[1]:
            st.caption(
                "Si el correo ya pertenece a un perfil existente, pide al administrador un codigo "
                "de activacion para vincularlo sin crear un duplicado."
            )
            with st.form(f"form_registro_{rol}", clear_on_submit=True):
                nombre = st.text_input(
                    "Nombre completo" if rol == ROL_USUARIO else "Nombre de la empresa",
                    key=f"registro_nombre_{rol}",
                )
                correo = st.text_input("Correo", key=f"registro_correo_{rol}")
                if rol == ROL_USUARIO:
                    perfil_profesional = st.text_input(
                        "Perfil profesional", key=f"registro_perfil_{rol}"
                    )
                    universidad = st.text_input(
                        "Universidad o institucion", key=f"registro_universidad_{rol}"
                    )
                    sector = ""
                else:
                    sector = st.text_input("Sector", key=f"registro_sector_{rol}")
                    perfil_profesional = ""
                    universidad = ""
                codigo_activacion = st.text_input(
                    "Codigo de activacion del perfil (si aplica)",
                    key=f"registro_codigo_{rol}",
                )
                password = st.text_input(
                    "Contraseña (mínimo 10 caracteres)",
                    type="password",
                    key=f"registro_password_{rol}",
                )
                confirmacion = st.text_input(
                    "Confirma la contraseña",
                    type="password",
                    key=f"registro_confirmacion_{rol}",
                )
                crear = st.form_submit_button("Crear cuenta", width="stretch")

            if crear:
                if password != confirmacion:
                    st.warning("Las contraseñas no coinciden.")
                elif not nombre.strip():
                    st.warning("Escribe el nombre del perfil.")
                else:
                    estado, cuenta = registrar_cuenta(
                        rol,
                        correo,
                        password,
                        {
                            "nombre": nombre,
                            "perfil_profesional": perfil_profesional,
                            "universidad": universidad,
                            "sector": sector,
                        },
                        codigo_activacion=codigo_activacion,
                    )
                    if estado in {"creada", "creada_perfil_existente"}:
                        if estado == "creada_perfil_existente":
                            st.success("Cuenta creada y vinculada a tu perfil existente.")
                        else:
                            st.success("Cuenta creada. Ya puedes entrar.")
                        _activar_sesion(cuenta)
                    elif estado == "correo_existente":
                        st.warning("Ya existe una cuenta con ese correo.")
                    elif estado == "perfil_ya_vinculado":
                        st.warning("Ese perfil ya tiene una cuenta asociada. Inicia sesión con su correo.")
                    elif estado == "correo_perfil_usuario":
                        st.warning(
                            "Ese correo ya pertenece a un perfil de usuario. "
                            "Solicita un código de activación y reclama ese perfil."
                        )
                    elif estado == "correo_perfil_empresa":
                        st.warning(
                            "Ese correo ya pertenece a un perfil de empresa. "
                            "Solicita un código de activación y reclama ese perfil."
                        )
                    elif estado == "correo_perfil_existente":
                        st.warning("Ese correo ya está asociado a un perfil existente.")
                    elif estado == "id_existente":
                        st.warning("Ya existe un perfil con ese ID.")
                    elif estado == "id_invalido":
                        st.warning("El ID debe empezar con U para usuarios o E para empresas.")
                    elif estado == "datos_incompletos":
                        st.warning("Completa el ID y el nombre del perfil.")
                    elif estado == "codigo_requerido":
                        st.warning("Ese perfil requiere un codigo de activacion del administrador.")
                    elif estado == "correo_invalido":
                        st.warning("Escribe un correo válido.")
                    elif estado == "password_corto":
                        st.warning("La contraseña debe tener al menos 10 caracteres.")
                    elif estado == "nombre_vacio":
                        st.warning("Escribe el nombre del perfil.")
                    elif estado == "rol_no_permitido":
                        st.error("Ese tipo de cuenta no se puede registrar desde esta pantalla.")
                    else:
                        st.error("No se pudo crear la cuenta. Revisa la conexión con Neo4j Aura.")
