"""Portal de gestión de marca, proyectos, ofertas y postulaciones de empresa."""

from datetime import date
from html import escape
import uuid

import streamlit as st

from backend_core import messages_ui
from backend_core.auth import url_http_valida
from backend_core.portal_common import consultar, escribir, enviar_mensaje, ir_a


ESTADOS = ["aplicado", "en revisión", "entrevista", "aceptado", "rechazado"]
ESTADOS_FINALES = {"aceptado", "rechazado"}


def _perfil(empresa_id):
    filas = consultar("MATCH (e:Empresa {id: $id}) RETURN properties(e) AS perfil", id=empresa_id)
    return filas[0]["perfil"] if filas else None


def _equipo_empresa(empresa_id):
    equipo = consultar(
        """
        MATCH (u:Usuario)-[trabajo:TRABAJA_EN]->(e:Empresa {id: $id})
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        WITH u, trabajo, collect(DISTINCT c.id) AS cuentas
        OPTIONAL MATCH (u)-[participacion:PARTICIPA_EN]->(p:Proyecto)
        WITH u, trabajo, cuentas,
             collect(DISTINCT CASE WHEN p IS NULL THEN null ELSE
                 {id: p.id, nombre: p.nombre, rol: participacion.rol} END) AS proyectos
        OPTIONAL MATCH (u)-[:TRABAJO_EN_OFERTA]->(o:Oferta)<-[:PUBLICA]-(empresa:Empresa {id: $id})
        RETURN u.id AS id, u.nombre AS nombre,
               u.perfil_profesional AS perfil, trabajo.cargo AS cargo,
               coalesce(trabajo.es_actual, false) AS actual,
               trabajo.periodo AS periodo, head(cuentas) AS cuenta_id,
               proyectos, collect(DISTINCT o.titulo) AS ofertas
        ORDER BY actual DESC, nombre
        """,
        id=empresa_id,
    ) or []
    contrataciones_aceptadas = consultar(
        """
        MATCH (e:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)<-[postulacion:POSTULA_A]-(u:Usuario)
        WHERE toLower(trim(coalesce(postulacion.estado_proceso, ''))) = 'aceptado'
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        RETURN u.id AS id, u.nombre AS nombre, u.perfil_profesional AS perfil,
               o.titulo AS cargo, true AS actual,
               postulacion.fecha_postulacion AS periodo,
               head(collect(DISTINCT c.id)) AS cuenta_id,
               [] AS proyectos, collect(DISTINCT o.titulo) AS ofertas
        ORDER BY nombre
        """,
        id=empresa_id,
    ) or []
    existentes = {persona["id"]: persona for persona in equipo}
    for persona in contrataciones_aceptadas:
        existente = existentes.get(persona["id"])
        if existente:
            existentes[persona["id"]]["ofertas"] = sorted(
                set((existente.get("ofertas") or []) + (persona.get("ofertas") or []))
            )
            existentes[persona["id"]]["actual"] = True
        else:
            existentes[persona["id"]] = persona
    return sorted(existentes.values(), key=lambda x: (not x.get("actual", False), str(x.get("nombre") or "").casefold()))


def _inicio(empresa_id, perfil):
    nombre = escape(str(perfil.get("nombre") or "empresa"))
    st.markdown(
        f"<section class='social-hero'><h1>Espacio de {nombre}</h1>"
        "<p>Presenta tu organización, publica proyectos y acompaña a cada candidato durante el proceso.</p></section>",
        unsafe_allow_html=True,
    )
    resumen = consultar(
        """
        MATCH (e:Empresa {id: $id})
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        WITH e, collect(DISTINCT o) AS ofertas
        OPTIONAL MATCH (e)-[:PUBLICA]->(:Oferta)<-[r:POSTULA_A]-(:Usuario)
        RETURN size(ofertas) AS total_ofertas,
               size([o IN ofertas WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta']) AS abiertas,
               count(r) AS postulaciones
        """,
        id=empresa_id,
    )
    datos = resumen[0] if resumen else {"total_ofertas": 0, "abiertas": 0, "postulaciones": 0}
    empleados = _equipo_empresa(empresa_id)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ofertas", datos["total_ofertas"])
    c2.metric("Abiertas", datos["abiertas"])
    c3.metric("Postulaciones recibidas", datos["postulaciones"])
    c4.metric("Personas vinculadas", len(empleados))

    principal, lateral = st.columns([2, 1], gap="large")
    with principal:
        with st.container(border=True):
            st.markdown("#### Perfil de empresa")
            st.markdown(f"**{escape(str(perfil.get('sector') or 'Sector por definir'))}**")
            st.write(perfil.get("descripcion") or "Añade una descripción para contar qué hace tu organización y qué tipo de talento busca.")
            st.caption(" · ".join(x for x in [perfil.get("ubicacion"), perfil.get("tamano")] if x))
            if st.button("Editar perfil de empresa", key="empresa_inicio_editar"):
                ir_a("Mi empresa")

        recientes = consultar(
            """
            MATCH (e:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)<-[r:POSTULA_A]-(u:Usuario)
            RETURN o.titulo AS oferta, u.nombre AS candidato,
                   u.perfil_profesional AS perfil, r.estado_proceso AS estado,
                   r.fecha_postulacion AS fecha
            ORDER BY fecha DESC
            LIMIT 5
            """,
            id=empresa_id,
        ) or []
        st.markdown("#### Actividad reciente")
        if not recientes:
            st.info("Cuando recibas postulaciones, verás aquí los movimientos recientes.")
        for fila in recientes:
            with st.container(border=True):
                st.markdown(f"**{fila['candidato']}** · {fila.get('perfil') or 'Profesional'}")
                st.caption(f"Se postuló a {fila['oferta']} · {fila.get('estado') or 'aplicado'} · {fila.get('fecha') or ''}")
        if st.button("Revisar postulaciones", key="empresa_inicio_postulaciones"):
            ir_a("Postulaciones")

        st.markdown("#### Equipo de la organización")
        if empleados:
            for empleado in empleados[:6]:
                proyectos = [p for p in (empleado.get("proyectos") or []) if p and p.get("nombre")]
                with st.container(border=True):
                    st.markdown(f"**{escape(str(empleado.get('nombre') or 'Profesional'))}** · {escape(str(empleado.get('cargo') or empleado.get('perfil') or 'Colaborador'))}")
                    st.caption(" · ".join(x for x in ["Actual" if empleado.get("actual") else "Anterior", empleado.get("periodo")] if x))
                    if proyectos:
                        st.caption("Proyectos: " + " · ".join(p["nombre"] for p in proyectos[:4]))
            if len(empleados) > 6:
                st.caption(f"Y {len(empleados) - 6} personas más en el equipo.")
        else:
            st.info("Aún no hay experiencias laborales verificadas para mostrar.")
        if st.button("Ver el equipo completo", key="empresa_inicio_equipo"):
            ir_a("Mi empresa")

    with lateral:
        candidatos = consultar(
            """
            MATCH (e:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
            WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
            MATCH (u:Usuario)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:REQUIERE]-(o)
            WHERE NOT EXISTS { MATCH (u)-[:POSTULA_A]->(o) }
            WITH u, count(DISTINCT h) AS coincidencias,
                 collect(DISTINCT o.titulo) AS ofertas
            RETURN u.nombre AS candidato, u.perfil_profesional AS perfil,
                   coincidencias, ofertas
            ORDER BY coincidencias DESC, candidato
            LIMIT 5
            """,
            id=empresa_id,
        ) or []
        with st.container(border=True):
            st.markdown("#### Perfiles afines a tus vacantes")
            if not candidatos:
                st.caption("Al publicar ofertas con habilidades requeridas aparecerán candidatos afines.")
            for candidato in candidatos:
                st.markdown(f"**{candidato['candidato']}**")
                st.caption(f"{candidato.get('perfil') or 'Profesional'} · {candidato['coincidencias']} habilidades coincidentes")


