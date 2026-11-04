import streamlit as st
from backend_core.connection import get_db_connection

def renderizar_creacion():
    st.subheader("Registrar entidad")

    entidades = {
        "Usuarios": {
            "label": "Usuario",
            "campos": {
                "nombre": "Nombre",
                "perfil_profesional": "Perfil profesional",
                "universidad": "Universidad",
            },
        },
        "Empresas": {
            "label": "Empresa",
            "campos": {
                "nombre": "Nombre",
                "sector": "Sector",
            },
        },
        "Ofertas": {
            "label": "Oferta",
            "campos": {
                "titulo": "Título",
                "estado": "Estado",
                "modalidad": "Modalidad",
                "nivel_experiencia": "Nivel de experiencia",
            },
        },
    }

    seleccion = st.selectbox("¿Qué quieres registrar?", list(entidades.keys()), key="entidad_crear",)
    config = entidades[seleccion]
    etiqueta = config["label"]

    with st.form(f"form_registrar_{etiqueta}", clear_on_submit=True):
        entidad_id = st.text_input("ID", key=f"crear_{etiqueta}_id")
        valores = {}

        for propiedad, etiqueta_campo in config["campos"].items():
            valores[propiedad] = st.text_input(etiqueta_campo,key=f"crear_{etiqueta}_{propiedad}",)

        guardar = st.form_submit_button("Guardar")

    if not guardar:
        return

    valores_limpios = {
        propiedad: valor.strip()
        for propiedad, valor in valores.items()
    }

    if not entidad_id.strip() or any(not valor for valor in valores_limpios.values()):
        st.warning("Completa todos los campos.")
        return

    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j.")
        return

    try:
        with conn.driver.session() as session:
            resultado = session.run(f"""CREATE (n:{etiqueta} {{id: $id}}) SET n += $propiedades RETURN n.id AS id""", id=entidad_id.strip(), propiedades=valores_limpios,).single()

        st.success(f"{etiqueta} registrado con ID {resultado['id']}.")

    except Exception:
        st.error("No se pudo registrar. Revisa que el ID no exista y que Neo4j esté disponible.")


def renderizar_lectura():
    st.subheader("Consultar registros")

    entidades = {
        "Usuarios": "Usuario",
        "Empresas": "Empresa",
        "Ofertas": "Oferta",
    }
    seleccion = st.selectbox("Entidad que quieres consultar", list(entidades.keys()), key="entidad_lectura",)

    conn = get_db_connection()

    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j. Revisa la conexión.")
        return

    etiqueta = entidades[seleccion]
    consulta = f"""MATCH (n:{etiqueta}) RETURN properties(n) AS registro ORDER BY coalesce(n.nombre, n.titulo, n.id)"""

    try:
        with conn.driver.session() as session:
            registros = [
                fila["registro"]
                for fila in session.run(consulta)
            ]

        if registros:
            st.dataframe(registros, use_container_width=True)
        else:
            st.info(f"No hay registros de {seleccion.lower()} todavía.")

    except Exception:
        st.error("No se pudieron consultar los datos de Neo4j.")


def limpiar_campos_actualizacion():
    for clave in list(st.session_state.keys()):
        if clave.startswith("form_actualizacion_campo_"):
            del st.session_state[clave]

