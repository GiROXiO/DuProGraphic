import json
import time

import streamlit as st

from backend_core.auth import (
    ROL_ADMIN,
    ROL_EMPRESA,
    ROL_USUARIO,
    asegurar_admin_inicial,
    autenticar,
    crear_sesion_persistente,
    registrar_cuenta,
    restaurar_sesion_persistente,
    revocar_sesion_persistente,
    segundos_bloqueo_login,
    url_http_valida,
)


ROLES = {
    ROL_USUARIO: ("Usuario", "Perfil profesional, habilidades, conexiones y postulaciones."),
    ROL_EMPRESA: ("Empresa / reclutador", "Perfil de empresa, ofertas y postulaciones recibidas."),
    ROL_ADMIN: ("Administrador", "Gestion completa de datos, relaciones y analitica."),
}
COOKIE_SESION = "duprographic_session"


@st.cache_data(ttl=30, show_spinner=False)
def _preparar_admin():
    return asegurar_admin_inicial()


def _seleccionar_rol(rol):
    st.session_state["rol_entrada"] = rol


def _activar_sesion(cuenta, mantener=True):
    st.session_state["cuenta_autenticada"] = cuenta
    st.session_state["pagina_activa"] = "Inicio"
    st.session_state.pop("rol_entrada", None)
    st.session_state.pop("aviso_sesion_persistente", None)
    if mantener:
        sesion = crear_sesion_persistente(cuenta)
        if sesion:
            st.session_state["_token_sesion_persistente"] = sesion["token"]
            st.session_state["_expira_sesion_persistente"] = sesion["expira_epoch"]
        else:
            st.session_state["aviso_sesion_persistente"] = (
                "Entraste correctamente, pero no se pudo guardar la sesión en este dispositivo."
            )
            st.session_state["_borrar_cookie_sesion"] = True
    else:
        st.session_state.pop("_token_sesion_persistente", None)
        st.session_state.pop("_expira_sesion_persistente", None)
        st.session_state["_borrar_cookie_sesion"] = True
    st.rerun()


def restaurar_sesion_desde_cookie():
    """Recupera el acceso tras recargar la página usando un token opaco."""
    if st.session_state.get("cuenta_autenticada"):
        return
    try:
        token = st.context.cookies.get(COOKIE_SESION, "")
    except Exception:
        token = ""
    if not token:
        return

    estado, cuenta = restaurar_sesion_persistente(token)
    if estado == "ok" and cuenta:
        st.session_state["cuenta_autenticada"] = {
            clave: valor for clave, valor in cuenta.items() if clave != "expira_epoch"
        }
        st.session_state["_token_sesion_persistente"] = token
        st.session_state["_expira_sesion_persistente"] = cuenta["expira_epoch"]
    elif estado == "invalida":
        st.session_state["_borrar_cookie_sesion"] = True
    else:
        st.session_state["aviso_sesion_persistente"] = (
            "No se pudo restaurar la sesión porque Neo4j no respondió. Vuelve a cargar la página cuando haya conexión."
        )


def sincronizar_cookie_sesion():
    """Escribe o elimina la cookie desde el navegador; nunca contiene la contraseña."""
    token = st.session_state.get("_token_sesion_persistente")
    expira = st.session_state.get("_expira_sesion_persistente")
    if token and expira:
        max_age = max(0, int(expira) - int(time.time()))
        if max_age <= 0:
            st.session_state["_borrar_cookie_sesion"] = True
        else:
            nombre_js = json.dumps(COOKIE_SESION)
            token_js = json.dumps(token)
            st.html(
                f"""<script>
                (() => {{
                  const secure = window.location.protocol === "https:" ? "; Secure" : "";
                  document.cookie = {nombre_js} + "=" + encodeURIComponent({token_js}) +
                    "; Max-Age={max_age}; Path=/; SameSite=Lax" + secure;
                }})();
                </script>""",
                unsafe_allow_javascript=True,
            )
            return

    if st.session_state.pop("_borrar_cookie_sesion", False):
        nombre_js = json.dumps(COOKIE_SESION)
        st.html(
            f"""<script>
            (() => {{
              const secure = window.location.protocol === "https:" ? "; Secure" : "";
              document.cookie = {nombre_js} + "=; Max-Age=0; Path=/; SameSite=Lax" + secure;
            }})();
            </script>""",
            unsafe_allow_javascript=True,
        )


