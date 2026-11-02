import streamlit as st

# Importaciones modulares de la arquitectura
from backend_core import crud_ui
from business_logic import logic_ui
from analytics_dashboard import analytics_ui

# Configuración inicial de la página
st.set_page_config(page_title="Duprographic - Neo4j", layout="wide")

def main():
    # Menú lateral
    st.sidebar.title("Duprographic")
    st.sidebar.markdown("---")
    
    opciones_menu = [
        "Inicio", 
        "1. Gestión de Entidades (CRUD)", 
        "2. Lógica de Negocio", 
        "3. Panel de Analítica"
    ]
    eleccion = st.sidebar.radio("Navegación", opciones_menu)
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Equipo de Desarrollo:\n"
        "- Jerónimo Castro (Arquitecto BD)\n"
        "- Juan Cáceres (Backend Core)\n"
        "- Juan Arrieta (Lógica de Negocio)\n"
        "- Miguel Carrizosa (Analista de Datos)"
    )

    # Enrutamiento de vistas modulares
    if eleccion == "Inicio":
        st.title("Plataforma Duprographic")
        st.markdown("""
        Sistema de gestión y análisis de relaciones profesionales basado en bases de datos orientadas a grafos (Neo4j).
        """)
        
    elif eleccion == "1. Gestión de Entidades (CRUD)":
        st.title("Gestión de Entidades (CRUD)")
        st.caption("Módulo asignado a: Juan Cáceres")
        st.markdown("---")
        
        operacion = st.selectbox(
            "Seleccione la operación transaccional:", 
            ["Registrar (Create)", "Consultar (Read)", "Actualizar (Update)", "Eliminar (Delete)"]
        )
        
        # Inyección de las funciones del submódulo CRUD
        if operacion == "Registrar (Create)":
            crud_ui.renderizar_creacion()
        elif operacion == "Consultar (Read)":
            crud_ui.renderizar_lectura()
        elif operacion == "Actualizar (Update)":
            crud_ui.renderizar_actualizacion()
        elif operacion == "Eliminar (Delete)":
            crud_ui.renderizar_eliminacion()
        
    elif eleccion == "2. Lógica de Negocio":
        st.title("Lógica de Negocio y Vinculaciones")
        st.caption("Módulo asignado a: Juan Arrieta")
        st.markdown("---")
        
        flujo = st.selectbox(
            "Seleccione el motor a utilizar:",
            ["Gestor de Relaciones (Networking)", "Portal de Postulaciones", "Explorador de Rutas"]
        )
        
        # Inyección de las funciones del submódulo de Lógica
        if flujo == "Gestor de Relaciones (Networking)":
            logic_ui.renderizar_vinculaciones()
        elif flujo == "Portal de Postulaciones":
            logic_ui.renderizar_portal()
        elif flujo == "Explorador de Rutas":
            logic_ui.renderizar_buscador()
        
    elif eleccion == "3. Panel de Analítica":
        st.title("Panel de Analítica y Recomendaciones")
        st.caption("Módulo asignado a: Miguel Carrizosa")
        st.markdown("---")
        
        reporte = st.selectbox(
            "Seleccione el tablero analítico:",
            ["Motor de Recomendaciones", "Inteligencia de Mercado (Insights)", "Análisis de Red Compleja"]
        )
        
        # Inyección de las funciones del submódulo de Analítica
        if reporte == "Motor de Recomendaciones":
            analytics_ui.renderizar_recomendaciones()
        elif reporte == "Inteligencia de Mercado (Insights)":
            analytics_ui.renderizar_metricas()
        elif reporte == "Análisis de Red Compleja":
            analytics_ui.renderizar_grafo()

if __name__ == "__main__":
    main()