def _mi_empresa(empresa_id, perfil):
    st.markdown("#### Perfil público de la organización")
    with st.container(border=True):
        st.markdown(f"## {escape(str(perfil.get('nombre') or 'Mi empresa'))}")
        st.markdown(f"**{escape(str(perfil.get('sector') or 'Sector por definir'))}**")
        st.write(perfil.get("descripcion") or "Todavía no se ha escrito una descripción.")
        datos_publicos = [perfil.get("ubicacion"), perfil.get("tamano")]
        if perfil.get("sitio_web") and url_http_valida(perfil.get("sitio_web")):
            datos_publicos.append(perfil.get("sitio_web"))
        st.caption(" · ".join(x for x in datos_publicos if x))
    with st.form("empresa_editar_perfil"):
        nombre = st.text_input("Nombre de la empresa", value=perfil.get("nombre", ""), max_chars=140)
        sector = st.text_input("Sector", value=perfil.get("sector", ""), max_chars=120)
        descripcion = st.text_area("Descripción pública", value=perfil.get("descripcion", ""), max_chars=1200, height=140)
        ubicacion = st.text_input("Ciudad o ubicación", value=perfil.get("ubicacion", ""), max_chars=120)
        tamano = st.selectbox(
            "Tamaño de la organización",
            ["Sin especificar", "1–10 personas", "11–50 personas", "51–200 personas", "201–1000 personas", "Más de 1000 personas"],
            index=["Sin especificar", "1–10 personas", "11–50 personas", "51–200 personas", "201–1000 personas", "Más de 1000 personas"].index(perfil.get("tamano")) if perfil.get("tamano") in ["Sin especificar", "1–10 personas", "11–50 personas", "51–200 personas", "201–1000 personas", "Más de 1000 personas"] else 0,
        )
        sitio = st.text_input("Sitio web", value=perfil.get("sitio_web", ""), max_chars=240, placeholder="https://...")
        guardar = st.form_submit_button("Guardar perfil de empresa", width="stretch")
    if guardar:
        if not nombre.strip() or not sector.strip():
            st.warning("El nombre y el sector son obligatorios.")
        elif not url_http_valida(sitio):
            st.warning("Escribe un enlace completo que comience con http:// o https:// y tenga un dominio válido.")
        else:
            resultado = escribir(
                """
                MATCH (e:Empresa {id: $id})
                SET e.nombre = $nombre, e.sector = $sector,
                    e.descripcion = $descripcion, e.ubicacion = $ubicacion,
                    e.tamano = $tamano, e.sitio_web = $sitio
                RETURN e.id AS id
                """,
                id=empresa_id, nombre=nombre.strip(), sector=sector.strip(),
                descripcion=descripcion.strip(), ubicacion=ubicacion.strip(),
                tamano="" if tamano == "Sin especificar" else tamano,
                sitio=sitio.strip(),
            )
            if resultado:
                st.success("El perfil público de la empresa se actualizó.")
                st.rerun()

    st.markdown("#### Personas que trabajan o han trabajado aquí")
    empleados = _equipo_empresa(empresa_id)
    if not empleados:
        st.info("Todavía no hay experiencias laborales aprobadas para esta organización.")
    for empleado in empleados:
        with st.container(border=True):
            st.markdown(f"**{escape(str(empleado.get('nombre') or 'Profesional'))}** · {escape(str(empleado.get('cargo') or empleado.get('perfil') or 'Colaborador'))}")
            st.caption(" · ".join(x for x in ["Actualmente" if empleado.get("actual") else "Anteriormente", empleado.get("periodo"), empleado.get("perfil")] if x))
            proyectos = [p for p in (empleado.get("proyectos") or []) if p and p.get("nombre")]
            ofertas = [o for o in (empleado.get("ofertas") or []) if o]
            if proyectos:
                st.write("Proyectos: " + " · ".join(p["nombre"] for p in proyectos))
            if ofertas:
                st.caption("Ingresó por: " + " · ".join(ofertas))
            if empleado.get("cuenta_id") and st.button("Escribir", key=f"mensaje_empleado_{empresa_id}_{empleado['id']}"):
                enviar_mensaje(empleado["cuenta_id"])


