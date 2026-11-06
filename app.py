import streamlit as st

from analytics_dashboard import analytics_ui
from backend_core import crud_ui
from business_logic import logic_ui


st.set_page_config(
    page_title="Duprographic | Red profesional",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


ESTILOS = """
<style>
:root {
    --ink: #24364b;
    --muted: #5d6977;
    --line: #aeb9c5;
    --surface: #ffffff;
    --canvas: #f0f1f2;
    --navy: #263e5b;
    --blue: #315c82;
}

.stApp { background: var(--canvas); color: var(--ink); font-family: Calibri, Arial, sans-serif; }
.block-container { max-width: 1360px; padding-top: 1.4rem; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] {
    background: #dfe4e8;
    border-right: 2px solid #aab4be;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #26384d; }
.brand-lockup { display: flex; align-items: center; gap: 10px; padding: 8px 2px 18px; }
.brand-symbol {
    display: grid; place-items: center; width: 35px; height: 35px; border: 1px solid #172b43;
    border-radius: 0; color: white; font-family: Calibri, Arial, sans-serif;
    font-size: 21px; font-weight: 700; background: #294665;
}
.brand-name { color: #20344d; font-family: Calibri, Arial, sans-serif; font-size: 18px; font-weight: 700; }
.brand-subtitle { color: #5d6977; font-size: 11px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 7px 9px; margin: 2px 0; border-radius: 0;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #cbd5df; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-color: #aab4be; border-radius: 0; }
.section-banner {
    padding: 17px 21px; margin-bottom: 20px; border: 1px solid var(--line);
    border-top: 4px solid var(--blue); border-radius: 0; background: #e3e8ed;
}
.section-banner h1 { color: var(--ink); font-family: Calibri, Arial, sans-serif; font-size: 29px; line-height: 1.2; margin: 4px 0 6px; }
.section-banner p { color: var(--muted); margin: 0; font-size: 14px; }
.home-hero {
    padding: 25px 29px; border: 1px solid #9eacba; border-top: 4px solid #294b6d;
    border-radius: 0; color: var(--ink); background: #dce4eb;
}
.home-hero h1 { color: #20344d; max-width: 760px; font-family: Calibri, Arial, sans-serif; font-size: 32px; line-height: 1.2; margin: 0 0 8px; }
.home-hero p { color: #4c5d70; font-size: 15px; max-width: 760px; margin: 0; }
.feature-card {
    min-height: 138px; padding: 15px 17px; border: 1px solid #aeb9c5;
    border-radius: 0; background: var(--surface);
}
.feature-card h3 { color: var(--ink); font-family: Calibri, Arial, sans-serif; font-size: 17px; margin: 0 0 6px; }
.feature-card p { color: var(--muted); font-size: 13px; line-height: 1.45; margin: 0; }
h1, h2, h3, button, input, textarea, label { font-family: Calibri, Arial, sans-serif; }
h2, h3 { color: var(--ink); }
[data-testid="stHeaderActionElements"] { display: none !important; }
div[data-testid="stMetric"] {
    padding: 12px 15px; border: 1px solid var(--line); border-radius: 0;
    background: white;
}
div[data-testid="stMetric"] label { color: var(--muted); }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 0; overflow: hidden; }
div[data-testid="stForm"] {
    padding: 15px 17px 10px; border: 1px solid var(--line); border-radius: 0;
    background: #f8f9fa;
}
.stButton button, [data-testid="stFormSubmitButton"] button {
    min-height: 38px; border-radius: 2px; font-weight: 600;
    background: #284d73 !important; color: #ffffff !important;
    border: 1px solid #193650 !important;
}
.stButton button *, [data-testid="stFormSubmitButton"] button * { color: #ffffff !important; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    background: #1f3f60 !important; border-color: #142e48 !important;
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
    color: #24364b !important;
    border: 1px solid #8795a3 !important;
    border-radius: 1px !important;
}
[data-baseweb="select"] svg { fill: #344b63 !important; }
[role="listbox"], [role="option"] { background-color: #ffffff !important; color: #24364b !important; }
[role="option"]:hover { background-color: #e1e7ed !important; }
input::placeholder, textarea::placeholder { color: #647282 !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important; color: #26384d !important;
    border-color: transparent !important; text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] * {
    color: #26384d !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #cbd5df !important; color: #20344d !important;
    border-color: #8795a3 !important; text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * {
    color: #20344d !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #cbd5df !important; border-color: #aeb9c5 !important;
}

@media (max-width: 700px) {
    .block-container { padding: 1rem 1rem 1.8rem; }
    .home-hero { padding: 20px 17px; }
    .section-banner { padding: 15px 16px; }
}
</style>
"""


ESTILOS_OSCUROS = """
<style>
.stApp { background: #151c25 !important; color: #e7edf4 !important; }
[data-testid="stSidebar"] { background: #1c2632 !important; border-right: 2px solid #3e4c5c !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #e0e7ef !important; }
.brand-name { color: #f0f3f7 !important; }
.brand-subtitle { color: #c1ccd8 !important; }
.brand-symbol { background: #334b66 !important; border-color: #74869a !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #2b3949 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border-color: #526172 !important; }
.section-banner { background: #202a36 !important; border-color: #526172 !important; border-top-color: #7597ba !important; }
.home-hero { background: #222d3a !important; border-color: #526172 !important; border-top-color: #7597ba !important; }
.home-hero h1, .home-hero p, .section-banner h1, .section-banner p, h1, h2, h3 { color: #e7edf4 !important; }
.feature-card, div[data-testid="stMetric"], div[data-testid="stForm"] {
    background: #222c38 !important; border-color: #526172 !important;
}
.feature-card h3, .feature-card p, div[data-testid="stMetric"] label { color: #d2dbe5 !important; }
div[data-testid="stDataFrame"] { border-color: #526172 !important; }
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #1b2530 !important; color: #edf2f7 !important; border-color: #6c7b8b !important;
}
[data-baseweb="select"] svg { fill: #d7e0e9 !important; }
[role="listbox"], [role="option"] { background-color: #222c38 !important; color: #edf2f7 !important; }
[role="option"]:hover { background-color: #344457 !important; }
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
    background: transparent !important; color: #e0e7ef !important;
    border-color: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] *,
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * {
    color: #e0e7ef !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #34485d !important; color: #e0e7ef !important;
    border-color: #74869a !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #2b3949 !important; border-color: #526172 !important;
}
</style>
"""


PAGINAS = {
    "Inicio": ("DuProGraphic", "Aplicación para gestionar y analizar una red profesional con Neo4j."),
    "Gestión de datos": ("Gestión de datos", "Registra, consulta y actualiza usuarios, empresas y ofertas."),
    "Relaciones": ("Relaciones", "Conecta usuarios, habilidades, proyectos, empresas y ofertas."),
    "Analítica": ("Consultas y análisis", "Revisa rutas, recomendaciones y resultados de la red."),
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


def _inicio():
    st.markdown(
        """
        <section class="home-hero">
          <h1>DuProGraphic</h1>
          <p>Aplicación para gestionar y analizar una red profesional usando una base de datos de grafos.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("¿Qué quieres hacer?")
    columnas = st.columns(3, gap="medium")
    tarjetas = [
        ("Gestión de datos", "Consulta y actualiza usuarios, empresas y ofertas.", "Gestionar datos"),
        ("Relaciones", "Vincula perfiles, habilidades, proyectos y vacantes.", "Gestionar relaciones"),
        ("Analítica", "Consulta rutas, recomendaciones y métricas de la red.", "Ver analítica"),
    ]
    for columna, (titulo, texto, accion) in zip(columnas, tarjetas):
        with columna:
            st.markdown(
                f'<div class="feature-card"><h3>{titulo}</h3><p>{texto}</p></div>',
                unsafe_allow_html=True,
            )
            st.button(
                accion,
                key=f"inicio_ir_{titulo.replace(' ', '_')}",
                width="stretch",
                on_click=_seleccionar_pagina,
                args=(titulo,),
            )
    st.markdown("")
    st.caption("También puedes cambiar de sección desde el menú lateral.")


def main():
    st.markdown(ESTILOS, unsafe_allow_html=True)
    if _tema_oscuro_activo():
        st.markdown(ESTILOS_OSCUROS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            '<div class="brand-lockup"><div class="brand-symbol">D</div><div>'
            '<div class="brand-name">Duprographic</div>'
            '<div class="brand-subtitle">Proyecto de bases de datos</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.session_state.get("pagina_activa") not in PAGINAS:
            st.session_state["pagina_activa"] = "Inicio"
        for pagina in PAGINAS:
            st.button(
                pagina,
                key=f"nav_{pagina.replace(' ', '_')}",
                type="primary" if st.session_state["pagina_activa"] == pagina else "secondary",
                width="stretch",
                on_click=_seleccionar_pagina,
                args=(pagina,),
            )
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Equipo del proyecto"):
            st.caption("Jerónimo Castro · Arquitectura de BD")
            st.caption("Juan Cáceres · Backend CRUD")
            st.caption("Juan Arrieta · Lógica de negocio")
            st.caption("Miguel Carrizosa · Analítica")

    seccion = st.session_state["pagina_activa"]
    titulo, descripcion = PAGINAS[seccion]

    if seccion == "Inicio":
        _inicio()
    elif seccion == "Gestión de datos":
        _encabezado(titulo, descripcion)
        operacion = st.selectbox(
            "Operación",
            ["Registrar", "Consultar", "Actualizar", "Eliminar"],
            key="operacion_crud",
        )
        vistas = {
            "Registrar": crud_ui.renderizar_creacion,
            "Consultar": crud_ui.renderizar_lectura,
            "Actualizar": crud_ui.renderizar_actualizacion,
            "Eliminar": crud_ui.renderizar_eliminacion,
        }
        vistas[operacion]()
    elif seccion == "Relaciones":
        _encabezado(titulo, descripcion)
        flujo = st.selectbox(
            "Flujo",
            ["Gestor de relaciones", "Portal de postulaciones", "Explorador de rutas"],
            key="flujo_negocio",
        )
        vistas = {
            "Gestor de relaciones": logic_ui.renderizar_vinculaciones,
            "Portal de postulaciones": logic_ui.renderizar_portal,
            "Explorador de rutas": logic_ui.renderizar_buscador,
        }
        vistas[flujo]()
    else:
        _encabezado(titulo, descripcion)
        reporte = st.selectbox(
            "Vista analítica",
            ["Recomendaciones", "Inteligencia de mercado", "Rutas y proyectos"],
            key="vista_analitica",
        )
        vistas = {
            "Recomendaciones": analytics_ui.renderizar_recomendaciones,
            "Inteligencia de mercado": analytics_ui.renderizar_metricas,
            "Rutas y proyectos": analytics_ui.renderizar_grafo,
        }
        vistas[reporte]()


if __name__ == "__main__":
    main()