def renderizar_actualizacion():
    st.subheader("Actualizar registros")

    entidades = {
        "Usuarios": {
            "label": "Usuario",
            "campos": {
                "nombre": "Nombre",
                "perfil_profesional": "Perfil profesional",
                "universidad": "Universidad",
            },
        },
        "Empresas": {
            "label": "Empresa",
            "campos": {
                "nombre": "Nombre",
                "sector": "Sector",
            },
        },
        "Ofertas": {
            "label": "Oferta",
            "campos": {
                "titulo": "Título",
                "estado": "Estado",
                "modalidad": "Modalidad",
                "nivel_experiencia": "Nivel de experiencia",
            },
        },
    }

    seleccion = st.selectbox("Entidad que quieres actualizar", list(entidades.keys()), key="entidad_actualizar",on_change=limpiar_campos_actualizacion,)
    config = entidades[seleccion]
    etiqueta = config["label"]

    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j.")
        return

    try:
        with conn.driver.session() as session:
            filas = session.run(f"""MATCH (n:{etiqueta}) RETURN n.id AS id, properties(n) AS datos ORDER BY n.id""").data()
    except Exception:
        st.error("No se pudieron cargar los registros.")
        return

    datos_por_id = {str(fila["id"]): fila["datos"] for fila in filas}

    if not datos_por_id:
        st.info(f"No hay registros de {seleccion.lower()} para actualizar.")
        return

    id_actual = st.selectbox("Registro que quieres editar", list(datos_por_id.keys()), key=f"registro_actualizar_{etiqueta}",on_change=limpiar_campos_actualizacion,)
    datos = datos_por_id[id_actual]

    with st.form(f"form_actualizar_{etiqueta}"):
        id_nuevo = st.text_input("ID", value=id_actual,key=f"form_actualizacion_campo_{etiqueta}_{id_actual}_id",)
        valores = {}

        for propiedad, etiqueta_campo in config["campos"].items():
            valores[propiedad] = st.text_input(etiqueta_campo, value=str(datos.get(propiedad, "")), key=f"form_actualizacion_campo_{etiqueta}_{id_actual}_{propiedad}",)
            

        guardar = st.form_submit_button("Guardar cambios")

    if not guardar:
        return

    if not id_nuevo.strip() or any(not valor.strip() for valor in valores.values()):
        st.warning("Completa todos los campos.")
        return

    asignaciones = ", ".join(
        f"n.{propiedad} = ${propiedad}"
        for propiedad in config["campos"]
    )
    consulta = f"""MATCH (n:{etiqueta} {{id: $id_actual}}) SET n.id = $id_nuevo, {asignaciones} RETURN n.id AS id"""

    parametros = {
        "id_actual": id_actual,
        "id_nuevo": id_nuevo.strip(),
        **{clave: valor.strip() for clave, valor in valores.items()},
    }

    try:
        with conn.driver.session() as session:
            resultado = session.run(consulta, parametros).single()

        if resultado:
            st.success(f"Registro actualizado con ID {resultado['id']}.")
        else:
            st.warning("No se encontró el registro que querías actualizar.")

    except Exception:
        st.error("No se pudo actualizar. Revisa que el ID nuevo no esté ocupado.")



def renderizar_eliminacion():
    st.subheader("Eliminar registros")

    entidades = {
        "Usuarios": "Usuario",
        "Empresas": "Empresa",
        "Ofertas": "Oferta",
    }

    seleccion = st.selectbox(
        "Entidad que quieres eliminar",
        list(entidades.keys()),
        key="entidad_eliminar",
    )
    etiqueta = entidades[seleccion]

    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j.")
        return

    try:
        with conn.driver.session() as session:
            filas = session.run(
                f"""
                MATCH (n:{etiqueta})
                RETURN n.id AS id, coalesce(n.nombre, n.titulo, n.id) AS nombre
                ORDER BY nombre
                """
            ).data()
    except Exception:
        st.error("No se pudieron cargar los registros.")
        return

    nombres_por_id = {
        str(fila["id"]): fila["nombre"]
        for fila in filas
    }

    if not nombres_por_id:
        st.info(f"No hay registros de {seleccion.lower()} para eliminar.")
        return

    id_eliminar = st.selectbox(
        "Registro que quieres eliminar",
        list(nombres_por_id.keys()),
        format_func=lambda id_registro: (
            f"{nombres_por_id[id_registro]} (ID: {id_registro})"
        ),
        key=f"registro_eliminar_{etiqueta}",
    )

    st.warning(
        "Esta acción modifica la base compartida de Aura y elimina "
        "también las relaciones directas de ese registro."
    )

    confirmar = st.checkbox(
        f"Confirmo eliminar {nombres_por_id[id_eliminar]} (ID: {id_eliminar})",
        key=f"confirmar_eliminar_{etiqueta}_{id_eliminar}",
    )

    if not st.button(
        "Eliminar registro",
        type="primary",
        disabled=not confirmar,
        key=f"boton_eliminar_{etiqueta}",
    ):
        return

    try:
        with conn.driver.session() as session:
            if etiqueta == "Empresa":
                tiene_ofertas = session.run(
                    """
                    MATCH (e:Empresa {id: $id})-[:PUBLICA]->(:Oferta)
                    RETURN count(*) > 0 AS tiene_ofertas
                    """,
                    id=id_eliminar,
                ).single()["tiene_ofertas"]

                if tiene_ofertas:
                    st.error(
                        "Primero elimina las ofertas publicadas por esta empresa."
                    )
                    return

            session.run(
                f"""
                MATCH (n:{etiqueta} {{id: $id}})
                DETACH DELETE n
                """,
                id=id_eliminar,
            ).consume()

        st.success(f"Registro {id_eliminar} eliminado.")

    except Exception:
        st.error("No se pudo eliminar el registro.")