def _proyectos_empresa(empresa_id):
    return consultar(
        """
        MATCH (e:Empresa {id: $id})
        OPTIONAL MATCH (e)-[:PUBLICA_PROYECTO]->(directo:Proyecto)
        OPTIONAL MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(por_oferta:Proyecto)
        WITH e, [p IN collect(DISTINCT directo) + collect(DISTINCT por_oferta)
                 WHERE p IS NOT NULL] AS posibles
        UNWIND posibles AS p
        WITH DISTINCT e, p
        CALL {
            WITH e, p
            OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)-[:PERTENECE_A]->(p)
            RETURN count(DISTINCT o) AS ofertas,
                   collect(DISTINCT o.titulo) AS ofertas_titulos
        }
        CALL {
            WITH p
            OPTIONAL MATCH (u:Usuario)-[r:PARTICIPA_EN]->(p)
            RETURN collect(DISTINCT CASE WHEN u IS NULL THEN null ELSE
                {id: u.id, nombre: u.nombre, perfil: u.perfil_profesional,
                 rol: r.rol, estado: r.estado} END) AS equipo
        }
        RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion,
               ofertas, ofertas_titulos, equipo,
               size([persona IN equipo WHERE persona.id IS NOT NULL]) AS participantes
        ORDER BY nombre
        """,
        id=empresa_id,
    ) or []


def _ofertas_empresa(empresa_id):
    return consultar(
        """
        MATCH (:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
        OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
        CALL {
            WITH o
            OPTIONAL MATCH (o)<-[r:POSTULA_A]-(:Usuario)
            RETURN count(DISTINCT r) AS postulaciones
        }
        CALL {
            WITH o
            OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
            RETURN collect(DISTINCT h.nombre) AS habilidades
        }
        CALL {
            WITH o
            OPTIONAL MATCH (u:Usuario)-[:TRABAJO_EN_OFERTA]->(o)
            RETURN collect(DISTINCT u.nombre) AS contrataciones_registradas
        }
        CALL {
            WITH o
            OPTIONAL MATCH (u:Usuario)-[r:POSTULA_A]->(o)
            WHERE toLower(trim(coalesce(r.estado_proceso, ''))) = 'aceptado'
            RETURN collect(DISTINCT u.nombre) AS postulaciones_aceptadas
        }
        RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
               o.estado AS estado, o.modalidad AS modalidad,
               o.nivel_experiencia AS experiencia, p.id AS proyecto_id,
               p.nombre AS proyecto, p.descripcion AS proyecto_descripcion,
               postulaciones, habilidades,
               contrataciones_registradas + postulaciones_aceptadas AS personas_contratadas
        ORDER BY titulo
        """,
        id=empresa_id,
    ) or []


def _crear_proyecto(empresa_id):
    with st.form("empresa_nuevo_proyecto", clear_on_submit=True):
        nombre = st.text_input("Nombre del proyecto", max_chars=140)
        descripcion = st.text_area("Qué busca resolver o construir", max_chars=1000, height=100)
        crear = st.form_submit_button("Crear proyecto")
    if not crear:
        return
    if not nombre.strip() or not descripcion.strip():
        st.warning("Completa el nombre y la descripción del proyecto.")
        return
    proyecto_id = "P" + uuid.uuid4().hex[:10].upper()
    resultado = escribir(
        """
        MATCH (e:Empresa {id: $empresa})
        CREATE (p:Proyecto {id: $id, nombre: $nombre, descripcion: $descripcion,
                            fecha_creacion: $fecha})
        CREATE (e)-[:PUBLICA_PROYECTO]->(p)
        RETURN p.id AS id
        """,
        empresa=empresa_id, id=proyecto_id, nombre=nombre.strip(),
        descripcion=descripcion.strip(), fecha=date.today().isoformat(),
    )
    if resultado:
        st.success("Proyecto creado. Ya puedes asociarle ofertas.")
        st.rerun()


