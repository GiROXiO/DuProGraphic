"""Punto de compatibilidad para los flujos profesionales de DuProGraphic.

Las acciones ya no se ejecutan desde un gestor central de relaciones. El portal de
usuario administra su propio perfil, invitaciones, habilidades y postulaciones;
el portal de empresa administra sus proyectos, ofertas y procesos de selección.
Las vistas de este módulo se conservan para mostrar esa ruta si un enlace antiguo
la invoca.
"""

import streamlit as st


def renderizar_vinculaciones():
    st.info(
        "La creación de conexiones, habilidades y participaciones está disponible "
        "en el portal de cada usuario. Las empresas gestionan proyectos y ofertas "
        "desde su propio espacio."
    )


def renderizar_portal():
    st.info(
        "Los usuarios se postulan desde la vista de ofertas. Las empresas revisan "
        "las candidaturas y actualizan su estado desde Postulaciones."
    )


def renderizar_buscador():
    st.info("El explorador de rutas ahora se encuentra en Consultas.")
