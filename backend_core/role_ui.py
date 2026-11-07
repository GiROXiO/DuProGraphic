"""Vistas privadas y acotadas para cuentas de usuario y empresa."""

import uuid
from html import escape

import streamlit as st

from backend_core.connection import get_db_connection, invalidar_cache_datos
from backend_core import messages_ui


PAGINAS_USUARIO = {
    "Inicio": ("Mi espacio", "Resumen de tu perfil, red y postulaciones."),
    "Mi perfil": ("Mi perfil", "Actualiza tu informacion profesional."),
    "Mi red": ("Mi red", "Consulta y crea conexiones profesionales."),
    "Habilidades y proyectos": ("Habilidades y proyectos", "Muestra tus competencias y participaciones."),
    "Oportunidades": ("Oportunidades", "Explora ofertas abiertas y postulate."),
    "Mensajes": ("Mensajes", "Conversa con profesionales y empresas."),
}

PAGINAS_EMPRESA = {
    "Inicio": ("Espacio de empresa", "Resumen de tus ofertas y postulaciones recibidas."),
    "Mi empresa": ("Mi empresa", "Actualiza los datos de tu organizacion."),
    "Mis ofertas": ("Mis ofertas", "Publica vacantes y define habilidades requeridas."),
    "Postulaciones": ("Postulaciones recibidas", "Consulta los candidatos de tus ofertas."),
    "Mensajes": ("Mensajes", "Conversa con profesionales y empresas."),
}


def _filas(consulta, **parametros):
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        st.error("No se pudo conectar con Neo4j Aura.")
        return None
    try:
        with conexion.driver.session() as session:
            return session.run(consulta, **parametros).data()
    except Exception:
        st.error("No se pudo completar la consulta. Revisa la conexion con Neo4j Aura.")
        return None


def _mostrar(filas, vacio="No hay registros para mostrar."):
    if filas is None:
        return
    if filas:
        st.dataframe(filas, width="stretch", hide_index=True)
    else:
        st.info(vacio)


def _perfil(etiqueta, entidad_id):
    if etiqueta not in {"Usuario", "Empresa"}:
        return None
    filas = _filas(
        f"MATCH (p:{etiqueta} {{id: $id}}) RETURN properties(p) AS perfil",
        id=entidad_id,
    )
    return filas[0]["perfil"] if filas else None