def _crear_oferta(empresa_id, proyectos):
    habilidades = consultar("MATCH (h:Habilidad) RETURN h.id AS id, h.nombre AS nombre ORDER BY nombre") or []
    nombres_h = {h["id"]: h["nombre"] for h in habilidades}
    nombres_p = {p["id"]: p["nombre"] for p in proyectos}
    with st.form("empresa_nueva_oferta", clear_on_submit=True):
        titulo = st.text_input("Título de la oferta", max_chars=160)
        descripcion = st.text_area("Descripción del cargo y responsabilidades", max_chars=1800, height=130)
        modalidad = st.selectbox("Modalidad", ["remoto", "híbrido", "presencial"])
        experiencia = st.selectbox("Nivel de experiencia", ["Junior", "Semi-Senior", "Senior"])
        proyecto_id = st.selectbox("Proyecto al que pertenece", [""] + list(nombres_p), format_func=lambda x: "Sin proyecto" if not x else nombres_p[x])
        habilidades_id = st.multiselect("Habilidades requeridas", list(nombres_h), format_func=lambda x: nombres_h[x])
        publicar = st.form_submit_button("Publicar oferta", width="stretch")
    if not publicar:
        return
    if not titulo.strip() or not descripcion.strip():
        st.warning("Escribe un título y una descripción para la vacante.")
        return
    oferta_id = "O" + uuid.uuid4().hex[:10].upper()
    resultado = escribir(
        """
        MATCH (e:Empresa {id: $empresa})
        OPTIONAL MATCH (e)-[:PUBLICA_PROYECTO]->(directo:Proyecto {id: $proyecto})
        OPTIONAL MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(por_oferta:Proyecto {id: $proyecto})
        WITH e, coalesce(directo, por_oferta) AS p
        WHERE $proyecto = '__sin_proyecto__' OR p IS NOT NULL
        CREATE (o:Oferta {id: $id, titulo: $titulo, descripcion: $descripcion,
                          estado: 'abierta', modalidad: $modalidad,
                          nivel_experiencia: $experiencia})
        CREATE (e)-[:PUBLICA {fecha_publicacion: $fecha}]->(o)
        FOREACH (x IN CASE WHEN p IS NULL THEN [] ELSE [p] END |
            MERGE (e)-[:PUBLICA_PROYECTO]->(x)
            MERGE (o)-[:PERTENECE_A]->(x)
        )
        FOREACH (hid IN $habilidades |
            MERGE (o)-[:REQUIERE {es_obligatoria: true}]->(:Habilidad {id: hid})
        )
        RETURN o.id AS id
        """,
        empresa=empresa_id, proyecto=proyecto_id or "__sin_proyecto__",
        id=oferta_id, titulo=titulo.strip(), descripcion=descripcion.strip(),
        modalidad=modalidad, experiencia=experiencia,
        fecha=date.today().isoformat(), habilidades=habilidades_id,
    )
    if resultado:
        st.success("Oferta publicada y vinculada al proyecto seleccionado.")
        st.rerun()
    else:
        st.warning("La oferta no se publicó. Comprueba que el proyecto seleccionado siga vinculado a tu organización.")


