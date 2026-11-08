"""Experiencia de red profesional para cuentas de usuario."""

from datetime import date
from html import escape
import uuid

import streamlit as st

from backend_core import messages_ui
from backend_core.auth import url_http_valida
from backend_core.connection import get_db_connection
from backend_core.portal_common import consultar, escribir, enviar_mensaje, ir_a, tarjeta


RELACIONES_RUTA = (
    "CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|"
    "POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A"
)
ESTADOS_POSTULACION = ["aplicado", "en revisión", "entrevista", "aceptado", "rechazado"]


def _perfil_usuario(usuario_id):
    filas = consultar(
        """
        MATCH (u:Usuario {id: $id})
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(u)
        WHERE coalesce(c.activa, true) = true
        RETURN properties(u) AS perfil, c.id AS cuenta_id
        LIMIT 1
        """,
        id=usuario_id,
    )
    return filas[0] if filas else None


def _habilidades(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:TIENE_HABILIDAD]->(h:Habilidad)
        RETURN h.id AS id, h.nombre AS habilidad, h.categoria AS categoria,
               r.nivel_dominio AS nivel
        ORDER BY habilidad
        """,
        id=usuario_id,
    ) or []


def _experiencia(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:TRABAJA_EN]->(e:Empresa)
        RETURN e.id AS id, e.nombre AS empresa, e.sector AS sector,
               r.cargo AS cargo, coalesce(r.es_actual, false) AS actual,
               r.periodo AS periodo, r.descripcion AS descripcion
        ORDER BY actual DESC, empresa
        """,
        id=usuario_id,
    ) or []


def _proyectos_usuario(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:PARTICIPA_EN]->(p:Proyecto)
        RETURN p.id AS id, p.nombre AS proyecto, p.descripcion AS descripcion,
               r.rol AS rol, coalesce(r.estado, 'en curso') AS estado
        ORDER BY proyecto
        """,
        id=usuario_id,
    ) or []


def _empresas_para_validar_experiencia(usuario_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $u}), (e:Empresa)
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        WHERE coalesce(c.activa, true) = true
          AND NOT EXISTS { MATCH (u)-[:TRABAJA_EN]->(e) }
          AND NOT EXISTS {
              MATCH (u)-[r:SOLICITA_EXPERIENCIA]->(e)
              WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente'
          }
        RETURN DISTINCT e.id AS id, e.nombre AS nombre, e.sector AS sector
        ORDER BY nombre
        """,
        u=usuario_id,
    ) or []


def _empresas_revisoras_proyecto(usuario_id, proyecto_id):
    return consultar(
        """
        MATCH (u:Usuario {id: $u}), (p:Proyecto {id: $p}), (e:Empresa)
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        WHERE coalesce(c.activa, true) = true
          AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
               OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
          AND NOT EXISTS { MATCH (u)-[:PARTICIPA_EN]->(p) }
          AND NOT EXISTS {
              MATCH (u)-[r:SOLICITA_PARTICIPACION]->(p)
              WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente'
          }
        RETURN DISTINCT e.id AS id, e.nombre AS nombre
        ORDER BY nombre
        """,
        u=usuario_id, p=proyecto_id,
    ) or []


def _solicitudes_trayectoria(usuario_id):
    experiencias = consultar(
        """
        MATCH (:Usuario {id: $u})-[r:SOLICITA_EXPERIENCIA]->(e:Empresa)
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        WHERE o.id = r.oferta_id
        RETURN r.id AS id, e.id AS empresa_id, e.nombre AS empresa,
               r.cargo AS cargo, r.periodo AS periodo, r.descripcion AS descripcion,
               r.estado_revision AS estado, r.fecha_solicitud AS fecha,
               o.titulo AS oferta
        ORDER BY fecha DESC
        """,
        u=usuario_id,
    ) or []
    proyectos = consultar(
        """
        MATCH (:Usuario {id: $u})-[r:SOLICITA_PARTICIPACION]->(p:Proyecto)
        OPTIONAL MATCH (e:Empresa)
        WHERE e.id = r.empresa_id
        RETURN r.id AS id, p.id AS proyecto_id, p.nombre AS proyecto,
               e.nombre AS empresa, r.rol AS rol,
               r.estado_participacion AS estado_participacion,
               r.estado_revision AS estado, r.fecha_solicitud AS fecha
        ORDER BY fecha DESC
        """,
        u=usuario_id,
    ) or []
    return experiencias, proyectos


def _gestionar_solicitudes_trayectoria(usuario_id):
    st.markdown("#### Estado de tus solicitudes")
    experiencias, proyectos = _solicitudes_trayectoria(usuario_id)
    if not experiencias and not proyectos:
        st.info("Todavía no has enviado solicitudes de verificación.")
        return
    etiquetas_estado = {
        "pendiente": "En revisión",
        "aceptada": "Aprobada",
        "rechazada": "Rechazada",
    }
    for solicitud in experiencias:
        estado = str(solicitud.get("estado") or "pendiente").casefold()
        with st.container(border=True):
            st.markdown(f"**Experiencia · {escape(str(solicitud.get('empresa') or 'Empresa'))}** · {etiquetas_estado.get(estado, estado.title())}")
            st.caption(" · ".join(x for x in [solicitud.get("cargo"), solicitud.get("periodo"), solicitud.get("oferta"), solicitud.get("fecha")] if x))
            if estado == "pendiente" and st.button("Cancelar solicitud", key=f"cancelar_experiencia_{solicitud['empresa_id']}"):
                if escribir(
                    "MATCH (:Usuario {id: $u})-[r:SOLICITA_EXPERIENCIA]->(:Empresa {id: $e}) WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente' DELETE r RETURN $e AS id",
                    u=usuario_id, e=solicitud["empresa_id"],
                ):
                    st.rerun()
    for solicitud in proyectos:
        estado = str(solicitud.get("estado") or "pendiente").casefold()
        with st.container(border=True):
            st.markdown(f"**Proyecto · {escape(str(solicitud.get('proyecto') or 'Proyecto'))}** · {etiquetas_estado.get(estado, estado.title())}")
            st.caption(" · ".join(x for x in [solicitud.get("empresa"), solicitud.get("rol"), solicitud.get("estado_participacion"), solicitud.get("fecha")] if x))
            if estado == "pendiente" and st.button("Cancelar solicitud", key=f"cancelar_proyecto_{solicitud['proyecto_id']}"):
                if escribir(
                    "MATCH (:Usuario {id: $u})-[r:SOLICITA_PARTICIPACION]->(:Proyecto {id: $p}) WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente' DELETE r RETURN $p AS id",
                    u=usuario_id, p=solicitud["proyecto_id"],
                ):
                    st.rerun()


def _iniciales(nombre):
    partes = [parte for parte in str(nombre or "").strip().split() if parte]
    return "".join(parte[0].upper() for parte in partes[:2]) or "DP"