def renderizar_usuario(cuenta, pagina):
    usuario_id = cuenta["entidad_id"]
    if not usuario_id:
        st.error("La cuenta no tiene un perfil de usuario asociado.")
        return

    perfil = _perfil("Usuario", usuario_id)
    if perfil is None:
        st.error("No se encontro tu perfil en Neo4j Aura.")
        return

    if pagina == "Inicio":
        st.markdown(
            f"<section class='home-hero'><h1>Hola, {escape(str(perfil.get('nombre', 'usuario')))}</h1>"
            "<p>Desde aqui puedes mantener tu perfil, ampliar tu red y revisar oportunidades.</p></section>",
            unsafe_allow_html=True,
        )
        conteos = _filas(
            """
            MATCH (u:Usuario {id: $id})
            OPTIONAL MATCH (u)-[:CONECTA_CON]-(contacto:Usuario)
            WITH u, count(DISTINCT contacto) AS contactos
            OPTIONAL MATCH (u)-[:TIENE_HABILIDAD]->(h:Habilidad)
            WITH contactos, count(DISTINCT h) AS habilidades
            MATCH (usuario:Usuario {id: $id})
            OPTIONAL MATCH (usuario)-[:POSTULA_A]->(o:Oferta)
            RETURN contactos, habilidades, count(DISTINCT o) AS postulaciones
            """,
            id=usuario_id,
        )
        valores = conteos[0] if conteos else {"contactos": 0, "habilidades": 0, "postulaciones": 0}
        c1, c2, c3 = st.columns(3)
        c1.metric("Contactos", valores["contactos"])
        c2.metric("Habilidades", valores["habilidades"])
        c3.metric("Postulaciones", valores["postulaciones"])
        st.info("Usa Mi perfil para completar tus datos y Habilidades y proyectos para actualizar tu experiencia.")

    elif pagina == "Mi perfil":
        with st.form("form_perfil_usuario"):
            nombre = st.text_input("Nombre", value=perfil.get("nombre", ""))
            profesional = st.text_input(
                "Perfil profesional", value=perfil.get("perfil_profesional", "")
            )
            universidad = st.text_input("Universidad o institucion", value=perfil.get("universidad", ""))
            guardar = st.form_submit_button("Guardar perfil", width="stretch")
        if guardar:
            if not nombre.strip():
                st.warning("El nombre es obligatorio.")
            else:
                resultado = _filas(
                    """
                    MATCH (u:Usuario {id: $id})
                    SET u.nombre = $nombre,
                        u.perfil_profesional = $profesional,
                        u.universidad = $universidad
                    RETURN u.id AS id
                    """,
                    id=usuario_id,
                    nombre=nombre.strip(),
                    profesional=profesional.strip(),
                    universidad=universidad.strip(),
                )
                if resultado:
                    invalidar_cache_datos()
                    st.success("Tu perfil se actualizo.")

    elif pagina == "Mi red":
        st.markdown("#### Tus conexiones")
        contactos = _filas(
            """
            MATCH (u:Usuario {id: $id})-[:CONECTA_CON]-(otro:Usuario)
            RETURN DISTINCT otro.id AS id, otro.nombre AS nombre,
                   otro.perfil_profesional AS perfil
            ORDER BY nombre
            """,
            id=usuario_id,
        )
        _mostrar(contactos, "Aun no tienes conexiones profesionales.")
        st.markdown("#### Conectar con un profesional")
        personas = _filas(
            """
            MATCH (otro:Usuario)
            WHERE otro.id <> $id
              AND NOT EXISTS { MATCH (:Usuario {id: $id})-[:CONECTA_CON]-(otro) }
            RETURN otro.id AS id, otro.nombre AS nombre,
                   otro.perfil_profesional AS perfil
            ORDER BY nombre
            """,
            id=usuario_id,
        )
        if personas:
            opciones = {p["id"]: f"{p['nombre']} - {p.get('perfil') or 'Sin perfil'}" for p in personas}
            with st.form("form_conectar_usuario"):
                contacto_id = st.selectbox(
                    "Profesional", list(opciones), format_func=lambda x: opciones[x]
                )
                fuerza = st.selectbox("Fuerza de la conexion", ["baja", "media", "alta"])
                conectar = st.form_submit_button("Crear conexion", width="stretch")
            if conectar:
                resultado = _filas(
                    """
                    MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
                    MERGE (a)-[ab:CONECTA_CON]->(b)
                    ON CREATE SET ab.fuerza_conexion = $fuerza
                    MERGE (b)-[ba:CONECTA_CON]->(a)
                    ON CREATE SET ba.fuerza_conexion = $fuerza
                    RETURN a.id AS id
                    """,
                    a=usuario_id,
                    b=contacto_id,
                    fuerza=fuerza,
                )
                if resultado:
                    invalidar_cache_datos()
                    st.success("Conexion profesional creada.")
                    st.rerun()
        else:
            st.info("No hay otros perfiles disponibles para conectar.")

    elif pagina == "Habilidades y proyectos":
        habilidades = _filas("MATCH (h:Habilidad) RETURN h.id AS id, h.nombre AS nombre ORDER BY nombre")
        proyectos = _filas("MATCH (p:Proyecto) RETURN p.id AS id, p.nombre AS nombre ORDER BY nombre")
        st.markdown("#### Tus habilidades")
        existentes = _filas(
            "MATCH (:Usuario {id: $id})-[r:TIENE_HABILIDAD]->(h:Habilidad) "
            "RETURN h.nombre AS habilidad, r.nivel_dominio AS nivel ORDER BY habilidad",
            id=usuario_id,
        )
        _mostrar(existentes, "Todavia no has agregado habilidades.")
        if habilidades:
            opciones_h = {r["id"]: r["nombre"] for r in habilidades}
            with st.form("form_habilidad_usuario"):
                habilidad_id = st.selectbox("Habilidad", list(opciones_h), format_func=lambda x: opciones_h[x])
                nivel = st.selectbox("Nivel", ["basico", "intermedio", "avanzado"])
                guardar_habilidad = st.form_submit_button("Guardar habilidad", width="stretch")
            if guardar_habilidad:
                result = _filas(
                    "MATCH (u:Usuario {id: $u}), (h:Habilidad {id: $h}) "
                    "MERGE (u)-[r:TIENE_HABILIDAD]->(h) SET r.nivel_dominio = $nivel "
                    "RETURN u.id AS id",
                    u=usuario_id,
                    h=habilidad_id,
                    nivel=nivel,
                )
                if result:
                    invalidar_cache_datos()
                    st.success("Habilidad guardada en tu perfil.")
                    st.rerun()

        st.markdown("#### Tus proyectos")
        participaciones = _filas(
            "MATCH (:Usuario {id: $id})-[r:PARTICIPA_EN]->(p:Proyecto) "
            "RETURN p.nombre AS proyecto, r.rol AS rol ORDER BY proyecto",
            id=usuario_id,
        )
        _mostrar(participaciones, "Todavia no has agregado proyectos.")
        if proyectos:
            opciones_p = {r["id"]: r["nombre"] for r in proyectos}
            with st.form("form_proyecto_usuario"):
                proyecto_id = st.selectbox("Proyecto", list(opciones_p), format_func=lambda x: opciones_p[x])
                rol_proyecto = st.text_input("Tu rol en el proyecto")
                guardar_proyecto = st.form_submit_button("Guardar participacion", width="stretch")
            if guardar_proyecto:
                if not rol_proyecto.strip():
                    st.warning("Indica tu rol en el proyecto.")
                else:
                    result = _filas(
                        "MATCH (u:Usuario {id: $u}), (p:Proyecto {id: $p}) "
                        "MERGE (u)-[r:PARTICIPA_EN]->(p) SET r.rol = $rol RETURN u.id AS id",
                        u=usuario_id,
                        p=proyecto_id,
                        rol=rol_proyecto.strip(),
                    )
                    if result:
                        invalidar_cache_datos()
                        st.success("Participacion guardada.")
                        st.rerun()

    elif pagina == "Oportunidades":
        ofertas = _filas(
            """
            MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
            WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
            RETURN o.id AS id, o.titulo AS oferta, e.nombre AS empresa,
                   o.modalidad AS modalidad, o.nivel_experiencia AS experiencia
            ORDER BY oferta
            """
        )
        st.markdown("#### Ofertas abiertas")
        _mostrar(ofertas, "No hay ofertas abiertas publicadas.")
        if ofertas:
            opciones = {r["id"]: f"{r['oferta']} - {r['empresa']}" for r in ofertas}
            with st.form("form_postularse_propio"):
                oferta_id = st.selectbox("Oferta", list(opciones), format_func=lambda x: opciones[x])
                postularse = st.form_submit_button("Postularme", width="stretch")
            if postularse:
                def registrar(tx):
                    estado = tx.run(
                        """
                        MATCH (o:Oferta {id: $oferta})
                        RETURN toLower(trim(coalesce(o.estado, ''))) = 'abierta' AS abierta,
                               EXISTS { MATCH (:Empresa)-[:PUBLICA]->(o) } AS publicada,
                               EXISTS { MATCH (:Usuario {id: $u})-[:POSTULA_A]->(o) } AS duplicada
                        """,
                        oferta=oferta_id,
                        u=usuario_id,
                    ).single()
                    if estado is None:
                        return "no_encontrada"
                    if not estado["abierta"]:
                        return "cerrada"
                    if not estado["publicada"]:
                        return "no_publicada"
                    if estado["duplicada"]:
                        return "duplicada"
                    tx.run(
                        """
                        MATCH (u:Usuario {id: $u}), (o:Oferta {id: $o})
                        CREATE (u)-[:POSTULA_A {
                            fecha_postulacion: $fecha, estado_proceso: 'aplicado'
                        }]->(o)
                        """,
                        u=usuario_id,
                        o=oferta_id,
                        fecha=__import__("datetime").date.today().isoformat(),
                    ).consume()
                    return "creada"

                conexion = get_db_connection()
                try:
                    with conexion.driver.session() as session:
                        estado = session.execute_write(registrar)
                    if estado == "creada":
                        invalidar_cache_datos()
                        st.success("Postulacion registrada.")
                    elif estado == "duplicada":
                        st.info("Ya te habias postulado a esta oferta.")
                    else:
                        st.warning("La oferta ya no esta disponible para postularse.")
                except Exception:
                    st.error("No se pudo registrar la postulacion.")

    elif pagina == "Mensajes":
        messages_ui.renderizar(cuenta)