def _gestion_proyectos_ofertas(empresa_id):
    tab_proyectos, tab_ofertas = st.tabs(["Proyectos", "Ofertas de empleo"])
    with tab_proyectos:
        proyectos = _proyectos_empresa(empresa_id)
        if proyectos:
            st.markdown("#### Proyectos de la organización")
            for p in proyectos:
                with st.container(border=True):
                    st.markdown(f"**{p['nombre']}**")
                    st.write(p.get("descripcion") or "Sin descripción")
                    st.caption(f"{p['ofertas']} ofertas · {p['participantes']} participantes")
                    titulos_oferta = [titulo for titulo in (p.get("ofertas_titulos") or []) if titulo]
                    if titulos_oferta:
                        st.caption("Ofertas: " + " · ".join(titulos_oferta))
                    equipo = [persona for persona in (p.get("equipo") or []) if persona and persona.get("nombre")]
                    if equipo:
                        st.caption("Equipo: " + " · ".join(
                            f"{persona['nombre']} · {persona.get('perfil') or 'Profesional'} ({persona.get('rol') or 'participante'})"
                            for persona in equipo
                        ))
                    with st.expander("Editar este proyecto"):
                        with st.form(f"form_editar_proyecto_{p['id']}"):
                            nombre_nuevo = st.text_input("Nombre", value=p["nombre"], max_chars=140)
                            descripcion_nueva = st.text_area("Descripción", value=p.get("descripcion") or "", max_chars=1000)
                            guardar_proyecto = st.form_submit_button("Guardar proyecto")
                        if guardar_proyecto:
                            if not nombre_nuevo.strip() or not descripcion_nueva.strip():
                                st.warning("El nombre y la descripción son obligatorios.")
                            else:
                                resultado = escribir(
                                    """
                                    MATCH (e:Empresa {id: $e}), (p:Proyecto {id: $p})
                                    WHERE EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
                                       OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) }
                                    SET p.nombre = $nombre, p.descripcion = $descripcion
                                    MERGE (e)-[:PUBLICA_PROYECTO]->(p)
                                    RETURN p.id AS id
                                    """,
                                    e=empresa_id, p=p["id"], nombre=nombre_nuevo.strip(),
                                    descripcion=descripcion_nueva.strip(),
                                )
                                if resultado:
                                    st.success("Proyecto actualizado.")
                                    st.rerun()
        else:
            st.info("Todavía no hay proyectos publicados por esta empresa.")
        st.caption("Los proyectos históricos sin organización asignada deben ser vinculados por administración para evitar atribuirlos a una empresa equivocada.")
        st.markdown("#### Crear proyecto")
        _crear_proyecto(empresa_id)

    with tab_ofertas:
        proyectos = _proyectos_empresa(empresa_id)
        ofertas = _ofertas_empresa(empresa_id)
        st.markdown("#### Tus ofertas")
        if ofertas:
            for oferta in ofertas:
                with st.container(border=True):
                    st.markdown(f"**{oferta['titulo']}** · {oferta.get('estado') or 'sin estado'}")
                    st.caption(f"{oferta.get('modalidad') or ''} · {oferta.get('experiencia') or ''} · {oferta['postulaciones']} postulaciones")
                    if oferta.get("proyecto"):
                        st.caption(f"Proyecto: {oferta['proyecto']}")
                        if oferta.get("proyecto_descripcion"):
                            st.write(oferta["proyecto_descripcion"])
                    if oferta.get("descripcion"):
                        st.write(oferta["descripcion"])
                    if oferta.get("habilidades"):
                        st.caption("Habilidades: " + " · ".join(x for x in oferta["habilidades"] if x))
                    contratados = [x for x in (oferta.get("personas_contratadas") or []) if x]
                    st.caption("Ingresaron por esta oferta: " + (", ".join(dict.fromkeys(contratados)) if contratados else "Ninguna persona todavía"))
                    if oferta["postulaciones"] and st.button(
                        "Revisar postulaciones",
                        key=f"revisar_oferta_{oferta['id']}",
                    ):
                        st.session_state["empresa_postulacion_oferta"] = oferta["id"]
                        ir_a("Postulaciones")
                    nueva = "cerrada" if str(oferta.get("estado", "")).casefold() == "abierta" else "abierta"
                    accion = "Cerrar oferta" if nueva == "cerrada" else "Reabrir oferta"
                    if st.button(accion, key=f"oferta_estado_{oferta['id']}"):
                        actualizada = escribir(
                            "MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o}) SET o.estado = $estado RETURN o.id AS id",
                            e=empresa_id, o=oferta["id"], estado=nueva,
                        )
                        if actualizada:
                            st.success(f"Oferta {nueva}.")
                            st.rerun()
                        st.warning("No se pudo actualizar la oferta; revisa si aún pertenece a tu organización.")
        else:
            st.info("Publica una oferta para que los profesionales puedan encontrarla y postularse.")
        if ofertas:
            st.markdown("#### Editar una oferta")
            opciones_o = {o["id"]: o["titulo"] for o in ofertas}
            oferta_id = st.selectbox("Oferta", list(opciones_o), format_func=lambda x: opciones_o[x], key="empresa_editar_oferta_id")
            oferta_actual = next(o for o in ofertas if o["id"] == oferta_id)
            with st.form(f"form_editar_oferta_{oferta_id}"):
                titulo = st.text_input("Título", value=oferta_actual.get("titulo") or "", max_chars=160)
                descripcion = st.text_area("Descripción", value=oferta_actual.get("descripcion") or "", max_chars=1800, height=120)
                modalidad = st.selectbox("Modalidad", ["remoto", "híbrido", "presencial"], index=["remoto", "híbrido", "presencial"].index(oferta_actual["modalidad"]) if oferta_actual.get("modalidad") in ["remoto", "híbrido", "presencial"] else 0)
                experiencia_opciones = ["Junior", "Semi-Senior", "Senior"]
                experiencia = st.selectbox("Experiencia", experiencia_opciones, index=experiencia_opciones.index(oferta_actual["experiencia"]) if oferta_actual.get("experiencia") in experiencia_opciones else 0)
                opciones_proyecto = {"": "Sin proyecto"} | {p["id"]: p["nombre"] for p in proyectos}
                proyecto_actual = oferta_actual.get("proyecto_id") or ""
                if proyecto_actual and proyecto_actual not in opciones_proyecto:
                    opciones_proyecto[proyecto_actual] = oferta_actual.get("proyecto") or "Proyecto actual"
                proyecto_nuevo = st.selectbox(
                    "Proyecto relacionado",
                    list(opciones_proyecto),
                    index=list(opciones_proyecto).index(proyecto_actual) if proyecto_actual in opciones_proyecto else 0,
                    format_func=lambda x: opciones_proyecto[x],
                    key=f"oferta_proyecto_{oferta_id}",
                )
                guardar = st.form_submit_button("Guardar cambios")
            if guardar:
                if not titulo.strip() or not descripcion.strip():
                    st.warning("El título y la descripción son obligatorios.")
                else:
                    resultado = escribir(
                        """
                        MATCH (e:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})
                        SET o.titulo = $titulo, o.descripcion = $descripcion,
                            o.modalidad = $modalidad, o.nivel_experiencia = $experiencia
                        WITH e, o
                        OPTIONAL MATCH (o)-[anterior:PERTENECE_A]->(:Proyecto)
                        FOREACH (rel IN CASE WHEN anterior IS NULL THEN [] ELSE [anterior] END | DELETE rel)
                        WITH e, o
                        OPTIONAL MATCH (e)-[:PUBLICA_PROYECTO]->(directo:Proyecto {id: $proyecto})
                        OPTIONAL MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(vinculado:Proyecto {id: $proyecto})
                        WITH e, o, coalesce(directo, vinculado) AS p
                        FOREACH (x IN CASE WHEN p IS NULL THEN [] ELSE [p] END |
                            MERGE (e)-[:PUBLICA_PROYECTO]->(x)
                            MERGE (o)-[:PERTENECE_A]->(x)
                        )
                        RETURN o.id AS id
                        """,
                        e=empresa_id, o=oferta_id, titulo=titulo.strip(),
                        descripcion=descripcion.strip(), modalidad=modalidad,
                        experiencia=experiencia, proyecto=proyecto_nuevo or "__sin_proyecto__",
                    )
                    if resultado:
                        st.success("Oferta actualizada.")
                        st.rerun()
        st.markdown("#### Publicar una oferta")
        if not proyectos:
            st.caption("Si quieres asociar una oferta a un proyecto, créalo primero en la pestaña Proyectos.")
        _crear_oferta(empresa_id, proyectos)


