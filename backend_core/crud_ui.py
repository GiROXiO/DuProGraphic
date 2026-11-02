import streamlit as st
from backend_core.connection import get_db_connection

def renderizar_creacion():
    st.write("Interfaz de registro (Create) en construcción...")
    # conn = get_db_connection()
    # Aquí Juan Cáceres inyectará los st.text_input y el botón de guardado

def renderizar_lectura():
    st.write("Interfaz de consulta (Read) en construcción...")

def renderizar_actualizacion():
    st.write("Interfaz de actualización (Update) en construcción...")

def renderizar_eliminacion():
    st.write("Interfaz de eliminación (Delete) en construcción...")