def _tarjeta_perfil(perfil, titulo=""):
    nombre = str(perfil.get("nombre") or "Profesional")
    iniciales = escape(_iniciales(nombre))
    nombre_html = escape(nombre)
    titular = escape(str(perfil.get("perfil_profesional") or "Completa tu titular profesional"))
    ubicacion = escape(str(perfil.get("ubicacion") or "Añade tu ciudad o región"))
    universidad = escape(str(perfil.get("universidad") or "Añade tu formación"))
    st.markdown(
        f"""
        <section class="profile-banner">
          <div class="profile-banner-cover"></div>
          <div class="profile-banner-body">
            <div class="profile-avatar">{iniciales}</div>
            <div class="profile-banner-copy">
              <div class="profile-name">{nombre_html}</div>
              <div class="profile-headline">{titular}</div>
              <div class="profile-meta">{ubicacion} <span>·</span> {universidad}</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if titulo:
        st.caption(titulo)


def _completitud(perfil, habilidades, experiencia, proyectos):
    elementos = [
        ("Titular profesional", bool(str(perfil.get("perfil_profesional") or "").strip())),
        ("Acerca de", bool(str(perfil.get("acerca_de") or "").strip())),
        ("Ubicación", bool(str(perfil.get("ubicacion") or "").strip())),
        ("Formación", bool(str(perfil.get("educacion_detalle") or perfil.get("universidad") or "").strip())),
        ("Tres o más habilidades", len(habilidades) >= 3),
        ("Experiencia", bool(experiencia) or bool(str(perfil.get("experiencia") or "").strip())),
        ("Proyecto", bool(proyectos)),
        ("Intereses profesionales", bool(str(perfil.get("areas_interes") or "").strip())),
    ]
    completados = sum(1 for _, listo in elementos if listo)
    return round(completados * 100 / len(elementos)), [etiqueta for etiqueta, listo in elementos if not listo]


def _sugerencias(usuario_id):
    # Afinidad explicable: personas pondera contactos (20), habilidades (30),
    # proyectos (20), intereses (10), ciudad (10) y formación (10). Las otras
    # dos consultas ponderan encaje con ofertas/tecnologías, actividad y rutas.
    personas = consultar(
        """
        MATCH (yo:Usuario {id: $id})
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(p:Usuario)
        WHERE p <> yo AND coalesce(c.activa, true) = true
          AND NOT EXISTS { MATCH (yo)-[:CONECTA_CON]-(p) }
        OPTIONAL MATCH (yo)-[:CONECTA_CON]-(intermedio:Usuario)-[:CONECTA_CON]-(p)
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(p)
        OPTIONAL MATCH (yo)-[:PARTICIPA_EN]->(proyecto:Proyecto)<-[:PARTICIPA_EN]-(p)
        WITH yo, p, c, count(DISTINCT intermedio) AS contactos,
             collect(DISTINCT h.nombre) AS habilidades,
             count(DISTINCT proyecto) AS proyectos,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         toLower(coalesce(p.areas_interes, '')) CONTAINS trim(tema)]) AS temas
        RETURN p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil,
               p.ubicacion AS ubicacion, p.universidad AS universidad,
               (yo.ubicacion IS NOT NULL AND toLower(yo.ubicacion) = toLower(coalesce(p.ubicacion, ''))) AS misma_ciudad,
               (yo.universidad IS NOT NULL AND toLower(yo.universidad) = toLower(coalesce(p.universidad, ''))) AS misma_formacion,
               c.id AS cuenta_id, contactos, habilidades, proyectos, temas,
               round(
                   CASE WHEN contactos * 7 > 20 THEN 20 ELSE contactos * 7 END +
                   CASE WHEN size(habilidades) * 10 > 30 THEN 30 ELSE size(habilidades) * 10 END +
                   CASE WHEN proyectos * 10 > 20 THEN 20 ELSE proyectos * 10 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END +
                   CASE WHEN yo.ubicacion IS NOT NULL AND toLower(yo.ubicacion) = toLower(coalesce(p.ubicacion, '')) THEN 10 ELSE 0 END +
                   CASE WHEN yo.universidad IS NOT NULL AND toLower(yo.universidad) = toLower(coalesce(p.universidad, '')) THEN 10 ELSE 0 END
               ) AS afinidad
        ORDER BY afinidad DESC, contactos DESC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    empresas = consultar(
        """
        MATCH (yo:Usuario {id: $id}), (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
          AND NOT EXISTS { MATCH (yo)-[:SIGUE_A]->(e) }
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:REQUIERE]-(o)
        WITH yo, e, o, count(DISTINCT h) AS coincidencias
        OPTIONAL MATCH (o)-[:REQUIERE]->(requisito:Habilidad)
        WITH yo, e, o, coincidencias, count(DISTINCT requisito) AS requisitos
        WITH yo, e, count(DISTINCT o) AS ofertas,
             sum(coincidencias) AS coincidencias,
             avg(CASE WHEN requisitos = 0 THEN 0.35 ELSE toFloat(coincidencias) / requisitos END) AS ajuste,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         toLower(coalesce(e.sector, '')) CONTAINS trim(tema)]) AS temas
        OPTIONAL MATCH ruta = shortestPath((yo)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A*..6]-(e))
        WITH yo, e, ofertas, coincidencias, ajuste, temas, length(ruta) AS distancia,
             CASE WHEN coalesce(yo.ubicacion, '') <> '' AND toLower(yo.ubicacion) = toLower(coalesce(e.ubicacion, '')) THEN 8 ELSE 0 END AS ciudad
        RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector,
               ofertas, coincidencias, distancia, temas,
               round(30 * ajuste +
                   CASE WHEN coincidencias * 5 > 20 THEN 20 ELSE coincidencias * 5 END +
                   CASE WHEN ofertas * 5 > 15 THEN 15 ELSE ofertas * 5 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END + ciudad +
                   CASE WHEN distancia IS NULL OR 17 - distancia * 3 < 0 THEN 0 ELSE 17 - distancia * 3 END
               ) AS afinidad
        ORDER BY afinidad DESC, distancia ASC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    proyectos = consultar(
        """
        MATCH (yo:Usuario {id: $id}), (p:Proyecto)
        WHERE NOT EXISTS { MATCH (yo)-[:PARTICIPA_EN]->(p) }
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p)
        WITH yo, p, collect(DISTINCT h.nombre) AS tecnologias,
             size([tema IN split(toLower(coalesce(yo.areas_interes, '')), ',')
                   WHERE trim(tema) <> '' AND
                         (toLower(coalesce(p.nombre, '')) CONTAINS trim(tema) OR
                          toLower(coalesce(p.descripcion, '')) CONTAINS trim(tema))]) AS temas
        OPTIONAL MATCH (miembro:Usuario)-[:PARTICIPA_EN]->(p)
        WITH yo, p, tecnologias, temas, count(DISTINCT miembro) AS miembros
        OPTIONAL MATCH ruta = shortestPath((yo)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA|PUBLICA_PROYECTO|PERTENECE_A*..6]-(p))
        WITH yo, p, tecnologias, temas, miembros, length(ruta) AS distancia
        RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion,
               tecnologias, size(tecnologias) AS coincidencias, miembros, distancia, temas,
               round(
                   CASE WHEN size(tecnologias) * 16 > 50 THEN 50 ELSE size(tecnologias) * 16 END +
                   CASE WHEN miembros * 2 > 10 THEN 10 ELSE miembros * 2 END +
                   CASE WHEN temas * 5 > 10 THEN 10 ELSE temas * 5 END +
                   CASE WHEN distancia IS NULL OR 30 - distancia * 4 < 0 THEN 0 ELSE 30 - distancia * 4 END
               ) AS afinidad
        ORDER BY afinidad DESC, distancia ASC, nombre
        LIMIT 5
        """,
        id=usuario_id,
    ) or []
    return personas, empresas, proyectos


def _boton_ver_usuario(usuario_id, key, texto="Ver perfil"):
    if st.button(texto, key=key, width="stretch"):
        st.session_state["usuario_publico_nonce"] = uuid.uuid4().hex
        ir_a("Usuarios", usuario_publico_id=usuario_id)


def _boton_ver_empresa(empresa_id, key, texto="Ver empresa"):
    if st.button(texto, key=key, width="stretch"):
        st.session_state["empresa_publica_nonce"] = uuid.uuid4().hex
        ir_a("Empresas", empresa_publica_id=empresa_id)


def _boton_ver_proyecto(proyecto_id, key, texto="Ver proyecto"):
    if st.button(texto, key=key, width="stretch"):
        st.session_state["proyecto_publico_nonce"] = uuid.uuid4().hex
        ir_a("Proyectos", proyecto_publico_id=proyecto_id)


def _panel_lateral(usuario_id):
    personas, empresas, proyectos = _sugerencias(usuario_id)
    with st.container(border=True):
        st.markdown("#### Perfiles afines")
        st.caption("Ordenados por contactos, habilidades, proyectos, intereses, ciudad y formación en común.")
        if not personas:
            st.caption("Completa tu perfil y agrega contactos para activar sugerencias.")
        for i, persona in enumerate(personas[:3]):
            st.markdown(f"**{persona['nombre']}**")
            st.caption(persona.get("perfil") or "Perfil profesional")
            motivos = []
            if persona.get("habilidades"):
                motivos.append(f"{len(persona['habilidades'])} habilidades compartidas")
            if persona.get("contactos"):
                motivos.append(f"{persona['contactos']} contactos en común")
            if persona.get("proyectos"):
                motivos.append(f"{persona['proyectos']} proyectos compartidos")
            if persona.get("temas"):
                motivos.append("intereses profesionales parecidos")
            if persona.get("misma_ciudad"):
                motivos.append("misma ciudad")
            if persona.get("misma_formacion"):
                motivos.append("misma institución")
            if not motivos and persona.get("ubicacion"):
                motivos.append(f"También está en {persona['ubicacion']}")
            st.caption(f"Afinidad {persona.get('afinidad', 0)}/100 · " + (" · ".join(motivos) or "Perfil relacionado"))
            _boton_ver_usuario(persona["id"], f"lateral_persona_{i}_{persona['id']}", "Ver perfil")
    with st.container(border=True):
        st.markdown("#### Empresas para explorar")
        if not empresas:
            st.caption("No hay empresas nuevas con ofertas abiertas.")
        for i, empresa in enumerate(empresas[:3]):
            st.markdown(f"**{empresa['nombre']}**")
            distancia = f" · {empresa['distancia']} pasos" if empresa.get("distancia") is not None else ""
            st.caption(f"Afinidad {empresa.get('afinidad', 0)}/100 · {empresa.get('sector') or 'Empresa'} · {empresa['ofertas']} ofertas · {empresa['coincidencias']} habilidades" + (" · sector afín" if empresa.get("temas") else "") + distancia)
            _boton_ver_empresa(empresa["id"], f"lateral_empresa_{i}_{empresa['id']}")
    with st.container(border=True):
        st.markdown("#### Proyectos afines")
        if not proyectos:
            st.caption("Completa tus habilidades para encontrar proyectos relacionados.")
        for i, proyecto in enumerate(proyectos[:2]):
            st.markdown(f"**{proyecto['nombre']}**")
            distancia = f" · {proyecto['distancia']} pasos" if proyecto.get("distancia") is not None else ""
            st.caption(f"Afinidad {proyecto.get('afinidad', 0)}/100 · {proyecto['coincidencias']} habilidades · {proyecto['miembros']} participantes" + (" · tema de interés" if proyecto.get("temas") else "") + distancia)
            _boton_ver_proyecto(proyecto["id"], f"lateral_proyecto_{i}_{proyecto['id']}")
    st.caption("Las sugerencias usan datos del perfil y relaciones del grafo; son una ayuda para explorar, no una garantía de compatibilidad.")


def _inicio(usuario_id, perfil):
    nombre = escape(str(perfil.get("nombre") or "profesional"))
    habilidades_perfil = _habilidades(usuario_id)
    experiencia_perfil = _experiencia(usuario_id)
    proyectos_perfil = _proyectos_usuario(usuario_id)
    porcentaje, pendientes = _completitud(perfil, habilidades_perfil, experiencia_perfil, proyectos_perfil)
    st.markdown(
        f"<section class='social-hero'><h1>Hola, {nombre}</h1>"
        "<p>Tu perfil, tu red y nuevas oportunidades profesionales en un solo lugar.</p></section>",
        unsafe_allow_html=True,
    )
    principal, lateral = st.columns([2.1, 1], gap="large")
    with principal:
        resumen = consultar(
            """
            MATCH (u:Usuario {id: $id})
            OPTIONAL MATCH (u)-[:CONECTA_CON]-(contacto:Usuario)
            WITH u, count(DISTINCT contacto) AS contactos
            OPTIONAL MATCH (u)-[:TIENE_HABILIDAD]->(h:Habilidad)
            WITH u, contactos, count(DISTINCT h) AS habilidades
            OPTIONAL MATCH (u)-[p:POSTULA_A]->(:Oferta)
            RETURN contactos, habilidades, count(p) AS postulaciones
            """,
            id=usuario_id,
        )
        datos = resumen[0] if resumen else {"contactos": 0, "habilidades": 0, "postulaciones": 0}
        c1, c2, c3 = st.columns(3)
        c1.metric("Contactos", datos["contactos"])
        c2.metric("Habilidades", datos["habilidades"])
        c3.metric("Postulaciones", datos["postulaciones"])

        with st.container(border=True):
            st.markdown("#### Tu perfil profesional")
            st.write(
                f"**{perfil.get('perfil_profesional') or 'Añade tu perfil profesional'}**"
                + (f" · {perfil['universidad']}" if perfil.get("universidad") else "")
            )
            st.caption(perfil.get("acerca_de") or "Cuenta brevemente qué haces, qué buscas y en qué te gustaría colaborar.")
            st.progress(porcentaje / 100)
            st.caption(f"Perfil completado: {porcentaje}%" + (f" · Siguiente paso: {pendientes[0]}" if pendientes else " · Todo listo"))
            if st.button("Completar mi perfil", key="inicio_editar_perfil"):
                ir_a("Mi perfil")

        st.markdown("#### Oportunidades que encajan contigo")
        ofertas = _ofertas_recomendadas(usuario_id)[:3]
        if not ofertas:
            st.info("No hay nuevas ofertas coincidentes. Añade habilidades a tu perfil para mejorar las recomendaciones.")
        for i, oferta in enumerate(ofertas):
            with st.container(border=True):
                st.markdown(f"**{oferta['titulo']}** · {oferta['empresa']}")
                st.caption(_resumen_afinidad(oferta))
                st.progress(float(oferta.get("afinidad") or 0) / 100)
                if st.button("Ver oportunidad", key=f"inicio_oferta_{i}_{oferta['id']}"):
                    st.session_state["oferta_publica_nonce"] = uuid.uuid4().hex
                    ir_a("Ofertas", oferta_seleccionada=oferta["id"])

    with lateral:
        _panel_lateral(usuario_id)


def _renderizar_perfil_detallado(usuario_id, propio=False):
    fila = _perfil_usuario(usuario_id)
    if not fila:
        st.info("No se encontró un perfil activo para mostrar.")
        return
    perfil = fila["perfil"] or {}
    habilidades = _habilidades(usuario_id)
    experiencia = _experiencia(usuario_id)
    proyectos = _proyectos_usuario(usuario_id)
    _tarjeta_perfil(perfil)
    with st.container(border=True):
        st.markdown("#### Acerca de")
        st.write(perfil.get("acerca_de") or "Este perfil todavía no incluye una presentación.")
        formacion = " · ".join(
            str(valor) for valor in (perfil.get("educacion_detalle"), perfil.get("universidad")) if valor
        ) or "Sin especificar"
        anios = perfil.get("anios_experiencia")
        experiencia_label = f"{anios} años" if anios is not None else "Sin especificar"
        columnas = st.columns(3)
        columnas[0].caption(f"Formación · {formacion}")
        columnas[1].caption(f"Experiencia · {experiencia_label}")
        columnas[2].caption(f"Idiomas · {perfil.get('idiomas') or 'Sin especificar'}")
        if perfil.get("experiencia"):
            st.markdown("#### Experiencia y objetivos")
            st.write(perfil["experiencia"])
        if perfil.get("logros"):
            st.markdown("#### Logros destacados")
            st.write(perfil["logros"])
        if perfil.get("areas_interes"):
            st.markdown("#### Áreas de interés")
            st.write(perfil["areas_interes"])
        if perfil.get("sitio_portafolio") and url_http_valida(perfil.get("sitio_portafolio")):
            st.link_button("Abrir portafolio", perfil["sitio_portafolio"])

    st.markdown("#### Habilidades")
    if habilidades:
        st.markdown(" · ".join(f"**{escape(str(h['habilidad']))}** ({h.get('nivel') or 'sin nivel'})" for h in habilidades))
    else:
        st.caption("Todavía no hay habilidades asociadas.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Experiencia en empresas")
        if experiencia:
            for empleo in experiencia:
                estado = "Actual" if empleo["actual"] else "Anterior"
                detalle = " · ".join(x for x in [empleo.get("sector"), empleo.get("periodo")] if x)
                tarjeta(empleo.get("empresa") or "Empresa", empleo.get("cargo") or "Cargo no especificado", detalle or "", estado)
                if empleo.get("descripcion"):
                    st.caption(empleo["descripcion"])
        else:
            st.caption("No hay experiencia empresarial en el perfil.")
    with c2:
        st.markdown("#### Proyectos")
        if proyectos:
            for proyecto in proyectos:
                tarjeta(proyecto["proyecto"], proyecto.get("rol") or "Participante", proyecto.get("descripcion") or "", proyecto.get("estado", "en curso"))
        else:
            st.caption("No hay proyectos asociados.")

    if propio:
        st.caption("Estos datos son visibles en tu perfil profesional. El correo de acceso no se publica aquí.")
        return

    cta = st.columns(3)
    estado = consultar(
        """
        MATCH (a:Usuario {id: $yo}), (b:Usuario {id: $otro})
        RETURN EXISTS { MATCH (a)-[:CONECTA_CON]-(b) } AS conectado,
               EXISTS { MATCH (a)-[:SOLICITA_CONEXION]->(b) } AS enviado,
               EXISTS { MATCH (b)-[:SOLICITA_CONEXION]->(a) } AS recibido
        """,
        yo=st.session_state.get("usuario_id_actual"),
        otro=usuario_id,
    )
    estado = estado[0] if estado else {"conectado": False, "enviado": False, "recibido": False}
    if estado["conectado"]:
        cta[0].success("Ya están conectados")
    elif estado["recibido"]:
        cta[0].info("Esta persona ya te envió una solicitud")
        if cta[0].button("Revisar solicitud", key=f"perfil_ir_red_{usuario_id}"):
            ir_a("Mi red")
    elif estado["enviado"]:
        cta[0].button("Solicitud enviada", key=f"perfil_solicitud_enviada_{usuario_id}", disabled=True)
    elif cta[0].button("Conectar", key=f"perfil_conectar_{usuario_id}"):
        _solicitar_conexion(st.session_state.get("usuario_id_actual"), usuario_id)
        st.rerun()

    if fila.get("cuenta_id") and cta[1].button("Enviar mensaje", key=f"perfil_mensaje_{usuario_id}"):
        enviar_mensaje(fila["cuenta_id"])


def _editar_perfil(usuario_id, perfil):
    st.markdown("#### Presentación profesional")
    st.caption("Una descripción concreta ayuda a que otras personas y las recomendaciones entiendan qué haces y qué buscas.")
    try:
        anios_actuales = max(0, min(50, int(perfil.get("anios_experiencia") or 0)))
    except (TypeError, ValueError):
        anios_actuales = 0
    modalidades = ["Sin preferencia", "remoto", "híbrido", "presencial"]
    with st.form("perfil_usuario_editar"):
        nombre = st.text_input("Nombre", value=perfil.get("nombre", ""), max_chars=140)
        profesional = st.text_input("Titular profesional", value=perfil.get("perfil_profesional", ""), max_chars=140, placeholder="Ej. Desarrolladora backend | Python y Neo4j")
        acerca = st.text_area("Acerca de", value=perfil.get("acerca_de", ""), max_chars=1800, height=140, placeholder="Cuenta qué sabes hacer, qué has construido y qué tipo de colaboración buscas.")
        col1, col2 = st.columns(2)
        ubicacion = col1.text_input("Ciudad o región", value=perfil.get("ubicacion", ""), max_chars=120)
        areas = col2.text_input("Áreas de interés", value=perfil.get("areas_interes", ""), max_chars=180, placeholder="Ej. Datos, educación, energía")
        universidad = col1.text_input("Institución", value=perfil.get("universidad", ""), max_chars=140)
        educacion = col2.text_input("Programa o formación", value=perfil.get("educacion_detalle", ""), max_chars=160)
        col3, col4 = st.columns(2)
        anios = col3.number_input("Años de experiencia", min_value=0, max_value=50, value=anios_actuales, step=1)
        modalidad_actual = perfil.get("modalidad_preferida") or "Sin preferencia"
        modalidad = col4.selectbox("Modalidad preferida", modalidades, index=modalidades.index(modalidad_actual) if modalidad_actual in modalidades else 0)
        sitio = st.text_input("Portafolio o sitio profesional", value=perfil.get("sitio_portafolio", ""), max_chars=240, placeholder="https://...")
        experiencia_resumen = st.text_area("Experiencia y objetivos", value=perfil.get("experiencia", ""), max_chars=1400, height=110, placeholder="Describe tus responsabilidades, proyectos o el siguiente paso que buscas.")
        col5, col6 = st.columns(2)
        idiomas = col5.text_input("Idiomas", value=perfil.get("idiomas", ""), max_chars=180, placeholder="Ej. Español nativo, inglés B2")
        logros = col6.text_area("Logros destacados", value=perfil.get("logros", ""), max_chars=700, height=95)
        guardar = st.form_submit_button("Guardar cambios", width="stretch")
    if guardar:
        if not nombre.strip() or not profesional.strip():
            st.warning("El nombre y el titular profesional son obligatorios.")
        elif not url_http_valida(sitio):
            st.warning("Escribe un enlace completo que comience con http:// o https:// y tenga un dominio válido.")
        else:
            resultado = escribir(
                """
                MATCH (u:Usuario {id: $id})
                SET u.nombre = $nombre, u.perfil_profesional = $profesional,
                    u.universidad = CASE WHEN trim($universidad) = '' THEN null ELSE trim($universidad) END,
                    u.ubicacion = CASE WHEN trim($ubicacion) = '' THEN null ELSE trim($ubicacion) END,
                    u.acerca_de = CASE WHEN trim($acerca) = '' THEN null ELSE trim($acerca) END,
                    u.experiencia = CASE WHEN trim($experiencia) = '' THEN null ELSE trim($experiencia) END,
                    u.areas_interes = CASE WHEN trim($areas) = '' THEN null ELSE trim($areas) END,
                    u.educacion_detalle = CASE WHEN trim($educacion) = '' THEN null ELSE trim($educacion) END,
                    u.anios_experiencia = $anios,
                    u.modalidad_preferida = CASE WHEN trim($modalidad) = '' THEN null ELSE trim($modalidad) END,
                    u.sitio_portafolio = CASE WHEN trim($sitio) = '' THEN null ELSE trim($sitio) END,
                    u.idiomas = CASE WHEN trim($idiomas) = '' THEN null ELSE trim($idiomas) END,
                    u.logros = CASE WHEN trim($logros) = '' THEN null ELSE trim($logros) END
                RETURN u.id AS id
                """,
                id=usuario_id,
                nombre=nombre.strip(),
                profesional=profesional.strip(),
                universidad=universidad.strip(),
                ubicacion=ubicacion.strip(),
                acerca=acerca.strip(),
                experiencia=experiencia_resumen.strip(),
                areas=areas.strip(),
                educacion=educacion.strip(),
                anios=int(anios),
                modalidad="" if modalidad == "Sin preferencia" else modalidad,
                sitio=sitio.strip(),
                idiomas=idiomas.strip(),
                logros=logros.strip(),
            )
            if resultado:
                cuenta_actual = st.session_state.get("cuenta_autenticada")
                if cuenta_actual is not None:
                    cuenta_actual["nombre"] = nombre.strip()
                st.success("Tu perfil quedó actualizado.")
                st.rerun()


def _editar_habilidades(usuario_id):
    habilidades = consultar("MATCH (h:Habilidad) RETURN h.id AS id, h.nombre AS nombre, h.categoria AS categoria ORDER BY nombre") or []
    actuales = _habilidades(usuario_id)
    st.markdown("#### Lo que sabes hacer")
    if actuales:
        for habilidad in actuales:
            with st.form(f"editar_habilidad_{usuario_id}_{habilidad['id']}"):
                a, b, c = st.columns([2, 2, 1])
                a.write(f"**{habilidad['habilidad']}**")
                niveles = ["básico", "intermedio", "avanzado"]
                nivel_actual = habilidad.get("nivel") or "básico"
                nivel = b.selectbox(
                    "Dominio", niveles,
                    index=niveles.index(nivel_actual) if nivel_actual in niveles else 0,
                    key=f"nivel_actual_{usuario_id}_{habilidad['id']}",
                )
                guardar_nivel = c.form_submit_button("Guardar")
            if guardar_nivel:
                escribir(
                    "MATCH (:Usuario {id: $u})-[r:TIENE_HABILIDAD]->(:Habilidad {id: $h}) SET r.nivel_dominio = $nivel RETURN $h AS id",
                    u=usuario_id, h=habilidad["id"], nivel=nivel,
                )
                st.rerun()
            if st.button("Quitar habilidad", key=f"quitar_habilidad_{usuario_id}_{habilidad['id']}"):
                escribir(
                    "MATCH (:Usuario {id: $u})-[r:TIENE_HABILIDAD]->(:Habilidad {id: $h}) DELETE r RETURN $h AS id",
                    u=usuario_id, h=habilidad["id"],
                )
                st.rerun()
    else:
        st.caption("Añade tus primeras habilidades para recibir mejores recomendaciones.")

    ids_actuales = {h["id"] for h in actuales}
    disponibles = [h for h in habilidades if h["id"] not in ids_actuales]
    if not disponibles:
        st.info("Ya agregaste todas las habilidades del catálogo.")
        return
    opciones_h = {h["id"]: f"{h['nombre']} · {h.get('categoria') or 'habilidad'}" for h in disponibles}
    with st.form("perfil_agregar_habilidad"):
        habilidad_id = st.selectbox("Agregar habilidad", list(opciones_h), format_func=lambda x: opciones_h[x])
        nivel = st.selectbox("Dominio", ["básico", "intermedio", "avanzado"])
        agregar = st.form_submit_button("Añadir a mi perfil")
    if agregar:
        if escribir(
            """
            MATCH (u:Usuario {id: $u}), (h:Habilidad {id: $h})
            MERGE (u)-[r:TIENE_HABILIDAD]->(h)
            SET r.nivel_dominio = $nivel
            RETURN h.id AS id
            """,
            u=usuario_id, h=habilidad_id, nivel=nivel,
        ):
            st.success("Habilidad agregada.")
            st.rerun()


def _editar_experiencia(usuario_id):
    empleos = _experiencia(usuario_id)
    st.markdown("#### Empresas vinculadas a tu perfil")
    if empleos:
        for empleo in empleos:
            actual = "Actual" if empleo["actual"] else "Anterior"
            with st.container(border=True):
                st.markdown(f"**{empleo['empresa']}** · {actual}")
                st.caption(f"{empleo.get('cargo') or 'Cargo no indicado'} · {empleo.get('sector') or 'Sector no indicado'}")
                if st.button("Quitar experiencia", key=f"quitar_empresa_{usuario_id}_{empleo['id']}"):
                    escribir(
                        "MATCH (:Usuario {id: $u})-[r:TRABAJA_EN]->(:Empresa {id: $e}) DELETE r RETURN $e AS id",
                        u=usuario_id, e=empleo["id"],
                    )
                    st.rerun()
    else:
        st.caption("Añade empresas en las que trabajas o trabajaste.")

    for empleo in empleos:
        with st.form(f"editar_experiencia_{usuario_id}_{empleo['id']}"):
            st.markdown(f"**{empleo['empresa']}**")
            cargo_editar = st.text_input("Cargo", value=empleo.get("cargo") or "", max_chars=120, key=f"cargo_{usuario_id}_{empleo['id']}")
            periodo = st.text_input("Periodo", value=empleo.get("periodo") or "", max_chars=80, placeholder="Ej. 2023–2025", key=f"periodo_{usuario_id}_{empleo['id']}")
            descripcion = st.text_area("Responsabilidades o logros", value=empleo.get("descripcion") or "", max_chars=700, key=f"descripcion_{usuario_id}_{empleo['id']}")
            actual_editar = st.checkbox("Trabajo actualmente allí", value=empleo["actual"], key=f"actual_{usuario_id}_{empleo['id']}")
            guardar_experiencia = st.form_submit_button("Guardar experiencia")
        if guardar_experiencia:
            if not cargo_editar.strip():
                st.warning("Escribe el cargo desempeñado.")
            else:
                escribir(
                    "MATCH (:Usuario {id: $u})-[r:TRABAJA_EN]->(:Empresa {id: $e}) SET r.cargo = $cargo, r.periodo = $periodo, r.descripcion = $descripcion, r.es_actual = $actual RETURN $e AS id",
                    u=usuario_id, e=empleo["id"], cargo=cargo_editar.strip(),
                    periodo=periodo.strip() or None, descripcion=descripcion.strip() or None,
                    actual=actual_editar,
                )
                st.rerun()
    st.markdown("#### Añadir una experiencia laboral")
    st.caption("La empresa debe revisar y aprobar la experiencia antes de que aparezca como empleo verificado.")
    empresas_validables = _empresas_para_validar_experiencia(usuario_id)
    if not empresas_validables:
        st.info("No hay empresas con acceso activo disponibles para revisar una nueva experiencia. Si la empresa no aparece, primero debe registrarse en la red.")
        return
    opciones_e = {e["id"]: f"{e['nombre']} · {e.get('sector') or 'Empresa'}" for e in empresas_validables}
    empresa_id = st.selectbox(
        "Empresa que verificará la experiencia",
        list(opciones_e),
        format_func=lambda x: opciones_e[x],
        key="solicitud_empresa_experiencia",
    )
    ofertas = consultar(
        "MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta) RETURN o.id AS id, o.titulo AS titulo ORDER BY titulo",
        e=empresa_id,
    ) or []
    opciones_oferta = {"": "Sin oferta relacionada"} | {o["id"]: o["titulo"] for o in ofertas}
    with st.form("perfil_solicitar_experiencia", clear_on_submit=True):
        cargo = st.text_input("Cargo", max_chars=120)
        periodo = st.text_input("Periodo", max_chars=80, placeholder="Ej. 2023–2025")
        descripcion = st.text_area("Responsabilidades o logros", max_chars=700)
        oferta_id = st.selectbox("Oferta relacionada (opcional)", list(opciones_oferta), format_func=lambda x: opciones_oferta[x])
        es_actual = st.checkbox("Trabajo actualmente allí", value=True)
        solicitar = st.form_submit_button("Enviar para revisión")
    if solicitar:
        if not cargo.strip():
            st.warning("Escribe el cargo desempeñado.")
        else:
            resultado = escribir(
                """
                MATCH (u:Usuario {id: $u}), (e:Empresa {id: $e})
                MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
                WHERE coalesce(c.activa, true) = true
                  AND NOT EXISTS { MATCH (u)-[:TRABAJA_EN]->(e) }
                OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta {id: $oferta})
                WITH u, e, o WHERE $oferta = '' OR o IS NOT NULL
                MERGE (u)-[r:SOLICITA_EXPERIENCIA]->(e)
                SET r.id = $solicitud_id, r.cargo = $cargo, r.periodo = $periodo,
                    r.descripcion = $descripcion, r.es_actual = $actual,
                    r.oferta_id = o.id, r.estado_revision = 'pendiente',
                    r.fecha_solicitud = $fecha
                RETURN r.id AS id
                """,
                u=usuario_id, e=empresa_id, oferta=oferta_id,
                solicitud_id=uuid.uuid4().hex,
                cargo=cargo.strip(), periodo=periodo.strip() or None,
                descripcion=descripcion.strip() or None, actual=es_actual,
                fecha=date.today().isoformat(),
            )
            if resultado:
                st.success("La solicitud se envió. La experiencia aparecerá en tu perfil cuando la empresa la apruebe.")
                st.rerun()
            else:
                st.warning("No se pudo enviar la solicitud. Revisa si ya existe una relación laboral con esa empresa.")


def _editar_proyectos(usuario_id):
    proyectos_actuales = _proyectos_usuario(usuario_id)
    st.markdown("#### Proyectos de tu trayectoria")
    for proyecto in proyectos_actuales:
        with st.container(border=True):
            st.markdown(f"**{proyecto['proyecto']}** · {proyecto.get('estado', 'en curso')}")
            with st.form(f"editar_aporte_{usuario_id}_{proyecto['id']}"):
                rol = st.text_input(
                    "Tu rol o contribución", value=proyecto.get("rol") or "",
                    max_chars=120, key=f"rol_proyecto_{usuario_id}_{proyecto['id']}",
                )
                estado = st.selectbox(
                    "Estado", ["en curso", "finalizado"],
                    index=1 if proyecto.get("estado") == "finalizado" else 0,
                    key=f"estado_proyecto_{usuario_id}_{proyecto['id']}",
                )
                guardar = st.form_submit_button("Guardar cambios")
            if guardar:
                if not rol.strip():
                    st.warning("Describe brevemente tu participación.")
                else:
                    escribir(
                        "MATCH (:Usuario {id: $u})-[r:PARTICIPA_EN]->(:Proyecto {id: $p}) SET r.rol = $rol, r.estado = $estado RETURN $p AS id",
                        u=usuario_id, p=proyecto["id"], rol=rol.strip(), estado=estado,
                    )
                    st.rerun()
            if st.button("Quitar de mi perfil", key=f"quitar_proyecto_{usuario_id}_{proyecto['id']}"):
                escribir(
                    "MATCH (:Usuario {id: $u})-[r:PARTICIPA_EN]->(:Proyecto {id: $p}) DELETE r RETURN $p AS id",
                    u=usuario_id, p=proyecto["id"],
                )
                st.rerun()
    if not proyectos_actuales:
        st.caption("Añade proyectos para mostrar en qué has participado.")

    st.markdown("#### Solicitar validación de otro proyecto")
    st.caption("La empresa que publica el proyecto revisará tu participación antes de añadirla al perfil.")
    proyectos_validables = consultar(
        """
        MATCH (u:Usuario {id: $u}), (p:Proyecto), (e:Empresa)
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        WHERE coalesce(c.activa, true) = true
          AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
               OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
          AND NOT EXISTS { MATCH (u)-[:PARTICIPA_EN]->(p) }
          AND NOT EXISTS {
              MATCH (u)-[r:SOLICITA_PARTICIPACION]->(p)
              WHERE coalesce(r.estado_revision, 'pendiente') = 'pendiente'
          }
        RETURN DISTINCT p.id AS proyecto_id, p.nombre AS proyecto,
               e.id AS empresa_id, e.nombre AS empresa
        ORDER BY proyecto, empresa
        """,
        u=usuario_id,
    ) or []
    if not proyectos_validables:
        st.info("No hay proyectos publicados por una empresa con acceso activo que puedas solicitar ahora. Si un proyecto no aparece, la organización debe registrarlo y publicarlo primero.")
        return
    opciones = {
        f"{fila['proyecto_id']}::{fila['empresa_id']}": f"{fila['proyecto']} · {fila['empresa']}"
        for fila in proyectos_validables
    }
    seleccion = st.selectbox(
        "Proyecto y organización que validará",
        list(opciones),
        format_func=lambda x: opciones[x],
        key=f"solicitud_proyecto_seleccion_{usuario_id}",
    )
    proyecto_id, empresa_id = seleccion.split("::", 1)
    with st.form("perfil_solicitar_proyecto"):
        rol = st.text_input("Tu rol o contribución", max_chars=120)
        estado = st.selectbox("Estado de tu participación", ["en curso", "finalizado"])
        solicitar = st.form_submit_button("Enviar para revisión")
    if solicitar:
        if not rol.strip():
            st.warning("Describe brevemente tu participación.")
        else:
            resultado = escribir(
                """
                MATCH (u:Usuario {id: $u}), (p:Proyecto {id: $p}), (e:Empresa {id: $e})
                MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
                WHERE coalesce(c.activa, true) = true
                  AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
                       OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
                  AND NOT EXISTS { MATCH (u)-[:PARTICIPA_EN]->(p) }
                MERGE (u)-[r:SOLICITA_PARTICIPACION]->(p)
                SET r.id = $solicitud_id, r.empresa_id = e.id,
                    r.rol = $rol, r.estado_participacion = $estado,
                    r.estado_revision = 'pendiente', r.fecha_solicitud = $fecha
                RETURN r.id AS id
                """,
                u=usuario_id, p=proyecto_id, e=empresa_id,
                solicitud_id=uuid.uuid4().hex, rol=rol.strip(), estado=estado,
                fecha=date.today().isoformat(),
            )
            if resultado:
                st.success("La solicitud se envió a la organización. Se añadirá a tu perfil cuando la aprueben.")
                st.rerun()


def _mi_perfil(usuario_id, perfil):
    habilidades = _habilidades(usuario_id)
    proyectos = _proyectos_usuario(usuario_id)
    experiencia = _experiencia(usuario_id)
    porcentaje, pendientes = _completitud(perfil, habilidades, experiencia, proyectos)
    _tarjeta_perfil(perfil)
    izquierda, derecha = st.columns([2, 1], gap="medium")
    with izquierda:
        with st.container(border=True):
            st.markdown(f"#### Perfil completado · {porcentaje}%")
            st.progress(porcentaje / 100)
            st.caption("Un perfil con presentación, habilidades y trayectoria ofrece mejores recomendaciones.")
            if pendientes:
                st.write("Por completar: " + " · ".join(pendientes[:4]))
            else:
                st.success("Tu perfil ya tiene la información principal.")
    with derecha:
        with st.container(border=True):
            st.markdown("#### Tu trayectoria")
            a, b, c = st.columns(3)
            a.metric("Habilidades", len(habilidades))
            b.metric("Proyectos", len(proyectos))
            c.metric("Empresas", len(experiencia))
    datos, skills, empleo, portfolio, solicitudes = st.tabs(
        ["Presentación", "Habilidades", "Experiencia", "Proyectos", "Solicitudes"]
    )
    with datos:
        _editar_perfil(usuario_id, perfil)
    with skills:
        _editar_habilidades(usuario_id)
    with empleo:
        _editar_experiencia(usuario_id)
    with portfolio:
        _editar_proyectos(usuario_id)
    with solicitudes:
        _gestionar_solicitudes_trayectoria(usuario_id)


def _directorio_usuarios(usuario_id):
    st.markdown("#### Profesionales de la red")
    busqueda = st.text_input("Buscar por nombre o especialidad", key="buscar_usuario_directorio")
    filas = consultar(
        """
        MATCH (c:Cuenta)-[:REPRESENTA_A]->(u:Usuario)
        WHERE u.id <> $yo AND coalesce(c.activa, true) = true
        RETURN u.id AS id, u.nombre AS nombre, u.perfil_profesional AS perfil,
               u.universidad AS universidad, u.ubicacion AS ubicacion, c.id AS cuenta_id
        ORDER BY nombre
        """,
        yo=usuario_id,
    ) or []
    texto = busqueda.strip().casefold()
    if texto:
        filas = [x for x in filas if texto in " ".join(str(x.get(k) or "") for k in ("nombre", "perfil", "universidad", "ubicacion")).casefold()]
    if not filas:
        st.info("No se encontraron perfiles con esos datos.")
        return
    opciones = {f["id"]: f"{f['nombre']} · {f.get('perfil') or 'Profesional'}" for f in filas}
    sugerido = st.session_state.get("usuario_publico_id")
    ids = list(opciones)
    index = ids.index(sugerido) if sugerido in ids else 0
    selector_key = f"usuario_directorio_seleccion_{st.session_state.get('usuario_publico_nonce', 'inicio')}"
    usuario_publico = st.selectbox("Perfiles disponibles", ids, index=index, format_func=lambda x: opciones[x], key=selector_key)
    izquierda, derecha = st.columns([2, 1], gap="large")
    with izquierda:
        _renderizar_perfil_detallado(usuario_publico, propio=usuario_publico == usuario_id)
    with derecha:
        _panel_lateral(usuario_id)


def _directorio_empresas(usuario_id):
    st.markdown("#### Organizaciones de la red")
    busqueda = st.text_input("Buscar por empresa, sector o descripción", key="buscar_empresa_directorio")
    filas = consultar(
        """
        MATCH (e:Empresa)
        OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
        WHERE coalesce(c.activa, true) = true
        WITH e, head(collect(DISTINCT c.id)) AS cuenta_id
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        WITH e, cuenta_id,
             count(DISTINCT CASE WHEN toLower(trim(coalesce(o.estado, ''))) = 'abierta' THEN o END) AS vacantes
        RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector,
               e.descripcion AS descripcion, e.ubicacion AS ubicacion,
               e.tamano AS tamano, e.sitio_web AS sitio_web,
               cuenta_id, vacantes
        ORDER BY nombre
        """
    ) or []
    texto = busqueda.strip().casefold()
    if texto:
        filas = [x for x in filas if texto in " ".join(str(x.get(k) or "") for k in ("nombre", "sector", "descripcion", "ubicacion")).casefold()]
    if not filas:
        st.info("No se encontraron organizaciones con esos datos.")
        return

    seleccionada = st.session_state.get("empresa_publica_id")
    if seleccionada not in {e["id"] for e in filas}:
        seleccionada = None
        st.session_state.pop("empresa_publica_id", None)
    st.caption("Elige una organización para abrir su perfil, conocer su equipo y revisar los proyectos y vacantes.")
    for inicio in range(0, len(filas), 2):
        columnas = st.columns(2, gap="medium")
        for columna, empresa in zip(columnas, filas[inicio:inicio + 2]):
            with columna:
                with st.container(border=True):
                    st.markdown(f"#### {escape(str(empresa.get('nombre') or 'Organización'))}")
                    st.caption(escape(str(empresa.get("sector") or "Sector por definir")))
                    descripcion = str(empresa.get("descripcion") or "").strip()
                    st.write((descripcion[:180] + "…") if len(descripcion) > 180 else (descripcion or "La organización aún no ha completado su descripción."))
                    st.caption(f"{empresa.get('vacantes') or 0} vacantes abiertas")
                    if st.button("Abrir empresa", key=f"abrir_empresa_{empresa['id']}", type="primary" if empresa["id"] == seleccionada else "secondary", width="stretch"):
                        st.session_state["empresa_publica_id"] = empresa["id"]
                        st.rerun()

    if not seleccionada:
        st.info("Selecciona una empresa de la lista para ver su perfil completo.")
        return
    empresa = next((e for e in filas if e["id"] == seleccionada), None)
    if not empresa:
        return

    principal, lateral = st.columns([2, 1], gap="large")
    with principal:
        with st.container(border=True):
            st.markdown(f"## {escape(str(empresa.get('nombre') or 'Organización'))}")
            st.markdown(f"**{escape(str(empresa.get('sector') or 'Organización'))}**")
            st.caption(" · ".join(x for x in [empresa.get("ubicacion"), empresa.get("tamano"), f"{empresa.get('vacantes') or 0} vacantes abiertas"] if x))
            st.write(empresa.get("descripcion") or "Esta empresa todavía no ha añadido una descripción.")
            if empresa.get("sitio_web") and url_http_valida(empresa.get("sitio_web")):
                st.link_button("Visitar sitio web", empresa["sitio_web"])

        empleados = consultar(
            """
            MATCH (u:Usuario)-[r:TRABAJA_EN]->(:Empresa {id: $e})
            RETURN u.id AS id, u.nombre AS nombre, u.perfil_profesional AS perfil,
                   r.cargo AS cargo, coalesce(r.es_actual, false) AS actual,
                   r.periodo AS periodo
            ORDER BY actual DESC, nombre
            """,
            e=seleccionada,
        ) or []
        st.markdown("#### Personas del equipo")
        if not empleados:
            st.caption("La organización todavía no tiene experiencias verificadas visibles.")
        for persona in empleados:
            with st.container(border=True):
                st.markdown(f"**{escape(str(persona.get('nombre') or 'Profesional'))}** · {escape(str(persona.get('cargo') or persona.get('perfil') or 'Colaborador'))}")
                st.caption(" · ".join(x for x in ["Actualmente" if persona.get("actual") else "Anteriormente", persona.get("periodo"), persona.get("perfil")] if x))

        proyectos = consultar(
            """
            MATCH (e:Empresa {id: $e}), (p:Proyecto)
            WHERE EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
               OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) }
            CALL {
                WITH p
                OPTIONAL MATCH (u:Usuario)-[r:PARTICIPA_EN]->(p)
                RETURN collect(DISTINCT CASE WHEN u IS NULL THEN null ELSE
                    {nombre: u.nombre, rol: r.rol} END) AS participantes
            }
            CALL {
                WITH e, p
                OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)-[:PERTENECE_A]->(p)
                RETURN collect(DISTINCT o.titulo) AS ofertas
            }
            RETURN DISTINCT p.id AS id, p.nombre AS nombre,
                   p.descripcion AS descripcion, participantes, ofertas
            ORDER BY nombre
            """,
            e=seleccionada,
        ) or []
        st.markdown("#### Proyectos de la organización")
        if not proyectos:
            st.caption("No hay proyectos publicados por esta organización.")
        for proyecto in proyectos:
            with st.container(border=True):
                st.markdown(f"**{escape(str(proyecto.get('nombre') or 'Proyecto'))}**")
                st.write(proyecto.get("descripcion") or "Descripción pendiente.")
                equipo = [p for p in (proyecto.get("participantes") or []) if p and p.get("nombre")]
                if equipo:
                    st.caption("Participantes: " + " · ".join(f"{p['nombre']} ({p.get('rol') or 'colaborador'})" for p in equipo))
                ofertas_proyecto = [o for o in (proyecto.get("ofertas") or []) if o]
                if ofertas_proyecto:
                    st.caption("Ofertas: " + " · ".join(ofertas_proyecto))

        filas_oferta = consultar(
            """
            MATCH (e:Empresa {id: $id})-[:PUBLICA]->(o:Oferta)
            WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
            OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
            CALL {
                WITH o
                OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
                RETURN collect(DISTINCT h.nombre) AS habilidades
            }
            RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
                   o.modalidad AS modalidad, o.nivel_experiencia AS experiencia,
                   p.nombre AS proyecto, p.descripcion AS proyecto_descripcion,
                   habilidades
            ORDER BY titulo
            """,
            id=seleccionada,
        ) or []
        st.markdown("#### Ofertas abiertas")
        for i, oferta in enumerate(filas_oferta):
            with st.container(border=True):
                st.markdown(f"**{escape(str(oferta.get('titulo') or 'Oferta'))}**")
                st.caption(" · ".join(x for x in [oferta.get("modalidad") or "Modalidad por definir", oferta.get("experiencia") or "Experiencia por definir", f"Proyecto: {oferta['proyecto']}" if oferta.get("proyecto") else ""] if x))
                if oferta.get("proyecto_descripcion"):
                    st.caption(oferta["proyecto_descripcion"])
                st.write(oferta.get("descripcion") or "La empresa no ha añadido una descripción adicional.")
                if oferta.get("habilidades"):
                    st.caption("Habilidades: " + " · ".join(x for x in oferta["habilidades"] if x))
                if st.button("Ver oferta", key=f"empresa_dir_oferta_{seleccionada}_{i}"):
                    st.session_state["oferta_publica_nonce"] = uuid.uuid4().hex
                    ir_a("Ofertas", oferta_seleccionada=oferta["id"])
        if not filas_oferta:
            st.caption("No hay vacantes abiertas en este momento.")

        es_seguida = consultar(
            "MATCH (u:Usuario {id: $u}), (e:Empresa {id: $e}) RETURN EXISTS { MATCH (u)-[:SIGUE_A]->(e) } AS sigue",
            u=usuario_id, e=seleccionada,
        )
        sigue = bool(es_seguida and es_seguida[0]["sigue"])
        if sigue:
            if st.button("Dejar de seguir", key=f"dejar_seguir_{seleccionada}"):
                escribir("MATCH (:Usuario {id: $u})-[r:SIGUE_A]->(:Empresa {id: $e}) DELETE r RETURN $e AS id", u=usuario_id, e=seleccionada)
                st.rerun()
        elif st.button("Seguir empresa", key=f"seguir_{seleccionada}"):
            escribir("MATCH (u:Usuario {id: $u}), (e:Empresa {id: $e}) MERGE (u)-[:SIGUE_A]->(e) RETURN e.id AS id", u=usuario_id, e=seleccionada)
            st.rerun()
        if empresa.get("cuenta_id") and st.button("Contactar empresa", key=f"contactar_empresa_{seleccionada}"):
            enviar_mensaje(empresa["cuenta_id"])
    with lateral:
        _panel_lateral(usuario_id)


def _resumen_afinidad(oferta):
    coincidencias = oferta.get("habilidades") or []
    distancia = oferta.get("distancia")
    partes = [f"Afinidad {oferta.get('afinidad', 0)}/100", f"{len(coincidencias)} habilidades coincidentes"]
    partes.append(f"a {distancia} pasos en la red" if distancia is not None else "sin ruta profesional cercana encontrada")
    if oferta.get("contactos"):
        partes.append(f"{oferta['contactos']} contactos vinculados")
    return " · ".join(partes)


def _ofertas_recomendadas(usuario_id):
    return consultar(
        f"""
        MATCH (u:Usuario {{id: $id}}), (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
          AND NOT EXISTS {{ MATCH (u)-[:POSTULA_A]->(o) }}
        OPTIONAL MATCH (u)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:REQUIERE]-(o)
        WITH u, e, o, collect(DISTINCT h) AS habilidades_coincidentes
        OPTIONAL MATCH (o)-[:REQUIERE]->(requerida:Habilidad)
        WITH u, e, o, habilidades_coincidentes,
             count(DISTINCT requerida) AS requisitos
        WITH u, e, o, habilidades_coincidentes, requisitos,
             CASE WHEN requisitos = 0 THEN 0.35
                  ELSE toFloat(size(habilidades_coincidentes)) / requisitos END AS ajuste_habilidades
        OPTIONAL MATCH ruta = shortestPath((u)-[:{RELACIONES_RUTA}*..6]-(e))
        OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
        OPTIONAL MATCH (u)-[:CONECTA_CON]-(contacto:Usuario)-[:POSTULA_A]->(o)
        WITH u, e, o, p, habilidades_coincidentes, ajuste_habilidades,
             length(ruta) AS distancia, count(DISTINCT contacto) AS contactos
        WITH u, e, o, p, habilidades_coincidentes, ajuste_habilidades, distancia, contactos,
             CASE WHEN coalesce(o.modalidad, '') = 'remoto' THEN 10
                  WHEN coalesce(u.modalidad_preferida, '') = o.modalidad THEN 10
                  WHEN coalesce(u.ubicacion, '') <> '' AND toLower(u.ubicacion) = toLower(coalesce(e.ubicacion, '')) THEN 8
                  ELSE 0 END AS ajuste_contexto
        RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
               o.modalidad AS modalidad, o.nivel_experiencia AS experiencia,
               e.id AS empresa_id, e.nombre AS empresa, e.sector AS sector,
               p.id AS proyecto_id, p.nombre AS proyecto,
               [h IN habilidades_coincidentes | h.nombre] AS habilidades,
               distancia, contactos,
               round(
                   55 * ajuste_habilidades + ajuste_contexto +
                   CASE WHEN contactos * 5 > 15 THEN 15 ELSE contactos * 5 END +
                   CASE WHEN distancia IS NULL OR 20 - distancia * 3 < 0 THEN 0 ELSE 20 - distancia * 3 END
               ) AS afinidad
        ORDER BY afinidad DESC, CASE WHEN distancia IS NULL THEN 99 ELSE distancia END,
                 contactos DESC, titulo
        """,
        id=usuario_id,
    ) or []


def _ofertas(usuario_id):
    st.markdown("#### Vacantes ordenadas por cercanía y afinidad")
    st.caption("La lista considera la distancia en la red profesional, las habilidades coincidentes y los contactos conectados a la oferta.")
    ofertas = _ofertas_recomendadas(usuario_id)
    postulaciones = consultar(
        """
        MATCH (u:Usuario {id: $id})-[r:POSTULA_A]->(o:Oferta)<-[:PUBLICA]-(e:Empresa)
        OPTIONAL MATCH (o)-[:PERTENECE_A]->(p:Proyecto)
        RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa,
               o.descripcion AS descripcion, o.modalidad AS modalidad,
               o.nivel_experiencia AS experiencia,
               p.nombre AS proyecto, p.descripcion AS proyecto_descripcion,
               r.estado_proceso AS estado, r.fecha_postulacion AS fecha
        ORDER BY fecha DESC
        """,
        id=usuario_id,
    ) or []
    en_proceso = [p for p in postulaciones if str(p.get("estado") or "aplicado").casefold() not in {"aceptado", "rechazado"}]
    resultados = [p for p in postulaciones if str(p.get("estado") or "aplicado").casefold() in {"aceptado", "rechazado"}]
    tab_nuevas, tab_enviadas, tab_resultados = st.tabs(["Para ti", "En proceso", "Resultados"])
    with tab_nuevas:
        if not ofertas:
            st.info("No hay ofertas nuevas. Completa habilidades o revisa más tarde.")
        else:
            opciones = {o["id"]: f"{o['titulo']} · {o['empresa']} · {_resumen_afinidad(o)}" for o in ofertas}
            previo = st.session_state.get("oferta_seleccionada")
            ids = list(opciones)
            selector_key = f"usuario_oferta_seleccion_{st.session_state.get('oferta_publica_nonce', 'inicio')}"
            seleccion = st.selectbox("Ofertas disponibles", ids, index=ids.index(previo) if previo in ids else 0, format_func=lambda x: opciones[x], key=selector_key)
            oferta = next(o for o in ofertas if o["id"] == seleccion)
            with st.container(border=True):
                st.markdown(f"## {escape(str(oferta['titulo']))}")
                st.markdown(f"**{escape(str(oferta['empresa']))}** · {escape(str(oferta.get('sector') or ''))}")
                st.caption(f"{oferta.get('modalidad') or 'Modalidad por definir'} · {oferta.get('experiencia') or 'Experiencia por definir'} · {_resumen_afinidad(oferta)}")
                if oferta.get("proyecto"):
                    st.caption(f"Proyecto relacionado: {oferta['proyecto']}")
                    if st.button("Ver proyecto completo", key=f"oferta_proyecto_{seleccion}"):
                        st.session_state["proyecto_publico_nonce"] = uuid.uuid4().hex
                        ir_a("Proyectos", proyecto_publico_id=oferta["proyecto_id"])
                st.write(oferta.get("descripcion") or "La empresa no ha añadido una descripción adicional.")
                if oferta.get("habilidades"):
                    st.markdown("**Habilidades solicitadas:** " + " · ".join(escape(str(x)) for x in oferta["habilidades"]))
                if st.button("Postularme", key=f"postular_{seleccion}", type="primary"):
                    estado = _postular(usuario_id, seleccion)
                    if estado == "creada":
                        st.success("Tu postulación fue enviada a la empresa.")
                        st.rerun()
                    elif estado == "duplicada":
                        st.info("Ya habías enviado una postulación a esta oferta.")
                    elif estado == "error":
                        st.error("No se pudo enviar la postulación. Revisa la conexión con Neo4j y vuelve a intentarlo.")
                    else:
                        st.warning("La oferta ya no está abierta o dejó de estar publicada.")
    with tab_enviadas:
        if en_proceso:
            for i, post in enumerate(en_proceso):
                with st.container(border=True):
                    st.markdown(f"**{post['titulo']}** · {post['empresa']}")
                    st.caption(f"Estado: {post.get('estado') or 'aplicado'} · Fecha: {post.get('fecha') or 'sin fecha'}")
                    st.caption(" · ".join(x for x in [post.get("modalidad"), post.get("experiencia"), f"Proyecto: {post['proyecto']}" if post.get("proyecto") else ""] if x))
                    if post.get("proyecto_descripcion"):
                        st.write(post["proyecto_descripcion"])
                    st.write(post.get("descripcion") or "La empresa no ha añadido una descripción adicional.")
                    if post.get("estado") in {"aplicado", "en revisión", "entrevista", "entrevistado"} and st.button("Retirar postulación", key=f"retirar_{post['id']}_{i}"):
                        retirada = escribir(
                            "MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o}) DELETE r RETURN $o AS id",
                            u=usuario_id, o=post["id"],
                        )
                        if retirada:
                            st.success("Postulación retirada.")
                            st.rerun()
                        st.warning("No se encontró una postulación pendiente para retirar.")
        else:
            st.info("No tienes candidaturas activas en proceso.")
    with tab_resultados:
        if resultados:
            for post in resultados:
                aceptada = str(post.get("estado") or "").casefold() == "aceptado"
                with st.container(border=True):
                    st.markdown(f"**{post['titulo']}** · {post['empresa']} · {'Aceptada' if aceptada else 'Rechazada'}")
                    st.caption(" · ".join(x for x in [post.get("modalidad"), post.get("experiencia"), f"Proyecto: {post['proyecto']}" if post.get("proyecto") else "", post.get("fecha")] if x))
                    st.write(post.get("descripcion") or "La empresa no ha añadido una descripción adicional.")
                    if aceptada:
                        st.success("La empresa te incorporó a su equipo. Revisa la experiencia en tu perfil.")
        else:
            st.info("Cuando una empresa tome una decisión, el resultado aparecerá aquí.")


def _postular(usuario_id, oferta_id):
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        return "error"
    def registrar(tx):
        actual = tx.run(
            """
            MATCH (u:Usuario {id: $u}), (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $o})
            WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
            RETURN EXISTS { MATCH (u)-[:POSTULA_A]->(o) } AS ya
            """,
            u=usuario_id, o=oferta_id,
        ).single()
        if actual is None:
            return "cerrada"
        if actual["ya"]:
            return "duplicada"
        tx.run(
            """
            MATCH (u:Usuario {id: $u}), (o:Oferta {id: $o})
            CREATE (u)-[:POSTULA_A {fecha_postulacion: $fecha, estado_proceso: 'aplicado'}]->(o)
            """,
            u=usuario_id, o=oferta_id, fecha=date.today().isoformat(),
        ).consume()
        return "creada"
    try:
        with conexion.driver.session() as session:
            resultado = session.execute_write(registrar)
        if resultado == "creada":
            from backend_core.connection import invalidar_cache_datos
            invalidar_cache_datos()
        return resultado
    except Exception:
        return "error"


def _proyectos(usuario_id):
    st.markdown("#### Proyectos profesionales")
    filas = consultar(
        f"""
        MATCH (yo:Usuario {{id: $id}}), (p:Proyecto)
        OPTIONAL MATCH ruta = shortestPath((yo)-[:{RELACIONES_RUTA}*..6]-(p))
        OPTIONAL MATCH (yo)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p)
        WITH yo, p, length(ruta) AS distancia, collect(DISTINCT h.nombre) AS afinidades
        CALL {{
            WITH p
            OPTIONAL MATCH (e:Empresa)-[:PUBLICA_PROYECTO]->(p)
            RETURN collect(DISTINCT CASE WHEN e IS NULL THEN null ELSE
                {{id: e.id, nombre: e.nombre}} END) AS publicadores
        }}
        CALL {{
            WITH p
            OPTIONAL MATCH (e:Empresa)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p)
            RETURN collect(DISTINCT CASE WHEN e IS NULL THEN null ELSE
                {{id: e.id, nombre: e.nombre}} END) AS empresas_oferta
        }}
        CALL {{
            WITH p
            OPTIONAL MATCH (u:Usuario)-[:PARTICIPA_EN]->(p)
            RETURN count(DISTINCT u) AS participantes,
                   collect(DISTINCT u.nombre) AS participantes_nombres
        }}
        CALL {{
            WITH p
            OPTIONAL MATCH (o:Oferta)-[:PERTENECE_A]->(p)
            RETURN collect(DISTINCT o.id) AS ofertas_ids
        }}
        WITH yo, p, distancia, afinidades, participantes,
             participantes_nombres, ofertas_ids,
             [e IN publicadores + empresas_oferta WHERE e.id IS NOT NULL] AS organizaciones
        RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion,
               [e IN organizaciones | e.nombre] AS empresas,
               [e IN organizaciones | e.id] AS empresas_ids,
               ofertas_ids, participantes, participantes_nombres,
               distancia, afinidades
        ORDER BY CASE WHEN distancia IS NULL THEN 99 ELSE distancia END,
                 size(afinidades) DESC, nombre
        """,
        id=usuario_id,
    ) or []
    if not filas:
        st.info("Todavía no hay proyectos disponibles.")
        return
    opcion = {
        p["id"]: f"{p['nombre']} · " + (f"{p['distancia']} pasos" if p.get("distancia") is not None else "sin ruta cercana")
        for p in filas
    }
    previo = st.session_state.get("proyecto_publico_id")
    ids = list(opcion)
    selector_key = f"directorio_proyecto_{st.session_state.get('proyecto_publico_nonce', 'inicio')}"
    seleccionado = st.selectbox("Explorar proyectos", ids, index=ids.index(previo) if previo in ids else 0, format_func=lambda x: opcion[x], key=selector_key)
    proyecto = next(p for p in filas if p["id"] == seleccionado)
    with st.container(border=True):
        st.markdown(f"## {escape(str(proyecto['nombre']))}")
        st.write(proyecto.get("descripcion") or "Este proyecto aún no tiene descripción.")
        distancia_texto = f"Distancia en la red: {proyecto['distancia']} pasos" if proyecto.get("distancia") is not None else "Sin ruta cercana en el grafo"
        st.caption(f"{distancia_texto} · Participantes: {proyecto['participantes']} · Empresas: {', '.join(x for x in proyecto['empresas'] if x) or 'No especificadas'}")
        participantes = [x for x in (proyecto.get("participantes_nombres") or []) if x]
        if participantes:
            st.caption("Personas en el proyecto: " + " · ".join(participantes))
        if proyecto.get("afinidades"):
            st.caption("Tecnologías relacionadas con tus habilidades: " + " · ".join(proyecto["afinidades"]))
    ofertas_proyecto = consultar(
        """
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)-[:PERTENECE_A]->(:Proyecto {id: $p})
        WHERE toLower(trim(coalesce(o.estado, ''))) = 'abierta'
        OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
        RETURN o.id AS id, o.titulo AS titulo, o.descripcion AS descripcion,
               e.nombre AS empresa, collect(DISTINCT h.nombre) AS habilidades
        ORDER BY titulo
        """,
        p=seleccionado,
    ) or []
    if ofertas_proyecto:
        st.markdown("#### Ofertas relacionadas con este proyecto")
        for i, oferta in enumerate(ofertas_proyecto):
            with st.container(border=True):
                st.markdown(f"**{oferta['titulo']}** · {oferta['empresa']}")
                st.write(oferta.get("descripcion") or "Descripción pendiente")
                if oferta.get("habilidades"):
                    st.caption("Habilidades: " + " · ".join(x for x in oferta["habilidades"] if x))
                ya = consultar(
                    "MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o}) RETURN r.estado_proceso AS estado",
                    u=usuario_id, o=oferta["id"],
                )
                if ya:
                    st.success(f"Ya te postulaste · {ya[0].get('estado') or 'aplicado'}")
                elif st.button("Postularme", key=f"postular_proyecto_{seleccionado}_{i}", type="primary"):
                    estado = _postular(usuario_id, oferta["id"])
                    if estado == "creada":
                        st.success("Tu postulación fue enviada.")
                        st.rerun()
                    elif estado == "error":
                        st.error("No se pudo enviar la postulación. Revisa la conexión con Neo4j y vuelve a intentarlo.")
                    else:
                        st.warning("La oferta dejó de estar disponible. Actualiza la vista e inténtalo de nuevo.")
    vinculo = consultar(
        "MATCH (:Usuario {id: $u})-[r:PARTICIPA_EN]->(:Proyecto {id: $p}) RETURN r.rol AS rol, coalesce(r.estado, 'en curso') AS estado",
        u=usuario_id, p=seleccionado,
    )
    if vinculo:
        st.success(f"Está en tu trayectoria: {vinculo[0].get('rol') or 'participante'} · {vinculo[0]['estado']}")
    else:
        revisores = _empresas_revisoras_proyecto(usuario_id, seleccionado)
        solicitud_previa = consultar(
            "MATCH (:Usuario {id: $u})-[r:SOLICITA_PARTICIPACION]->(:Proyecto {id: $p}) RETURN r.estado_revision AS estado, r.empresa_id AS empresa_id LIMIT 1",
            u=usuario_id, p=seleccionado,
        ) or []
        estado_solicitud = str(solicitud_previa[0].get("estado") or "").casefold() if solicitud_previa else ""
        if estado_solicitud == "pendiente":
            st.info("Tu solicitud de participación está en revisión por la organización.")
        elif not revisores:
            st.info("Este proyecto no tiene una organización con cuenta activa que pueda validar tu participación. La empresa debe publicarlo en su perfil primero.")
        else:
            opciones_revisor = {e["id"]: e["nombre"] for e in revisores}
            empresa_default = solicitud_previa[0].get("empresa_id") if solicitud_previa else None
            ids_revisor = list(opciones_revisor)
            with st.form(f"form_sumarse_proyecto_{seleccionado}"):
                empresa_id = st.selectbox(
                    "Organización que revisará tu participación",
                    ids_revisor,
                    index=ids_revisor.index(empresa_default) if empresa_default in ids_revisor else 0,
                    format_func=lambda x: opciones_revisor[x],
                )
                rol = st.text_input("Tu rol o contribución", max_chars=120)
                estado_participacion = st.selectbox("Estado", ["en curso", "finalizado"])
                solicitar = st.form_submit_button("Solicitar validación")
            if solicitar:
                if not rol.strip():
                    st.warning("Describe tu contribución para que la empresa pueda revisarla.")
                elif escribir(
                    """
                    MATCH (u:Usuario {id: $u}), (p:Proyecto {id: $p}), (e:Empresa {id: $e})
                    MATCH (c:Cuenta)-[:REPRESENTA_A]->(e)
                    WHERE coalesce(c.activa, true) = true
                      AND (EXISTS { MATCH (e)-[:PUBLICA_PROYECTO]->(p) }
                           OR EXISTS { MATCH (e)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(p) })
                      AND NOT EXISTS { MATCH (u)-[:PARTICIPA_EN]->(p) }
                    MERGE (u)-[r:SOLICITA_PARTICIPACION]->(p)
                    SET r.id = $solicitud_id, r.empresa_id = e.id,
                        r.rol = $rol, r.estado_participacion = $estado,
                        r.estado_revision = 'pendiente', r.fecha_solicitud = $fecha
                    RETURN r.id AS id
                    """,
                    u=usuario_id, p=seleccionado, e=empresa_id,
                    solicitud_id=uuid.uuid4().hex, rol=rol.strip(),
                    estado=estado_participacion, fecha=date.today().isoformat(),
                ):
                    st.success("La solicitud se envió a la organización.")
                    st.rerun()


def _recomendaciones(usuario_id):
    st.markdown("#### Recomendaciones basadas en tu perfil y la red")
    t_personas, t_empresas, t_proyectos, t_ofertas = st.tabs(["Personas", "Empresas", "Proyectos", "Ofertas"])
    with t_personas:
        personas, _, _ = _sugerencias(usuario_id)
        if not personas:
            st.info("Aún no hay suficientes perfiles para recomendar.")
        for i, persona in enumerate(personas):
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** · {persona.get('perfil') or 'Profesional'}")
                razones = [f"{persona['contactos']} contactos en común"] if persona.get("contactos") else []
                if persona.get("habilidades"):
                    razones.append("Habilidades: " + ", ".join(persona["habilidades"]))
                if persona.get("proyectos"):
                    razones.append(f"{persona['proyectos']} proyectos compartidos")
                if persona.get("temas"):
                    razones.append("Intereses profesionales similares")
                if persona.get("misma_ciudad"):
                    razones.append("Misma ciudad")
                if persona.get("misma_formacion"):
                    razones.append("Misma institución")
                st.caption(f"Afinidad {persona.get('afinidad', 0)}/100 · " + (" · ".join(razones) or "Coincidencia de perfil"))
                st.progress(max(0, min(100, float(persona.get("afinidad") or 0))) / 100)
                _boton_ver_usuario(persona["id"], f"recomendacion_persona_{i}_{persona['id']}")
    with t_empresas:
        _, empresas, _ = _sugerencias(usuario_id)
        if not empresas:
            st.info("No hay empresas nuevas con ofertas abiertas.")
        for i, empresa in enumerate(empresas):
            with st.container(border=True):
                st.markdown(f"**{empresa['nombre']}** · {empresa.get('sector') or 'Empresa'}")
                st.caption(f"Afinidad {empresa.get('afinidad', 0)}/100 · {empresa['ofertas']} ofertas abiertas · {empresa['coincidencias']} habilidades coincidentes" + (" · sector relacionado con tus intereses" if empresa.get("temas") else ""))
                st.progress(max(0, min(100, float(empresa.get("afinidad") or 0))) / 100)
                _boton_ver_empresa(empresa["id"], f"recomendacion_empresa_{i}_{empresa['id']}")
    with t_proyectos:
        _, _, proyectos = _sugerencias(usuario_id)
        if not proyectos:
            st.info("No hay proyectos con tecnologías coincidentes por ahora.")
        for i, proyecto in enumerate(proyectos):
            with st.container(border=True):
                st.markdown(f"**{proyecto['nombre']}**")
                st.write(proyecto.get("descripcion") or "Proyecto profesional")
                st.caption(f"Afinidad {proyecto.get('afinidad', 0)}/100 · {proyecto['coincidencias']} habilidades coincidentes · {proyecto['miembros']} participantes" + (" · tema relacionado con tus intereses" if proyecto.get("temas") else ""))
                st.progress(max(0, min(100, float(proyecto.get("afinidad") or 0))) / 100)
                _boton_ver_proyecto(proyecto["id"], f"recomendacion_proyecto_{i}_{proyecto['id']}")
    with t_ofertas:
        ofertas = _ofertas_recomendadas(usuario_id)
        if not ofertas:
            st.info("No hay ofertas abiertas que coincidan con tu perfil.")
        for i, oferta in enumerate(ofertas[:10]):
            with st.container(border=True):
                st.markdown(f"**{oferta['titulo']}** · {oferta['empresa']}")
                st.caption(_resumen_afinidad(oferta))
                st.progress(float(oferta.get("afinidad") or 0) / 100)
                if st.button("Ver y postularme", key=f"recomendacion_oferta_{i}_{oferta['id']}"):
                    st.session_state["oferta_publica_nonce"] = uuid.uuid4().hex
                    ir_a("Ofertas", oferta_seleccionada=oferta["id"])


def _solicitar_conexion(origen_id, destino_id):
    if not origen_id or not destino_id or origen_id == destino_id:
        return
    resultado = escribir(
        """
        MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
        WHERE NOT EXISTS { MATCH (a)-[:CONECTA_CON]-(b) }
          AND NOT EXISTS { MATCH (a)-[:SOLICITA_CONEXION]->(b) }
          AND NOT EXISTS { MATCH (b)-[:SOLICITA_CONEXION]->(a) }
        CREATE (a)-[:SOLICITA_CONEXION {fecha: $fecha, estado: 'pendiente'}]->(b)
        RETURN b.id AS id
        """,
        a=origen_id, b=destino_id, fecha=date.today().isoformat(),
    )
    if resultado:
        st.success("Solicitud enviada. La conexión se activará cuando la otra persona la acepte.")
    else:
        st.info("Ya existe una conexión o una solicitud pendiente con este perfil.")


def _gestionar_solicitud(origen_id, destino_id, aceptar):
    if aceptar:
        consulta = """
        MATCH (a:Usuario {id: $a})-[s:SOLICITA_CONEXION]->(b:Usuario {id: $b})
        DELETE s
        WITH a, b
        MERGE (a)-[ab:CONECTA_CON]->(b)
        ON CREATE SET ab.fuerza_conexion = 'media'
        MERGE (b)-[ba:CONECTA_CON]->(a)
        ON CREATE SET ba.fuerza_conexion = 'media'
        RETURN a.id AS id
        """
    else:
        consulta = "MATCH (:Usuario {id: $a})-[s:SOLICITA_CONEXION]->(:Usuario {id: $b}) DELETE s RETURN $a AS id"
    return bool(escribir(consulta, a=origen_id, b=destino_id))


def _mi_red(usuario_id):
    st.markdown("#### Mi red profesional")
    conexiones, recibidas, enviadas, desconexiones = st.tabs(["Conexiones", "Solicitudes recibidas", "Enviadas", "Cambios pendientes"])
    with conexiones:
        filas = consultar(
            """
            MATCH (u:Usuario {id: $id})-[:CONECTA_CON]-(p:Usuario)
            RETURN DISTINCT p.id AS id, p.nombre AS nombre,
                   p.perfil_profesional AS perfil
            ORDER BY nombre
            """,
            id=usuario_id,
        ) or []
        if not filas:
            st.info("Cuando otras personas acepten tu invitación, aparecerán aquí.")
        for persona in filas:
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** · {persona.get('perfil') or 'Profesional'}")
                a, b = st.columns(2)
                if a.button("Ver perfil", key=f"red_perfil_{persona['id']}"):
                    ir_a("Usuarios", usuario_publico_id=persona["id"])
                if b.button("Solicitar desconexión", key=f"red_desconectar_{persona['id']}"):
                    resultado = escribir(
                        """
                        MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
                        WHERE EXISTS { MATCH (a)-[:CONECTA_CON]-(b) }
                          AND NOT EXISTS { MATCH (a)-[:SOLICITA_DESCONEXION]->(b) }
                        CREATE (a)-[:SOLICITA_DESCONEXION {fecha: $fecha, estado: 'pendiente'}]->(b)
                        RETURN b.id AS id
                        """,
                        a=usuario_id, b=persona["id"], fecha=date.today().isoformat(),
                    )
                    if resultado:
                        st.info("La desconexión quedará pendiente hasta que la otra persona responda.")
                        st.rerun()
                    st.warning("No se pudo solicitar la desconexión. Puede que ya exista una solicitud pendiente.")
    with recibidas:
        filas = consultar(
            "MATCH (p:Usuario)-[r:SOLICITA_CONEXION]->(:Usuario {id: $id}) RETURN p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil, r.fecha AS fecha ORDER BY fecha DESC",
            id=usuario_id,
        ) or []
        if not filas:
            st.info("No tienes solicitudes nuevas.")
        for persona in filas:
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** · {persona.get('perfil') or 'Profesional'}")
                st.caption(f"Enviada: {persona.get('fecha') or 'fecha no disponible'}")
                a, b, c = st.columns([1, 1, 2])
                if a.button("Aceptar", key=f"aceptar_conexion_{persona['id']}"):
                    if _gestionar_solicitud(persona["id"], usuario_id, True):
                        st.success("Ahora forman parte de la misma red.")
                        st.rerun()
                    st.warning("La solicitud ya no está disponible.")
                if b.button("Rechazar", key=f"rechazar_conexion_{persona['id']}"):
                    if _gestionar_solicitud(persona["id"], usuario_id, False):
                        st.rerun()
                    st.warning("La solicitud ya no está disponible.")
                if c.button("Ver perfil", key=f"solicitud_perfil_{persona['id']}"):
                    ir_a("Usuarios", usuario_publico_id=persona["id"])
    with enviadas:
        filas = consultar(
            "MATCH (:Usuario {id: $id})-[r:SOLICITA_CONEXION]->(p:Usuario) RETURN p.id AS id, p.nombre AS nombre, p.perfil_profesional AS perfil, r.fecha AS fecha ORDER BY fecha DESC",
            id=usuario_id,
        ) or []
        if not filas:
            st.info("No tienes solicitudes pendientes.")
        for persona in filas:
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** · {persona.get('perfil') or 'Profesional'}")
                st.caption(f"Pendiente desde {persona.get('fecha') or 'fecha no disponible'}")
                if st.button("Cancelar solicitud", key=f"cancelar_conexion_{persona['id']}"):
                    _gestionar_solicitud(usuario_id, persona["id"], False)
                    st.rerun()
    with desconexiones:
        filas = consultar(
            "MATCH (p:Usuario)-[r:SOLICITA_DESCONEXION]->(:Usuario {id: $id}) RETURN p.id AS id, p.nombre AS nombre, r.fecha AS fecha ORDER BY fecha DESC",
            id=usuario_id,
        ) or []
        if not filas:
            st.info("No hay solicitudes de desconexión pendientes.")
        for persona in filas:
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** solicita cerrar la conexión")
                a, b = st.columns(2)
                if a.button("Aceptar desconexión", key=f"aceptar_desconexion_{persona['id']}"):
                    escribir(
                        """
                        MATCH (a:Usuario {id: $a})-[s:SOLICITA_DESCONEXION]->(b:Usuario {id: $b})
                        DELETE s
                        WITH a, b
                        OPTIONAL MATCH (a)-[r:CONECTA_CON]->(b)
                        WITH a, b, collect(r) AS relaciones
                        FOREACH (r IN relaciones | DELETE r)
                        WITH a, b
                        OPTIONAL MATCH (b)-[r2:CONECTA_CON]->(a)
                        WITH a, b, collect(r2) AS inversas
                        FOREACH (r IN inversas | DELETE r)
                        RETURN a.id AS id
                        """,
                        a=persona["id"], b=usuario_id,
                    )
                    st.rerun()
                if b.button("Mantener conexión", key=f"rechazar_desconexion_{persona['id']}"):
                    escribir("MATCH (:Usuario {id: $a})-[s:SOLICITA_DESCONEXION]->(:Usuario {id: $b}) DELETE s RETURN $a AS id", a=persona["id"], b=usuario_id)
                    st.rerun()
        st.markdown("#### Solicitudes que enviaste")
        pendientes = consultar(
            "MATCH (:Usuario {id: $id})-[r:SOLICITA_DESCONEXION]->(p:Usuario) RETURN p.id AS id, p.nombre AS nombre, r.fecha AS fecha ORDER BY fecha DESC",
            id=usuario_id,
        ) or []
        if not pendientes:
            st.caption("No tienes solicitudes de desconexión enviadas.")
        for persona in pendientes:
            with st.container(border=True):
                st.markdown(f"**{persona['nombre']}** · esperando respuesta")
                if st.button("Cancelar solicitud de desconexión", key=f"cancelar_desconexion_{persona['id']}"):
                    escribir("MATCH (:Usuario {id: $a})-[s:SOLICITA_DESCONEXION]->(:Usuario {id: $b}) DELETE s RETURN $a AS id", a=usuario_id, b=persona["id"])
                    st.rerun()


def _recomendaciones_pagina(usuario_id):
    principal, lateral = st.columns([2.1, 1], gap="large")
    with principal:
        _recomendaciones(usuario_id)
    with lateral:
        _panel_lateral(usuario_id)


def _consulta_ruta(usuario_id):
    st.markdown("#### ¿Cómo se conecta tu perfil con una empresa?")
    empresas = consultar("MATCH (e:Empresa) RETURN e.id AS id, e.nombre AS nombre ORDER BY nombre") or []
    if not empresas:
        st.info("No hay empresas para explorar.")
        return
    nombres = {e["id"]: e["nombre"] for e in empresas}
    with st.form("consulta_ruta_usuario"):
        empresa = st.selectbox("Empresa de destino", list(nombres), format_func=lambda x: nombres[x])
        buscar = st.form_submit_button("Explorar conexión")
    if not buscar:
        return
    filas = consultar(
        f"""
        MATCH (u:Usuario {{id: $u}}), (e:Empresa {{id: $e}})
        MATCH ruta = shortestPath((u)-[:{RELACIONES_RUTA}*..6]-(e))
        RETURN [n IN nodes(ruta) | coalesce(n.nombre, n.titulo, n.id)] AS nodos,
               [r IN relationships(ruta) | type(r)] AS relaciones,
               length(ruta) AS pasos
        LIMIT 1
        """,
        u=usuario_id, e=empresa,
    )
    if filas:
        st.success(f"Hay una ruta de {filas[0]['pasos']} pasos.")
        st.markdown(" → ".join(escape(str(n)) for n in filas[0]["nodos"]))
        st.caption("Relaciones recorridas: " + " → ".join(filas[0]["relaciones"]))
    else:
        st.info("No encontramos una ruta de hasta seis relaciones con los datos actuales.")


def renderizar(cuenta, pagina):
    usuario_id = cuenta.get("entidad_id")
    if not usuario_id:
        st.error("La cuenta no tiene un perfil de usuario asociado.")
        return
    perfil_fila = _perfil_usuario(usuario_id)
    if not perfil_fila:
        st.error("No se encontró tu perfil en Neo4j Aura.")
        return
    perfil = perfil_fila["perfil"] or {}
    st.session_state["usuario_id_actual"] = usuario_id

    if pagina == "Inicio":
        _inicio(usuario_id, perfil)
    elif pagina == "Mi perfil":
        _mi_perfil(usuario_id, perfil)
    elif pagina == "Mi red":
        _mi_red(usuario_id)
    elif pagina == "Usuarios":
        _directorio_usuarios(usuario_id)
    elif pagina == "Empresas":
        _directorio_empresas(usuario_id)
    elif pagina == "Ofertas":
        _ofertas(usuario_id)
    elif pagina == "Proyectos":
        _proyectos(usuario_id)
    elif pagina == "Recomendaciones":
        _recomendaciones_pagina(usuario_id)
    elif pagina == "Consultas":
        _consulta_ruta(usuario_id)
    elif pagina == "Mensajes":
        messages_ui.renderizar(cuenta)