def _resolver_solicitud_trayectoria(empresa_id, usuario_id, objetivo_id, tipo, aceptar):
    estado = "aceptada" if aceptar else "rechazada"
    if tipo == "experiencia":
        consulta = """
            MATCH (u:Usuario {id: $u})-[s:SOLICITA_EXPERIENCIA]->(e:Empresa {id: $e})
            WHERE coalesce(s.estado_revision, 'pendiente') = 'pendiente'
            OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
            WHERE o.id = s.oferta_id
            SET s.estado_revision = $estado, s.fecha_revision = $fecha
            FOREACH (_ IN CASE WHEN $estado = 'aceptada' THEN [1] ELSE [] END |
                MERGE (u)-[trabajo:TRABAJA_EN]->(e)
                SET trabajo.cargo = coalesce(trabajo.cargo, s.cargo),
                    trabajo.periodo = coalesce(trabajo.periodo, s.periodo),
                    trabajo.descripcion = coalesce(trabajo.descripcion, s.descripcion),
                    trabajo.es_actual = s.es_actual,
                    trabajo.validada_por_empresa = true,
                    trabajo.fecha_validacion = $fecha
            )
            FOREACH (_ IN CASE WHEN $estado = 'aceptada' AND o IS NOT NULL THEN [1] ELSE [] END |
                MERGE (u)-[referencia:TRABAJO_EN_OFERTA]->(o)
                SET referencia.cargo = s.cargo,
                    referencia.fecha_validacion = $fecha
            )
            RETURN s.id AS id
        """
    else:
        consulta = """
            MATCH (u:Usuario {id: $u})-[s:SOLICITA_PARTICIPACION]->(p:Proyecto {id: $objetivo})
            MATCH (e:Empresa {id: $e})
            WHERE coalesce(s.estado_revision, 'pendiente') = 'pendiente'
              AND coalesce(s.empresa_id, $e) = $e
              AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
                   OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
            SET s.estado_revision = $estado, s.fecha_revision = $fecha
            FOREACH (_ IN CASE WHEN $estado = 'aceptada' THEN [1] ELSE [] END |
                MERGE (u)-[participacion:PARTICIPA_EN]->(p)
                SET participacion.rol = s.rol,
                    participacion.estado = s.estado_participacion,
                    participacion.validada_por_empresa = true,
                    participacion.fecha_validacion = $fecha
            )
            RETURN s.id AS id
        """
    parametros = {
        "e": empresa_id,
        "u": usuario_id,
        "estado": estado,
        "fecha": date.today().isoformat(),
    }
    if tipo == "proyecto":
        parametros["objetivo"] = objetivo_id
    resultado = escribir(consulta, **parametros)
    return bool(resultado)


def _solicitudes_trayectoria(empresa_id):
    st.markdown("#### Validar experiencia profesional")
    experiencia = consultar(
        """
        MATCH (u:Usuario)-[r:SOLICITA_EXPERIENCIA]->(e:Empresa {id: $e})
        WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente'
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        RETURN u.id AS usuario_id, u.nombre AS nombre,
               u.perfil_profesional AS perfil, u.universidad AS universidad,
               head(collect(DISTINCT c.id)) AS cuenta_id,
               r.id AS solicitud_id, r.cargo AS cargo, r.periodo AS periodo,
               r.descripcion AS descripcion, r.es_actual AS es_actual,
               r.oferta_id AS oferta_id, r.fecha_solicitud AS fecha
        ORDER BY fecha DESC, nombre
        """,
        e=empresa_id,
    ) or []
    if not experiencia:
        st.info("No hay solicitudes pendientes para validar empleos.")
    for solicitud in experiencia:
        with st.container(border=True):
            st.markdown(f"**{escape(str(solicitud.get('nombre') or 'Profesional'))}** · {escape(str(solicitud.get('cargo') or 'Cargo por verificar'))}")
            st.caption(" · ".join(x for x in [solicitud.get("perfil"), solicitud.get("universidad"), solicitud.get("periodo"), solicitud.get("fecha")] if x))
            if solicitud.get("descripcion"):
                st.write(solicitud["descripcion"])
            oferta = consultar(
                "MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o}) RETURN o.titulo AS titulo",
                e=empresa_id, o=solicitud.get("oferta_id") or "__sin_oferta__",
            ) if solicitud.get("oferta_id") else []
            if oferta:
                st.caption(f"Oferta de referencia: {oferta[0]['titulo']}")
            a, b, c = st.columns([1, 1, 2])
            if a.button("Aprobar experiencia", key=f"aprobar_experiencia_{solicitud['usuario_id']}"):
                if _resolver_solicitud_trayectoria(empresa_id, solicitud["usuario_id"], None, "experiencia", True):
                    st.success("La experiencia fue validada y agregada al vínculo laboral.")
                    st.rerun()
            if b.button("Rechazar", key=f"rechazar_experiencia_{solicitud['usuario_id']}"):
                if _resolver_solicitud_trayectoria(empresa_id, solicitud["usuario_id"], None, "experiencia", False):
                    st.info("La solicitud fue rechazada.")
                    st.rerun()
            if solicitud.get("cuenta_id") and c.button("Escribir a la persona", key=f"mensaje_solicitud_experiencia_{solicitud['usuario_id']}"):
                enviar_mensaje(solicitud["cuenta_id"])

    st.markdown("#### Validar participación en proyectos")
    proyectos = consultar(
        """
        MATCH (u:Usuario)-[r:SOLICITA_PARTICIPACION]->(p:Proyecto)
        MATCH (e:Empresa {id: $e})
        WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente'
          AND coalesce(r.empresa_id, $e) = $e
          AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
               OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        RETURN u.id AS usuario_id, u.nombre AS nombre,
               u.perfil_profesional AS perfil, head(collect(DISTINCT c.id)) AS cuenta_id,
               p.id AS proyecto_id, p.nombre AS proyecto,
               r.rol AS rol, r.estado_participacion AS estado,
               r.fecha_solicitud AS fecha
        ORDER BY fecha DESC, nombre
        """,
        e=empresa_id,
    ) or []
    if not proyectos:
        st.info("No hay solicitudes pendientes para validar proyectos.")
    for solicitud in proyectos:
        with st.container(border=True):
            st.markdown(f"**{escape(str(solicitud.get('nombre') or 'Profesional'))}** quiere añadir **{escape(str(solicitud.get('proyecto') or 'un proyecto'))}** a su trayectoria.")
            st.caption(" · ".join(x for x in [solicitud.get("perfil"), solicitud.get("rol"), solicitud.get("estado"), solicitud.get("fecha")] if x))
            a, b, c = st.columns([1, 1, 2])
            if a.button("Aprobar proyecto", key=f"aprobar_proyecto_{solicitud['usuario_id']}_{solicitud['proyecto_id']}"):
                if _resolver_solicitud_trayectoria(empresa_id, solicitud["usuario_id"], solicitud["proyecto_id"], "proyecto", True):
                    st.success("La participación en el proyecto fue validada.")
                    st.rerun()
            if b.button("Rechazar", key=f"rechazar_proyecto_{solicitud['usuario_id']}_{solicitud['proyecto_id']}"):
                if _resolver_solicitud_trayectoria(empresa_id, solicitud["usuario_id"], solicitud["proyecto_id"], "proyecto", False):
                    st.info("La solicitud fue rechazada.")
                    st.rerun()
            if solicitud.get("cuenta_id") and c.button("Escribir a la persona", key=f"mensaje_solicitud_proyecto_{solicitud['usuario_id']}_{solicitud['proyecto_id']}"):
                enviar_mensaje(solicitud["cuenta_id"])


