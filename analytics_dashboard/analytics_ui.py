from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st
from backend_core.connection import get_db_connection


CONSULTAS = Path(__file__).resolve().parent / "consultas_cypher"


@st.cache_data(ttl=15, show_spinner=False)
def _consultar_cacheada(consulta, parametros):
    conn = get_db_connection()
    if conn is None or conn.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j. Revisa la conexión y el archivo .env.")
    with conn.driver.session() as session:
        return session.run(consulta, **parametros).data()


def _consultar(consulta, **parametros):
    try:
        return _consultar_cacheada(consulta, parametros)
    except Exception as error:
        st.error(f"No se pudo ejecutar la consulta: {error}")
        return None


def _consultar_archivo(nombre, **parametros):
    ruta = CONSULTAS / nombre
    try:
        consulta = ruta.read_text(encoding="utf-8-sig")
    except OSError as error:
        st.error(f"No se pudo leer la consulta {nombre}: {error}")
        return None
    return _consultar(consulta, **parametros)


def _opciones(etiqueta):
    # Las etiquetas son constantes internas, nunca valores introducidos por el usuario.
    if etiqueta not in {"Usuario", "Empresa", "Oferta"}:
        st.error("Tipo de entidad no permitido.")
        return None
    filas = _consultar(
        f"""
        MATCH (n:{etiqueta})
        RETURN n.id AS id, coalesce(n.nombre, n.titulo, n.id) AS nombre
        ORDER BY nombre
        """
    )
    if filas is None:
        return None
    return {str(fila["id"]): str(fila["nombre"]) for fila in filas}


def _selector(opciones, titulo, clave):
    if opciones is None:
        return None
    if not opciones:
        st.info("No hay registros disponibles para esta consulta.")
        return None
    return st.selectbox(
        titulo,
        list(opciones),
        format_func=lambda registro_id: f"{opciones[registro_id]} (ID: {registro_id})",
        key=clave,
    )


def _mostrar(filas, mensaje_vacio="No se encontraron resultados."):
    if filas is None:
        return
    if filas:
        st.dataframe(filas, width="stretch", hide_index=True)
    else:
        st.info(mensaje_vacio)


def _detectar_comunidades(filas, max_iteraciones=30):
    """Agrupa usuarios con propagación de etiquetas sobre CONECTA_CON."""
    nombres = {fila["usuario_id"]: fila["usuario"] for fila in filas}
    grafo = {usuario_id: set() for usuario_id in nombres}
    for fila in filas:
        usuario_id = fila["usuario_id"]
        for contacto_id in fila["contactos_ids"] or []:
            if contacto_id is not None:
                nombres.setdefault(contacto_id, contacto_id)
                grafo.setdefault(usuario_id, set()).add(contacto_id)
                grafo.setdefault(contacto_id, set()).add(usuario_id)

    etiquetas = {usuario_id: usuario_id for usuario_id in grafo}
    for _ in range(max_iteraciones):
        cambios = False
        for usuario_id in sorted(grafo):
            vecinos = grafo[usuario_id]
            if not vecinos:
                continue
            frecuencias = Counter(etiquetas[vecino] for vecino in vecinos)
            frecuencia_maxima = max(frecuencias.values())
            etiqueta_ganadora = min(
                etiqueta
                for etiqueta, frecuencia in frecuencias.items()
                if frecuencia == frecuencia_maxima
            )
            if etiquetas[usuario_id] != etiqueta_ganadora:
                etiquetas[usuario_id] = etiqueta_ganadora
                cambios = True
        if not cambios:
            break

    grupos = defaultdict(list)
    for usuario_id, etiqueta in etiquetas.items():
        grupos[etiqueta].append(usuario_id)
    grupos_ordenados = sorted(
        (sorted(miembros) for miembros in grupos.values()),
        key=lambda miembros: (-len(miembros), miembros[0]),
    )
    return [
        {
            "comunidad": numero,
            "usuarios": len(miembros),
            "miembros": ", ".join(nombres.get(usuario_id, usuario_id) for usuario_id in miembros),
        }
        for numero, miembros in enumerate(grupos_ordenados, start=1)
    ]