def renderizar_empresa(cuenta, pagina):
    empresa_id = cuenta["entidad_id"]
    if not empresa_id:
        st.error("La cuenta no tiene una empresa asociada.")
        return
    perfil = _perfil("Empresa", empresa_id)
    if perfil is None:
        st.error("No se encontro tu empresa en Neo4j Aura.")
        return

    if pagina == "Inicio":
        st.markdown(
            f"<section class='home-hero'><h1>Hola, {escape(str(perfil.get('nombre', 'empresa')))}</h1>"
            "<p>Administra las vacantes de tu organizacion y revisa las postulaciones recibidas.</p></section>",
            unsafe_allow_html=True,
        )
        conteos = _filas(
            """
            MATCH (e:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
            OPTIONAL MATCH (:Usuario)-[r:POSTULA_A]->(o)
            RETURN count(DISTINCT o) AS ofertas, count(r) AS postulaciones
            """,
            id=empresa_id,
        )
        valores = conteos[0] if conteos else {"ofertas": 0, "postulaciones": 0}
        c1, c2 = st.columns(2)
        c1.metric("Ofertas publicadas", valores["ofertas"])
        c2.metric("Postulaciones recibidas", valores["postulaciones"])
        st.info("Completa Mi empresa y publica tu primera oferta desde Mis ofertas.")

    elif pagina == "Mi empresa":
        with st.form("form_perfil_empresa"):
            nombre = st.text_input("Nombre", value=perfil.get("nombre", ""))
            sector = st.text_input("Sector", value=perfil.get("sector", ""))
            guardar = st.form_submit_button("Guardar empresa", width="stretch")
        if guardar:
            if not nombre.strip():
                st.warning("El nombre de la empresa es obligatorio.")
            else:
                result = _filas(
                    "MATCH (e:Empresa {id: $id}) SET e.nombre = $nombre, e.sector = $sector RETURN e.id AS id",
                    id=empresa_id,
                    nombre=nombre.strip(),
                    sector=sector.strip(),
                )
                if result:
                    invalidar_cache_datos()
                    st.success("Datos de empresa actualizados.")

    elif pagina == "Mis ofertas":
        actuales = _filas(
            """
            MATCH (:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
            RETURN o.id AS id, o.titulo AS titulo, o.estado AS estado,
                   o.modalidad AS modalidad, o.nivel_experiencia AS experiencia
            ORDER BY titulo
            """,
            id=empresa_id,
        )
        _mostrar(actuales, "Esta empresa aun no ha publicado ofertas.")
        habilidades = _filas("MATCH (h:Habilidad) RETURN h.id AS id, h.nombre AS nombre ORDER BY nombre")
        opciones_h = {r["id"]: r["nombre"] for r in habilidades or []}
        st.markdown("#### Publicar una oferta")
        with st.form("form_nueva_oferta_empresa", clear_on_submit=True):
            titulo = st.text_input("Titulo de la oferta")
            modalidad = st.selectbox("Modalidad", ["remoto", "híbrido", "presencial"])
            experiencia = st.selectbox("Nivel de experiencia", ["Junior", "Semi-Senior", "Senior"])
            requisitos = st.multiselect(
                "Habilidades requeridas", list(opciones_h),
                format_func=lambda x: opciones_h[x],
            )
            publicar = st.form_submit_button("Publicar oferta", width="stretch")
        if publicar:
            if not titulo.strip():
                st.warning("Escribe el titulo de la oferta.")
            else:
                oferta_id = "O" + uuid.uuid4().hex[:10].upper()
                conexion = get_db_connection()
                try:
                    with conexion.driver.session() as session:
                        def crear_oferta(tx):
                            tx.run(
                                """
                                MATCH (e:Empresa {id: $empresa})
                                CREATE (o:Oferta {
                                    id: $id, titulo: $titulo, estado: 'abierta',
                                    modalidad: $modalidad, nivel_experiencia: $experiencia
                                })
                                CREATE (e)-[:PUBLICA {fecha_publicacion: $fecha}]->(o)
                                WITH o
                                UNWIND $habilidades AS hid
                                MATCH (h:Habilidad {id: hid})
                                MERGE (o)-[:REQUIERE {es_obligatoria: true}]->(h)
                                RETURN o.id AS id
                                """,
                                empresa=empresa_id,
                                id=oferta_id,
                                titulo=titulo.strip(),
                                modalidad=modalidad,
                                experiencia=experiencia,
                                fecha=__import__("datetime").date.today().isoformat(),
                                habilidades=requisitos,
                            ).consume()
                            return True

                        session.execute_write(crear_oferta)
                    invalidar_cache_datos()
                    st.success(f"Oferta publicada con ID {oferta_id}.")
                    st.rerun()
                except Exception:
                    st.error("No se pudo publicar la oferta. Revisa la conexion y los requisitos elegidos.")

    elif pagina == "Postulaciones":
        postulaciones = _filas(
            """
            MATCH (:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)<-[r:POSTULA_A]-(u:Usuario)
            RETURN o.titulo AS oferta, u.nombre AS candidato,
                   u.perfil_profesional AS perfil, r.estado_proceso AS estado,
                   r.fecha_postulacion AS fecha
            ORDER BY oferta, fecha DESC
            """,
            id=empresa_id,
        )
        _mostrar(postulaciones, "Tus ofertas aun no tienen postulaciones.")

    elif pagina == "Mensajes":
        messages_ui.renderizar(cuenta)