def limpiar_claves_credenciales():
    """Limpia contraseñas despues del rerun que confirma el acceso."""
    for clave in list(st.session_state.keys()):
        if clave.startswith(("login_password_", "registro_password_", "registro_confirmacion_")):
            st.session_state.pop(clave, None)


def cerrar_sesion():
    token = st.session_state.get("_token_sesion_persistente")
    if token:
        revocar_sesion_persistente(token)
    st.session_state.clear()
    st.session_state["_borrar_cookie_sesion"] = True
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
            st.warning("Revisa ADMIN_EMAIL y usa una contraseña de 10 a 256 caracteres en .env.")
        elif estado_admin == "correo_en_uso":
            st.warning("El correo configurado para administrador ya pertenece a otro rol.")
        elif estado_admin == "error_bd":
            st.error("No se pudo preparar el acceso de administrador. Revisa la conexión con Neo4j Aura.")
        elif estado_admin == "admin_inactivo_password_distinta":
            st.error("La cuenta de administrador configurada está desactivada. ADMIN_PASSWORD debe coincidir con su contraseña actual para reactivarla.")
        elif estado_admin == "admin_reactivado":
            st.info("Se reactivó la cuenta de administrador configurada. Inicia sesión con sus credenciales habituales.")

    pestañas = st.tabs(["Iniciar sesión"] if rol == ROL_ADMIN else ["Iniciar sesión", "Crear cuenta"])
    with pestañas[0]:
        with st.form(f"form_login_{rol}", clear_on_submit=True):
            correo = st.text_input("Correo", max_chars=254, key=f"login_correo_{rol}")
            password = st.text_input("Contraseña", type="password", max_chars=256, key=f"login_password_{rol}")
            mantener_sesion = st.checkbox(
                "Mantener la sesión iniciada por 14 días",
                value=True,
                key=f"mantener_sesion_{rol}",
            )
            entrar = st.form_submit_button("Entrar", width="stretch")
        if entrar:
            cuenta = autenticar(correo, password, rol)
            if cuenta:
                _activar_sesion(cuenta, mantener=mantener_sesion)
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
                    max_chars=140,
                    key=f"registro_nombre_{rol}",
                )
                correo = st.text_input("Correo", max_chars=254, key=f"registro_correo_{rol}")
                if rol == ROL_USUARIO:
                    perfil_profesional = st.text_input(
                        "Titular profesional", key=f"registro_perfil_{rol}",
                        max_chars=180,
                        placeholder="Ej. Analista de datos | Python y Neo4j",
                    )
                    acerca_de = st.text_area(
                        "Presentación breve", key=f"registro_acerca_{rol}", max_chars=1200,
                        placeholder="Resume tu experiencia, fortalezas y qué oportunidades buscas.",
                    )
                    col_a, col_b = st.columns(2)
                    universidad = col_a.text_input("Universidad o institución", max_chars=160, key=f"registro_universidad_{rol}")
                    ubicacion = col_b.text_input("Ciudad o región", max_chars=120, key=f"registro_ubicacion_{rol}")
                    col_c, col_d = st.columns(2)
                    educacion_detalle = col_c.text_input("Programa o formación", max_chars=160, key=f"registro_educacion_{rol}")
                    areas_interes = col_d.text_input("Áreas de interés", max_chars=180, key=f"registro_intereses_{rol}", placeholder="Ej. Desarrollo, educación, energía")
                    col_e, col_f = st.columns(2)
                    anios_experiencia = col_e.number_input("Años de experiencia", min_value=0, max_value=50, value=0, step=1, key=f"registro_anios_{rol}")
                    modalidad_preferida = col_f.selectbox("Modalidad preferida", ["Sin preferencia", "remoto", "híbrido", "presencial"], key=f"registro_modalidad_{rol}")
                    experiencia = st.text_area("Experiencia u objetivos profesionales", key=f"registro_experiencia_{rol}", max_chars=900)
                    col_g, col_h = st.columns(2)
                    logros = col_g.text_area("Logros destacados (opcional)", key=f"registro_logros_{rol}", max_chars=600)
                    idiomas = col_h.text_input("Idiomas", max_chars=180, key=f"registro_idiomas_{rol}", placeholder="Ej. Español, inglés B2")
                    sitio_portafolio = st.text_input("Portafolio (opcional)", max_chars=240, key=f"registro_portafolio_{rol}", placeholder="https://...")
                    sector = ""
                    descripcion_empresa = ""
                    ubicacion_empresa = ""
                    sitio_empresa = ""
                else:
                    col_a, col_b = st.columns(2)
                    sector = col_a.text_input("Sector", max_chars=120, key=f"registro_sector_{rol}")
                    ubicacion_empresa = col_b.text_input("Ciudad o región", max_chars=120, key=f"registro_ubicacion_empresa_{rol}")
                    descripcion_empresa = st.text_area(
                        "Descripción de la organización", key=f"registro_descripcion_empresa_{rol}",
                        max_chars=1200, placeholder="Qué hace la empresa y qué tipo de talento busca.",
                    )
                    sitio_empresa = st.text_input("Sitio web", max_chars=240, key=f"registro_sitio_empresa_{rol}", placeholder="https://...")
                    perfil_profesional = ""
                    universidad = ""
                    ubicacion = ""
                    acerca_de = ""
                    educacion_detalle = ""
                    areas_interes = ""
                    experiencia = ""
                    logros = ""
                    idiomas = ""
                    sitio_portafolio = ""
                    anios_experiencia = 0
                    modalidad_preferida = "Sin preferencia"
                codigo_activacion = st.text_input(
                    "Codigo de activacion del perfil (si aplica)",
                    key=f"registro_codigo_{rol}",
                )
                password = st.text_input(
                    "Contraseña (10 a 256 caracteres)", max_chars=256,
                    type="password",
                    key=f"registro_password_{rol}",
                )
                confirmacion = st.text_input(
                    "Confirma la contraseña",
                    type="password",
                    max_chars=256,
                    key=f"registro_confirmacion_{rol}",
                )
                crear = st.form_submit_button("Crear cuenta", width="stretch")

            if crear:
                if password != confirmacion:
                    st.warning("Las contraseñas no coinciden.")
                elif not nombre.strip():
                    st.warning("Escribe el nombre del perfil.")
                elif rol == ROL_USUARIO and not perfil_profesional.strip():
                    st.warning("Escribe un titular profesional para presentar tu perfil.")
                elif rol == ROL_EMPRESA and not sector.strip():
                    st.warning("Escribe el sector de la empresa.")
                elif not url_http_valida(sitio_portafolio):
                    st.warning("Escribe un enlace completo que comience con http:// o https:// y tenga un dominio válido.")
                elif not url_http_valida(sitio_empresa):
                    st.warning("Escribe un enlace completo que comience con http:// o https:// y tenga un dominio válido.")
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
                            "ubicacion": ubicacion if rol == ROL_USUARIO else ubicacion_empresa,
                            "acerca_de": acerca_de,
                            "educacion_detalle": educacion_detalle,
                            "areas_interes": areas_interes,
                            "experiencia": experiencia,
                            "logros": logros,
                            "idiomas": idiomas,
                            "sitio_portafolio": sitio_portafolio,
                            "anios_experiencia": anios_experiencia,
                            "modalidad_preferida": "" if modalidad_preferida == "Sin preferencia" else modalidad_preferida,
                            "descripcion": descripcion_empresa,
                            "sitio_web": sitio_empresa,
                        },
                        codigo_activacion=codigo_activacion,
                    )
                    if estado in {"creada", "creada_perfil_existente"}:
                        if estado == "creada_perfil_existente":
                            st.success("Cuenta creada y vinculada a tu perfil existente.")
                        else:
                            st.success("Cuenta creada. Ya puedes entrar.")
                        _activar_sesion(cuenta, mantener=True)
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
                    elif estado == "password_largo":
                        st.warning("La contraseña no puede superar 256 caracteres.")
                    elif estado == "nombre_vacio":
                        st.warning("Escribe el nombre del perfil.")
                    elif estado == "perfil_incompleto":
                        st.warning("Completa el titular profesional o sector del perfil.")
                    elif estado == "datos_invalidos":
                        st.warning("Revisa los campos: hay un valor demasiado largo o fuera de las opciones permitidas.")
                    elif estado == "url_invalida":
                        st.warning("El enlace debe ser una dirección web completa que comience con http:// o https://.")
                    elif estado == "rol_no_permitido":
                        st.error("Ese tipo de cuenta no se puede registrar desde esta pantalla.")
                    else:
                        st.error("No se pudo crear la cuenta. Revisa la conexión con Neo4j Aura.")