def renderizar_recomendaciones():
    st.subheader("Recomendaciones de la red profesional")
    tipo = st.selectbox(
        "Tipo de recomendación",
        [
            "Contactos",
            "Colaboradores",
            "Ofertas de empleo para un usuario",
            "Candidatos para una oferta",
            "Contactos en común",
            "Usuarios con habilidades similares",
        ],
        key="tipo_recomendacion_analitica",
    )

    consultas_comparativas = {
        "Contactos en común": "contactos_en_comun.cypher",
        "Usuarios con habilidades similares": "habilidades_similares.cypher",
    }
    if tipo in consultas_comparativas:
        _mostrar(_consultar_archivo(consultas_comparativas[tipo]))
        return

    if tipo == "Candidatos para una oferta":
        opciones = _opciones("Oferta")
        with st.form("form_recomendar_candidatos"):
            oferta_id = _selector(opciones, "Oferta", "recomendar_oferta_id")
            consultar = st.form_submit_button("Buscar candidatos")
        if consultar and oferta_id:
            _mostrar(
                _consultar_archivo(
                    "candidatos_recomendados_para_oferta.cypher", oferta_id=oferta_id
                ),
                "No se encontraron candidatos con habilidades requeridas.",
            )
        return

    if tipo == "Ofertas de empleo para un usuario":
        opciones = _opciones("Usuario")
        with st.form("form_recomendar_empleos"):
            usuario_id = _selector(
                opciones, "Usuario", "recomendar_empleos_usuario_id"
            )
            consultar = st.form_submit_button("Buscar ofertas recomendadas")
        if consultar and usuario_id:
            _mostrar(
                _consultar_archivo(
                    "recomendaciones_empleos.cypher", usuario_id=usuario_id
                ),
                "No se encontraron ofertas abiertas que coincidan con sus habilidades.",
            )
        return

    opciones = _opciones("Usuario")
    archivo = (
        "recomendaciones_contactos.cypher"
        if tipo == "Contactos"
        else "recomendaciones_colaboradores.cypher"
    )
    texto_boton = "Buscar contactos" if tipo == "Contactos" else "Buscar colaboradores"
    with st.form("form_recomendacion_usuario"):
        usuario_id = _selector(opciones, "Usuario", "recomendar_usuario_id")
        consultar = st.form_submit_button(texto_boton)
    if consultar and usuario_id:
        _mostrar(
            _consultar_archivo(archivo, usuario_id=usuario_id),
            "No hay recomendaciones para este usuario con los datos actuales.",
        )


def renderizar_metricas():
    st.subheader("Inteligencia de mercado")
    conteos = _consultar(
        """
        MATCH (n)
        RETURN labels(n)[0] AS entidad, count(*) AS cantidad
        ORDER BY entidad
        """
    )
    if conteos is None:
        return
    totales = {fila["entidad"]: fila["cantidad"] for fila in conteos}
    columnas = st.columns(5)
    etiquetas_metricas = {
        "Usuario": "Usuarios",
        "Empresa": "Empresas",
        "Oferta": "Ofertas",
        "Habilidad": "Habilidades",
        "Proyecto": "Proyectos",
    }
    for columna, entidad in zip(columnas, etiquetas_metricas):
        columna.metric(etiquetas_metricas[entidad], totales.get(entidad, 0))

    indicador = st.radio(
        "Indicador",
        ["Usuarios influyentes", "Habilidades demandadas", "Comunidades"],
        horizontal=True,
        label_visibility="collapsed",
        key="indicador_mercado",
    )
    if indicador == "Usuarios influyentes":
        filas = _consultar_archivo("usuarios_mas_influyentes.cypher")
        _mostrar(filas)
    elif indicador == "Habilidades demandadas":
        filas = _consultar_archivo("habilidades_mas_demandadas.cypher")
        _mostrar(filas)
    else:
        st.caption("Comunidades calculadas con Label Propagation sobre CONECTA_CON; no requiere GDS.")
        filas = _consultar_archivo("comunidades_detectadas.cypher")
        if filas is not None:
            _mostrar(_detectar_comunidades(filas), "No hay usuarios para agrupar.")


def renderizar_grafo():
    st.subheader("Análisis de rutas y proyectos")
    analisis = st.radio(
        "Tipo de análisis",
        ["Ruta usuario–empresa", "Proyectos con miembros", "Proyectos con tecnologías"],
        horizontal=True,
        label_visibility="collapsed",
        key="tipo_analisis_red",
    )

    if analisis == "Ruta usuario–empresa":
        usuarios = _opciones("Usuario")
        empresas = _opciones("Empresa")
        with st.form("form_ruta_analitica"):
            usuario_id = _selector(usuarios, "Usuario de origen", "ruta_analitica_usuario")
            empresa_id = _selector(empresas, "Empresa de destino", "ruta_analitica_empresa")
            consultar = st.form_submit_button("Buscar ruta más corta")
        if consultar and usuario_id and empresa_id:
            _mostrar(
                _consultar_archivo(
                    "ruta_mas_corta_usuario_empresa.cypher",
                    usuario_id=usuario_id,
                    empresa_id=empresa_id,
                ),
                "No se encontró una ruta entre ese usuario y esa empresa.",
            )

    elif analisis == "Proyectos con miembros":
        _mostrar(_consultar_archivo("proyectos_miembros_compartidos.cypher"))
    else:
        _mostrar(_consultar_archivo("proyectos_tecnologias_compartidas.cypher"))
