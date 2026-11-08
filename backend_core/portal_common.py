"""Funciones compartidas por los portales de usuario y empresa."""

import logging

import streamlit as st

from backend_core.connection import get_db_connection, invalidar_cache_datos


logger = logging.getLogger(__name__)


def consultar(consulta, **parametros):
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        st.error("No se pudo conectar con Neo4j Aura.")
        return None
    try:
        with conexion.driver.session() as session:
            return session.run(consulta, **parametros).data()
    except Exception as error:
        codigo = getattr(error, "code", None)
        logger.error("Error al consultar Neo4j: tipo=%s código=%s", type(error).__name__, codigo)
        if codigo:
            st.error(f"Neo4j rechazó una consulta ({codigo}). Si persiste, comparte este código para revisarlo.")
        else:
            st.error("No se pudo consultar Neo4j. Revisa la conexión y vuelve a intentarlo.")
        return None


def escribir(consulta, **parametros):
    filas = consultar(consulta, **parametros)
    if filas:
        invalidar_cache_datos()
    return filas


def opciones(etiqueta, consulta=None, **parametros):
    if etiqueta not in {"Usuario", "Empresa", "Oferta", "Proyecto", "Habilidad"}:
        st.error("Tipo de registro no permitido.")
        return None
    consulta = consulta or f"""
        MATCH (n:{etiqueta})
        RETURN n.id AS id, coalesce(n.nombre, n.titulo, n.id) AS nombre
        ORDER BY nombre
    """
    filas = consultar(consulta, **parametros)
    if filas is None:
        return None
    return {str(fila["id"]): str(fila["nombre"]) for fila in filas}


def ir_a(pagina, **estado):
    st.session_state["pagina_activa"] = pagina
    st.session_state.update(estado)
    st.rerun()


def tarjeta(titulo, texto="", detalle="", etiqueta=None):
    with st.container(border=True):
        if etiqueta:
            st.caption(etiqueta)
        st.markdown(f"**{titulo}**")
        if texto:
            st.write(texto)
        if detalle:
            st.caption(detalle)


def enviar_mensaje(cuenta_destino):
    st.session_state["mensajes_destinatario_preseleccionado"] = cuenta_destino
    st.session_state["nuevo_mensaje_destinatario"] = cuenta_destino
    ir_a("Mensajes")


def mostrar_lista(filas, mensaje_vacio="Todavía no hay información para mostrar."):
    if filas is None:
        return
    if filas:
        st.dataframe(filas, width="stretch", hide_index=True)
    else:
        st.info(mensaje_vacio)
