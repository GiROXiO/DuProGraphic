from html import escape

import streamlit as st

from analytics_dashboard import analytics_ui
from backend_core import accounts_ui, crud_ui
from backend_core import auth_ui, role_ui
from backend_core.auth import validar_sesion


st.set_page_config(
    page_title="Duprographic | Red profesional",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


ESTILOS = """
<style>
:root {
    --ink: #1f2328;
    --muted: #59636e;
    --line: #d0d7de;
    --surface: #ffffff;
    --canvas: #f3f2ef;
    --navy: #1f2937;
    --blue: #0a66c2;
}

.stApp { background: var(--canvas); color: var(--ink); font-family: Calibri, Arial, sans-serif; }
.block-container { max-width: 1360px; padding-top: 1.4rem; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #d0d7de;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #26384d; }
.brand-lockup { display: flex; align-items: center; gap: 10px; padding: 8px 2px 14px; }
.brand-symbol {
    display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid #0a66c2;
    border-radius: 6px; color: white; font-family: Calibri, Arial, sans-serif;
    font-size: 21px; font-weight: 700; background: #0a66c2;
}
.brand-name { color: #1f2328; font-family: Calibri, Arial, sans-serif; font-size: 18px; font-weight: 700; }
.brand-subtitle { color: #59636e; font-size: 11px; }
.sidebar-profile { display: flex; align-items: center; gap: 10px; padding: 11px; margin: 2px 0 16px; border: 1px solid #d0d7de; background: #f6f8fa; border-radius: 8px; min-width: 0; }
.sidebar-avatar { display: grid; place-items: center; flex: 0 0 38px; height: 38px; border-radius: 50%; background: #d9eaf7; color: #0a4b78; font-size: 15px; font-weight: 700; }
.sidebar-account { color: #1f2328; font-size: 13px; line-height: 1.25; font-weight: 700; overflow-wrap: anywhere; }
.sidebar-role { color: #59636e; font-size: 11px; margin-top: 3px; }
.nav-group-label { color: #697582; font-size: 10px; font-weight: 700; letter-spacing: .06em; padding: 12px 8px 3px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 7px 9px; margin: 2px 0; border-radius: 6px;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #edf3f8; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-color: #d0d7de; border-radius: 6px; }
.section-banner {
    padding: 16px 20px; margin-bottom: 18px; border: 1px solid var(--line);
    border-left: 4px solid var(--blue); border-radius: 8px; background: #ffffff;
}
.section-banner h1 { color: var(--ink); font-family: Calibri, Arial, sans-serif; font-size: 29px; line-height: 1.2; margin: 4px 0 6px; }
.section-banner p { color: var(--muted); margin: 0; font-size: 14px; }
.home-hero {
    padding: 25px 29px; border: 1px solid #d0d7de; border-top: 4px solid #0a66c2;
    border-radius: 8px; color: var(--ink); background: #ffffff;
}
.home-hero h1 { color: #20344d; max-width: 760px; font-family: Calibri, Arial, sans-serif; font-size: 32px; line-height: 1.2; margin: 0 0 8px; }
.home-hero p { color: #4c5d70; font-size: 15px; max-width: 760px; margin: 0; }
.social-hero {
    padding: 22px 25px; margin-bottom: 18px; border: 1px solid #d0d7de;
    border-top: 4px solid #0a66c2; border-radius: 8px; background: #ffffff;
}
.social-hero h1 { color: #1f2328; font-family: Calibri, Arial, sans-serif; font-size: 29px; line-height: 1.2; margin: 0 0 8px; }
.social-hero p { color: #59636e; font-size: 15px; max-width: 850px; margin: 0; }
.social-panel { padding: 15px 17px; border: 1px solid #d0d7de; background: #fff; border-radius: 8px; }
.profile-banner { overflow: hidden; margin-bottom: 14px; border: 1px solid #d0d7de; background: #fff; border-radius: 8px; }
.profile-banner-cover { height: 70px; background: #dbe9f3; border-bottom: 1px solid #d0d7de; }
.profile-banner-body { display: flex; align-items: center; gap: 14px; padding: 0 20px 18px; }
.profile-avatar { display: grid; place-items: center; width: 66px; height: 66px; margin-top: -24px; flex: 0 0 66px; border: 3px solid #fff; border-radius: 50%; background: #0a66c2; color: #fff; font-size: 22px; font-weight: 700; }
.profile-banner-copy { padding-top: 8px; min-width: 0; }
.profile-name { color: #1f2328; font-size: 23px; line-height: 1.2; font-weight: 700; overflow-wrap: anywhere; }
.profile-headline { color: #303a44; font-size: 15px; margin-top: 3px; }
.profile-meta { color: #59636e; font-size: 13px; margin-top: 5px; }
.profile-meta span { padding: 0 4px; }
.profile-completion { border-left: 3px solid #0a66c2; padding-left: 12px; }
.feature-card {
    min-height: 138px; padding: 15px 17px; border: 1px solid #d0d7de;
    border-radius: 8px; background: var(--surface);
}
.feature-card h3 { color: var(--ink); font-family: Calibri, Arial, sans-serif; font-size: 17px; margin: 0 0 6px; }
.feature-card p { color: var(--muted); font-size: 13px; line-height: 1.45; margin: 0; }
h1, h2, h3, button, input, textarea, label { font-family: Calibri, Arial, sans-serif; }
h2, h3 { color: var(--ink); }
[data-testid="stHeaderActionElements"] { display: none !important; }
div[data-testid="stMetric"] {
    padding: 12px 15px; border: 1px solid var(--line); border-radius: 8px;
    background: white;
}
div[data-testid="stMetric"] label { color: var(--muted); }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
div[data-testid="stForm"] {
    padding: 15px 17px 10px; border: 1px solid var(--line); border-radius: 8px;
    background: #ffffff;
}
.stButton button, [data-testid="stFormSubmitButton"] button {
    min-height: 38px; border-radius: 6px; font-weight: 600;
    background: #0a66c2 !important; color: #ffffff !important;
    border: 1px solid #07549f !important;
}
.stButton button *, [data-testid="stFormSubmitButton"] button * { color: #ffffff !important; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    background: #07549f !important; border-color: #064781 !important;
}
.stButton button:disabled, [data-testid="stFormSubmitButton"] button:disabled {
    background: #d5dbe0 !important; color: #596775 !important;
    border-color: #aab4be !important;
}
.stButton button:disabled *, [data-testid="stFormSubmitButton"] button:disabled * {
    color: #596775 !important;
}
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #ffffff !important;
    color: #1f2328 !important;
    border: 1px solid #aab4be !important;
    border-radius: 4px !important;
}
[data-baseweb="select"] svg { fill: #344b63 !important; }
[role="listbox"], [role="option"] { background-color: #ffffff !important; color: #24364b !important; }
[role="option"]:hover { background-color: #e1e7ed !important; }
input::placeholder, textarea::placeholder { color: #647282 !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
    min-height: 34px; background: transparent !important; color: #303a44 !important;
    border-color: transparent !important; text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] * {
    color: #303a44 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    min-height: 34px; background: #e8f2fa !important; color: #0a4b78 !important;
    border-color: #d4e5f2 !important; text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * {
    color: #164b75 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #edf3f8 !important; border-color: #d0d7de !important;
}
.sidebar-rule { height: 1px; background: #d0d7de; margin: 13px 0 9px; }
.sidebar-footer { color: #697582; font-size: 11px; padding: 8px 3px 0; }

@media (max-width: 700px) {
    .block-container { padding: 1rem 1rem 1.8rem; }
    .home-hero { padding: 20px 17px; }
    .section-banner { padding: 15px 16px; }
}
</style>
"""


ESTILOS_OSCUROS = """
<style>
.stApp { background: #111820 !important; color: #e8eef4 !important; }
[data-testid="stSidebar"] { background: #18222c !important; border-right: 1px solid #34414e !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #e0e7ef !important; }
.brand-name { color: #eef3f7 !important; }
.brand-subtitle { color: #b4c0cc !important; }
.brand-symbol { background: #0a66c2 !important; border-color: #6b9bc6 !important; }
.sidebar-profile { background: #202b36 !important; border-color: #3a4856 !important; }
.sidebar-account { color: #e8eef4 !important; }
.sidebar-role, .nav-group-label { color: #aebbc7 !important; }
.sidebar-avatar { background: #244765 !important; color: #d9ecfb !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] { color: #d9e1e8 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] * { color: #d9e1e8 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] { background: #233e54 !important; color: #eaf4fb !important; border-color: #4d7190 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * { color: #eaf4fb !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button:hover { background: #263847 !important; border-color: #465969 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-color: #3e4d5b !important; }
.section-banner { background: #1c2833 !important; border-color: #3a4856 !important; border-left-color: #79b8f3 !important; }
.home-hero { background: #1b2834 !important; border-color: #3a4856 !important; border-top-color: #79b8f3 !important; }
.social-hero, .social-panel, .profile-banner, div[data-testid="stForm"] { background: #1b2834 !important; border-color: #3a4856 !important; }
.profile-banner-cover { background: #203e57 !important; border-color: #3a4856 !important; }
.profile-avatar { background: #2b79b9 !important; border-color: #1b2834 !important; }
.profile-name, .profile-headline { color: #e8eef4 !important; }
.profile-meta { color: #b4c0cc !important; }
.profile-completion { border-left-color: #79b8f3 !important; }
.home-hero h1, .home-hero p, .section-banner h1, .section-banner p, h1, h2, h3 { color: #e7edf4 !important; }
.social-hero h1, .social-hero p { color: #e8eef4 !important; }
.feature-card, div[data-testid="stMetric"] {
    background: #1b2834 !important; border-color: #3a4856 !important;
}
.feature-card h3, .feature-card p, div[data-testid="stMetric"] label { color: #c7d2dc !important; }
div[data-testid="stDataFrame"] { border-color: #3a4856 !important; }
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #17212a !important; color: #edf2f7 !important; border-color: #536372 !important;
}
[data-baseweb="select"] svg { fill: #d7e0e9 !important; }
[role="listbox"], [role="option"] { background-color: #1b2834 !important; color: #edf2f7 !important; }
[role="option"]:hover { background-color: #2a3b4a !important; }
input::placeholder, textarea::placeholder { color: #b4c0cd !important; }
.stButton button, [data-testid="stFormSubmitButton"] button {
    background: #365b80 !important; color: #ffffff !important; border-color: #7794b1 !important;
}
.stButton button *, [data-testid="stFormSubmitButton"] button * { color: #ffffff !important; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover { background: #456f97 !important; }
.stButton button:disabled, [data-testid="stFormSubmitButton"] button:disabled {
    background: #303b47 !important; color: #c1ccd8 !important; border-color: #596879 !important;
}
.stButton button:disabled *, [data-testid="stFormSubmitButton"] button:disabled * { color: #c1ccd8 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important; color: #d9e1e8 !important;
    border-color: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] *,
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * {
    color: #d9e1e8 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #233e54 !important; color: #eaf4fb !important;
    border-color: #4d7190 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #263847 !important; border-color: #465969 !important;
}
.sidebar-rule { background: #3a4856 !important; }
.sidebar-footer { color: #aebbc7 !important; }
</style>
"""


PAGINAS = {
    "Inicio": ("DuProGraphic", "Aplicación para gestionar y analizar una red profesional con Neo4j."),
    "Usuarios": ("Usuarios", "Administra perfiles y revisa las cuentas asociadas."),
    "Empresas": ("Empresas", "Consulta y administra perfiles de organizaciones."),
    "Ofertas": ("Ofertas", "Gestiona los registros de vacantes."),
    "Proyectos": ("Proyectos", "Gestiona los registros de proyectos."),
    "Recomendaciones": ("Recomendaciones", "Explora sugerencias calculadas sobre la red."),
    "Consultas": ("Consultas", "Consulta rutas y relaciones entre los elementos del grafo."),
    "Analítica": ("Analítica", "Revisa métricas, habilidades y comunidades de la red."),
}

ENTIDADES_ADMIN = {
    "Usuarios": "Usuarios",
    "Empresas": "Empresas",
    "Ofertas": "Ofertas",
    "Proyectos": "Proyectos",
}


def _encabezado(titulo, descripcion):
    st.markdown(
        f'<div class="section-banner"><h1>{titulo}</h1><p>{descripcion}</p></div>',
        unsafe_allow_html=True,
    )


def _tema_oscuro_activo():
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def _seleccionar_pagina(pagina):
    st.session_state["pagina_activa"] = pagina


def _grupos_menu(rol):
    """Ordena el menú en grupos que siguen el trabajo de cada tipo de cuenta."""
    if rol == "usuario":
        return [
            ("Inicio", ["Inicio"]),
            ("Mi perfil y red", ["Mi perfil", "Mi red"]),
            ("Explorar", ["Usuarios", "Empresas"]),
            ("Oportunidades", ["Ofertas", "Proyectos", "Recomendaciones"]),
            ("Mensajes y consultas", ["Consultas", "Mensajes"]),
        ]
    if rol == "empresa":
        return [
            ("Inicio", ["Inicio"]),
            ("Organización", ["Mi empresa", "Proyectos y ofertas"]),
            ("Contratación", ["Postulaciones"]),
            ("Mensajes", ["Mensajes"]),
        ]
    return [
        ("Inicio", ["Inicio"]),
        ("Directorio", ["Usuarios", "Empresas", "Ofertas", "Proyectos"]),
        ("Consultas y análisis", ["Recomendaciones", "Consultas", "Analítica"]),
    ]


def _iniciales_cuenta(nombre):
    partes = [p for p in str(nombre or "").strip().split() if p]
    return "".join(p[0].upper() for p in partes[:2]) or "DP"


def _inicio():
    st.markdown(
        """
        <section class="home-hero">
          <h1>DuProGraphic</h1>
          <p>Administra los perfiles, oportunidades y proyectos de la red. Las conexiones profesionales se crean desde los perfiles de usuario.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Administración de la red")
    st.caption("Elige un apartado para consultar los datos o revisar la actividad del grafo.")
    columnas = st.columns(3, gap="medium")
    tarjetas = [
        ("Usuarios", "Perfiles, accesos y cuentas de la comunidad."),
        ("Empresas", "Organizaciones registradas en la red."),
        ("Ofertas", "Vacantes publicadas y sus propiedades."),
        ("Proyectos", "Proyectos profesionales y sus descripciones."),
        ("Recomendaciones", "Sugerencias de contactos, empleo y colaboración."),
        ("Consultas", "Rutas y recorridos entre usuarios y empresas."),
        ("Analítica", "Métricas generales, comunidades y habilidades demandadas."),
    ]
    for indice, (titulo, texto) in enumerate(tarjetas):
        columna = columnas[indice % len(columnas)]
        with columna:
            with st.container(border=True):
                st.markdown(f"#### {titulo}")
                st.caption(texto)
                st.button(
                    "Abrir apartado",
                    key=f"inicio_ir_{titulo.replace(' ', '_')}",
                    width="stretch",
                    on_click=_seleccionar_pagina,
                    args=(titulo,),
                )


def _admin_categoria(seccion):
    entidad = ENTIDADES_ADMIN.get(seccion)
    if not entidad:
        return
    if seccion == "Usuarios":
        vista = st.radio(
            "Administrar",
            ["Perfiles", "Cuentas y accesos"],
            horizontal=True,
            label_visibility="collapsed",
            key="admin_vista_usuarios",
        )
        if vista == "Cuentas y accesos":
            accounts_ui.renderizar()
            return
    st.caption("Las relaciones profesionales se crean desde los portales de usuario y empresa; aquí administras los registros.")
    operacion = st.radio(
        "Operación",
        ["Consultar", "Crear", "Editar", "Eliminar"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"admin_operacion_{entidad}",
    )
    vistas = {
        "Crear": crud_ui.renderizar_creacion,
        "Consultar": crud_ui.renderizar_lectura,
        "Editar": crud_ui.renderizar_actualizacion,
        "Eliminar": crud_ui.renderizar_eliminacion,
    }
    vistas[operacion](entidad_fija=entidad)


def main():
    st.markdown(ESTILOS, unsafe_allow_html=True)
    if _tema_oscuro_activo():
        st.markdown(ESTILOS_OSCUROS, unsafe_allow_html=True)

    cierre_pendiente = st.session_state.get("_borrar_cookie_sesion", False)
    if not cierre_pendiente:
        auth_ui.restaurar_sesion_desde_cookie()
    auth_ui.sincronizar_cookie_sesion()
    aviso_sesion = st.session_state.pop("aviso_sesion_persistente", None)
    if aviso_sesion:
        st.warning(aviso_sesion)

    cuenta = st.session_state.get("cuenta_autenticada")
    if cuenta:
        auth_ui.limpiar_claves_credenciales()
        estado_sesion = validar_sesion(cuenta)
        if estado_sesion is None:
            st.error("No se pudo validar la sesión con Neo4j. Reintenta cuando la conexión vuelva.")
            return
        if not estado_sesion:
            st.session_state.clear()
            st.session_state["_borrar_cookie_sesion"] = True
            auth_ui.sincronizar_cookie_sesion()
            st.warning("Tu acceso cambió o fue revocado. Inicia sesión de nuevo.")
            auth_ui.renderizar_acceso()
            return
    if not cuenta:
        auth_ui.renderizar_acceso()
        return

    rol = cuenta.get("rol")
    if rol == "administrador":
        paginas = PAGINAS
    elif rol == "usuario":
        paginas = role_ui.PAGINAS_USUARIO
    elif rol == "empresa":
        paginas = role_ui.PAGINAS_EMPRESA
    else:
        st.session_state.clear()
        st.session_state["_borrar_cookie_sesion"] = True
        auth_ui.sincronizar_cookie_sesion()
        st.error("El tipo de cuenta no es valido. Inicia sesion otra vez.")
        return

    with st.sidebar:
        st.markdown(
            '<div class="brand-lockup"><div class="brand-symbol">D</div><div>'
            '<div class="brand-name">Duprographic</div>'
            '<div class="brand-subtitle">Red profesional</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.session_state.get("pagina_activa") not in paginas:
            st.session_state["pagina_activa"] = "Inicio"
        nombre_cuenta = str(cuenta.get("nombre") or cuenta.get("correo", "Cuenta"))
        iniciales = escape(_iniciales_cuenta(nombre_cuenta))
        nombre_cuenta_html = escape(nombre_cuenta)
        st.markdown(
            '<div class="sidebar-profile">'
            f'<div class="sidebar-avatar">{iniciales}</div>'
            '<div><div class="sidebar-account">'
            f'{nombre_cuenta_html}</div><div class="sidebar-role">{auth_ui.ROLES[rol][0]}</div></div></div>',
            unsafe_allow_html=True,
        )
        for grupo, opciones in _grupos_menu(rol):
            if not (grupo == "Inicio" and opciones == ["Inicio"]):
                st.markdown(f'<div class="nav-group-label">{grupo}</div>', unsafe_allow_html=True)
            for pagina in opciones:
                if pagina not in paginas:
                    continue
                st.button(
                    pagina,
                    key=f"nav_{rol}_{pagina.replace(' ', '_')}",
                    type="primary" if st.session_state["pagina_activa"] == pagina else "secondary",
                    width="stretch",
                    on_click=_seleccionar_pagina,
                    args=(pagina,),
                )
        st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
        if st.button("Cerrar sesión", key="cerrar_sesion", width="stretch"):
            auth_ui.cerrar_sesion()
        st.markdown('<div class="sidebar-footer">DuProGraphic · Red profesional</div>', unsafe_allow_html=True)

    if rol == "usuario":
        titulo, descripcion = paginas[st.session_state["pagina_activa"]]
        if st.session_state["pagina_activa"] != "Inicio":
            _encabezado(titulo, descripcion)
        role_ui.renderizar_usuario(cuenta, st.session_state["pagina_activa"])
        return
    if rol == "empresa":
        titulo, descripcion = paginas[st.session_state["pagina_activa"]]
        if st.session_state["pagina_activa"] != "Inicio":
            _encabezado(titulo, descripcion)
        role_ui.renderizar_empresa(cuenta, st.session_state["pagina_activa"])
        return

    seccion = st.session_state["pagina_activa"]
    titulo, descripcion = PAGINAS[seccion]

    if seccion == "Inicio":
        _inicio()
    elif seccion in ENTIDADES_ADMIN:
        _encabezado(titulo, descripcion)
        _admin_categoria(seccion)
    elif seccion == "Recomendaciones":
        _encabezado(titulo, descripcion)
        analytics_ui.renderizar_recomendaciones()
    elif seccion == "Consultas":
        _encabezado(titulo, descripcion)
        analytics_ui.renderizar_grafo()
    elif seccion == "Analítica":
        _encabezado(titulo, descripcion)
        analytics_ui.renderizar_metricas()
    else:
        _encabezado(titulo, descripcion)
        _inicio()


if __name__ == "__main__":
    main()
