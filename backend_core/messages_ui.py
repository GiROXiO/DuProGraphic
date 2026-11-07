from datetime import datetime

import streamlit as st

from backend_core import messages


def _fecha_legible(fecha):
    if not fecha:
        return ""
    try:
        return datetime.fromisoformat(fecha).astimezone().strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return fecha


def renderizar(cuenta):
    cuenta_id = cuenta.get("id")
    if not cuenta_id:
        st.error("No se pudo identificar tu cuenta para abrir los mensajes.")
        return

    st.caption("Mensajes internos entre cuentas. Puedes indicar si escribes por un proyecto o una oferta.")
    try:
        destinatarios = messages.listar_destinatarios(cuenta_id)
        conversaciones = messages.obtener_conversaciones(cuenta_id)
    except Exception:
        st.error("No se pudo cargar la bandeja. Revisa la conexion con Neo4j Aura.")
        return

    izquierda, derecha = st.columns([1, 2], gap="large")
    with izquierda:
        st.markdown("#### Nueva conversacion")
        if destinatarios:
            opciones = {
                registro["id"]: (
                    f"{registro['nombre']} ({'Empresa' if registro['rol'] == 'empresa' else 'Usuario'})"
                )
                for registro in destinatarios
            }
            contexto_tipo = st.selectbox(
                "Tema", ["General", "Proyecto", "Oferta"], key="mensaje_contexto_tipo"
            )
            contexto_id = ""
            if contexto_tipo in {"Proyecto", "Oferta"}:
                try:
                    contextos = messages.listar_contextos(contexto_tipo)
                except Exception:
                    contextos = []
                    st.error("No se pudieron cargar los temas disponibles.")
                opciones_contexto = {r["id"]: r["nombre"] for r in contextos}
                if opciones_contexto:
                    contexto_id = st.selectbox(
                        contexto_tipo,
                        list(opciones_contexto),
                        format_func=lambda x: opciones_contexto[x],
                        key="mensaje_contexto_id",
                    )
                else:
                    sustantivo = "proyectos" if contexto_tipo == "Proyecto" else "ofertas"
                    st.info(f"No hay {sustantivo} disponibles.")
            with st.form("form_nueva_conversacion"):
                destinatario_id = st.selectbox(
                    "Enviar a", list(opciones), format_func=lambda x: opciones[x]
                )
                iniciar = st.form_submit_button("Abrir conversacion", width="stretch")
            if iniciar:
                estado, conversacion_id = messages.iniciar_conversacion(
                    cuenta_id,
                    destinatario_id,
                    contexto_tipo,
                    contexto_id,
                )
                if estado == "abierta":
                    st.session_state["conversacion_activa"] = conversacion_id
                    st.session_state["seleccionar_conversacion"] = conversacion_id
                    st.rerun()
                elif estado == "contexto_invalido":
                    st.warning("Selecciona un proyecto u oferta para usarlo como tema.")
                else:
                    st.error("No se pudo abrir la conversacion.")
        else:
            st.info("Aun no hay otras cuentas registradas para contactar.")

        if conversaciones:
            st.markdown("#### Tus conversaciones")
            labels = {
                c["id"]: " · ".join(
                    part for part in [
                        c["contacto"],
                        c["contexto_tipo"] if c["contexto_tipo"] != "General" else "General",
                        c["ultimo_mensaje"][:52] if c["ultimo_mensaje"] else "Sin mensajes",
                    ] if part
                )
                for c in conversaciones
            }
            ids = list(labels)
            actual = st.session_state.get("conversacion_activa")
            if actual not in ids:
                actual = ids[0]
                st.session_state["conversacion_activa"] = actual
            activa = st.selectbox(
                "Bandeja",
                ids,
                index=ids.index(actual),
                format_func=lambda x: labels[x],
                key="seleccionar_conversacion",
            )
            st.session_state["conversacion_activa"] = activa
        else:
            activa = st.session_state.get("conversacion_activa")

    with derecha:
        conversacion = next((c for c in conversaciones if c["id"] == activa), None)
        if not conversacion:
            st.markdown("#### Mensajes")
            st.info("Abre una conversacion para empezar.")
            return

        st.markdown(f"#### {conversacion['contacto']}")
        contexto = conversacion.get("contexto_tipo") or "General"
        if contexto != "General":
            st.caption(
                f"Tema: {contexto} - "
                f"{conversacion.get('contexto_nombre') or conversacion.get('contexto_id') or ''}"
            )
        st.divider()
        try:
            mensajes = messages.obtener_mensajes(activa, cuenta_id)
        except Exception:
            st.error("No se pudieron leer los mensajes de esta conversacion.")
            return

        if not mensajes:
            st.caption("Esta conversacion aun no tiene mensajes.")
        for mensaje in mensajes:
            autor = "Tú" if mensaje["autor_id"] == cuenta_id else mensaje["autor"]
            with st.container(border=True):
                st.caption(f"{autor} · {_fecha_legible(mensaje['fecha'])}")
                st.text(mensaje["texto"])

        with st.form("form_enviar_mensaje", clear_on_submit=True):
            texto = st.text_area("Escribe un mensaje", max_chars=3000, key=f"texto_{activa}")
            enviar = st.form_submit_button("Enviar mensaje", width="stretch")
        if enviar:
            estado = messages.enviar_mensaje(activa, cuenta_id, texto)
            if estado == "enviado":
                st.rerun()
            elif estado == "vacio":
                st.warning("Escribe un mensaje antes de enviarlo.")
            elif estado == "largo":
                st.warning("El mensaje supera el limite de 3000 caracteres.")
            elif estado == "sin_acceso":
                st.error("Esta cuenta no participa en esa conversacion.")
            else:
                st.error("No se pudo enviar el mensaje.")