def _postulaciones(empresa_id):
    ofertas = _ofertas_empresa(empresa_id)
    ofertas_con_candidatos = [o for o in ofertas if o["postulaciones"] > 0]
    candidatos = []
    oferta_actual = None
    if ofertas_con_candidatos:
        opciones = {
            o["id"]: f"{o['titulo']} · {o['postulaciones']} candidaturas"
            for o in ofertas_con_candidatos
        }
        sugerida = st.session_state.get("empresa_postulacion_oferta")
        ids = list(opciones)
        if sugerida not in ids:
            st.session_state.pop("empresa_postulacion_oferta", None)
            sugerida = None
        seleccionada = sugerida if sugerida in ids else ids[0]
        oferta_id = st.selectbox(
            "Oferta de empleo",
            ids,
            index=ids.index(seleccionada),
            format_func=lambda x: opciones[x],
            key="empresa_postulacion_oferta",
        )
        oferta_actual = next(o for o in ofertas_con_candidatos if o["id"] == oferta_id)
        with st.container(border=True):
            st.markdown(f"### {escape(str(oferta_actual['titulo']))}")
            st.caption(" · ".join(x for x in [oferta_actual.get("proyecto"), oferta_actual.get("modalidad"), oferta_actual.get("experiencia"), f"{oferta_actual['postulaciones']} postulaciones"] if x))
            if oferta_actual.get("proyecto_descripcion"):
                st.write(oferta_actual["proyecto_descripcion"])
            if oferta_actual.get("descripcion"):
                st.write(oferta_actual["descripcion"])
            if oferta_actual.get("habilidades"):
                st.caption("Habilidades requeridas: " + " · ".join(x for x in oferta_actual["habilidades"] if x))
        candidatos = consultar(
            """
            MATCH (e:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})<-[r:POSTULA_A]-(u:Usuario)
            CALL {
                WITH u
                OPTIONAL MATCH (u)-[rel:TIENE_HABILIDAD]->(h:Habilidad)
                RETURN collect(DISTINCT CASE WHEN h IS NULL THEN null ELSE
                    {nombre: h.nombre, nivel: rel.nivel_dominio} END) AS habilidades
            }
            CALL {
                WITH u
                OPTIONAL MATCH (u)-[rel:PARTICIPA_EN]->(p:Proyecto)
                RETURN collect(DISTINCT CASE WHEN p IS NULL THEN null ELSE
                    {nombre: p.nombre, rol: rel.rol, estado: rel.estado} END) AS proyectos
            }
            CALL {
                WITH u
                OPTIONAL MATCH (u)-[rel:TRABAJA_EN]->(empresa:Empresa)
                RETURN collect(DISTINCT CASE WHEN empresa IS NULL THEN null ELSE
                    {nombre: empresa.nombre, cargo: rel.cargo, actual: rel.es_actual} END) AS experiencia
            }
            OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
            WHERE coalesce(c.activa, true) = true
            WITH o, u, r, habilidades, proyectos, experiencia,
                 collect(DISTINCT c.id) AS cuentas
            RETURN u.id AS id, properties(u) AS perfil_completo,
                   u.nombre AS nombre, u.perfil_profesional AS perfil,
                   u.universidad AS universidad, u.ubicacion AS ubicacion,
                   u.acerca_de AS acerca, head(cuentas) AS cuenta_id,
                   r.estado_proceso AS estado, r.fecha_postulacion AS fecha,
                   habilidades, proyectos, experiencia
            ORDER BY fecha DESC, nombre
            """,
            e=empresa_id, o=oferta_id,
        ) or []

    en_proceso = [c for c in candidatos if str(c.get("estado") or "aplicado").casefold() not in ESTADOS_FINALES]
    resueltas = [c for c in candidatos if str(c.get("estado") or "aplicado").casefold() in ESTADOS_FINALES]
    tab_activas, tab_historial, tab_verificaciones = st.tabs(
        ["En proceso", "Aceptadas y rechazadas", "Validar trayectoria"]
    )
    with tab_activas:
        if not ofertas_con_candidatos:
            st.info("Aún no hay postulaciones en tus ofertas.")
        elif not en_proceso:
            st.success("No hay candidaturas pendientes para esta oferta.")
        for candidato in en_proceso:
            with st.container(border=True):
                st.markdown(f"### {escape(str(candidato.get('nombre') or 'Profesional'))}")
                st.markdown(f"**{escape(str(candidato.get('perfil') or 'Profesional'))}**")
                st.caption(" · ".join(x for x in [candidato.get("universidad"), candidato.get("ubicacion"), candidato.get("fecha")] if x))
                if candidato.get("acerca"):
                    st.write(candidato["acerca"])
                habilidades = [h for h in (candidato.get("habilidades") or []) if h and h.get("nombre")]
                if habilidades:
                    st.caption("Habilidades: " + " · ".join(f"{h['nombre']} ({h.get('nivel') or 'sin nivel'})" for h in habilidades))
                with st.expander("Ver perfil y trayectoria completos"):
                    perfil_completo = candidato.get("perfil_completo") or {}
                    for etiqueta, propiedad in [
                        ("Presentación", "acerca_de"), ("Formación", "educacion_detalle"),
                        ("Áreas de interés", "areas_interes"), ("Experiencia", "experiencia"),
                        ("Logros", "logros"), ("Idiomas", "idiomas"),
                        ("Portafolio", "sitio_portafolio"),
                    ]:
                        valor = perfil_completo.get(propiedad)
                        if valor:
                            st.markdown(f"**{etiqueta}:** {escape(str(valor))}")
                    proyectos_perfil = [p for p in (candidato.get("proyectos") or []) if p and p.get("nombre")]
                    experiencias = [x for x in (candidato.get("experiencia") or []) if x and x.get("nombre")]
                    if proyectos_perfil:
                        st.markdown("**Proyectos**")
                        for proyecto in proyectos_perfil:
                            st.caption(f"{proyecto['nombre']} · {proyecto.get('rol') or 'Participante'} · {proyecto.get('estado') or ''}")
                    if experiencias:
                        st.markdown("**Experiencia laboral**")
                        for empleo in experiencias:
                            st.caption(f"{empleo['nombre']} · {empleo.get('cargo') or 'Cargo no indicado'} · {'actual' if empleo.get('actual') else 'anterior'}")
                estado_actual = str(candidato.get("estado") or "aplicado").casefold()
                if estado_actual == "entrevistado":
                    estado_actual = "entrevista"
                estado_nuevo = st.selectbox(
                    "Estado del proceso", ESTADOS,
                    index=ESTADOS.index(estado_actual) if estado_actual in ESTADOS else 0,
                    key=f"estado_postulacion_{oferta_id}_{candidato['id']}",
                )
                if st.button("Guardar estado", key=f"guardar_estado_{oferta_id}_{candidato['id']}"):
                    resultado = escribir(
                        """
                        MATCH (e:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o})<-[r:POSTULA_A]-(u:Usuario {id: $u})
                        SET r.estado_proceso = $estado
                        FOREACH (_ IN CASE WHEN $estado = 'aceptado' THEN [1] ELSE [] END |
                            MERGE (u)-[trabajo:TRABAJA_EN]->(e)
                            SET trabajo.cargo = coalesce(trabajo.cargo, o.titulo),
                                trabajo.es_actual = true,
                                trabajo.oferta_id = o.id,
                                trabajo.fecha_inicio = coalesce(trabajo.fecha_inicio, $fecha),
                                trabajo.validada_por_empresa = true,
                                trabajo.fecha_validacion = $fecha
                            MERGE (u)-[contratacion:TRABAJO_EN_OFERTA]->(o)
                            SET contratacion.cargo = o.titulo,
                                contratacion.fecha = $fecha
                        )
                        RETURN r.estado_proceso AS estado
                        """,
                        e=empresa_id, o=oferta_id, u=candidato["id"],
                        estado=estado_nuevo, fecha=date.today().isoformat(),
                    )
                    if resultado:
                        st.success("La candidatura se actualizó.")
                        if estado_nuevo == "aceptado":
                            st.info("La persona fue agregada al equipo y a la oferta como contratación verificada.")
                        st.rerun()
                if candidato.get("cuenta_id") and st.button("Escribir al candidato", key=f"mensaje_candidato_{oferta_id}_{candidato['id']}"):
                    enviar_mensaje(candidato["cuenta_id"])
    with tab_historial:
        if not resueltas:
            st.info("Las candidaturas aceptadas o rechazadas aparecerán aquí, fuera de la lista activa.")
        for candidato in resueltas:
            estado = str(candidato.get("estado") or "").casefold()
            nombre_estado = "Aceptada" if estado == "aceptado" else "Rechazada"
            with st.container(border=True):
                st.markdown(f"**{escape(str(candidato.get('nombre') or 'Profesional'))}** · {nombre_estado}")
                st.caption(" · ".join(x for x in [candidato.get("perfil"), candidato.get("universidad"), candidato.get("fecha")] if x))
                if candidato.get("acerca"):
                    st.write(candidato["acerca"])
                if candidato.get("cuenta_id") and st.button("Escribir", key=f"mensaje_historial_{oferta_id}_{candidato['id']}"):
                    enviar_mensaje(candidato["cuenta_id"])
    with tab_verificaciones:
        _solicitudes_trayectoria(empresa_id)


def renderizar(cuenta, pagina):
    empresa_id = cuenta.get("entidad_id")
    if not empresa_id:
        st.error("La cuenta no tiene una empresa asociada.")
        return
    perfil = _perfil(empresa_id)
    if perfil is None:
        st.error("No se encontró el perfil de la empresa en Neo4j Aura.")
        return
    if pagina == "Inicio":
        _inicio(empresa_id, perfil)
    elif pagina == "Mi empresa":
        _mi_empresa(empresa_id, perfil)
    elif pagina == "Proyectos y ofertas":
        _gestion_proyectos_ofertas(empresa_id)
    elif pagina == "Postulaciones":
        _postulaciones(empresa_id)
    elif pagina == "Mensajes":
        messages_ui.renderizar(cuenta)
