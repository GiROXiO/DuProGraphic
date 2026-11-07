from datetime import date

import streamlit as st
from backend_core.connection import get_db_connection, invalidar_cache_datos


ETIQUETAS = {
    "Usuarios": "Usuario",
    "Empresas": "Empresa",
    "Habilidades": "Habilidad",
    "Proyectos": "Proyecto",
    "Ofertas": "Oferta",
}


def _conexion():
    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j. Revisa la conexión y el archivo .env.")
        return None
    return conn


@st.cache_data(ttl=15, show_spinner=False)
def _opciones_cacheadas(etiqueta, solo_publicadas=False):
    conn = get_db_connection()
    if conn is None or conn.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j.")
    filtro_publicacion = (
        "MATCH (:Empresa)-[:PUBLICA]->(n)"
        if solo_publicadas and etiqueta == "Oferta"
        else ""
    )
    with conn.driver.session() as session:
        filas = session.run(
            f"""
            MATCH (n:{etiqueta})
            {filtro_publicacion}
            RETURN DISTINCT n.id AS id, coalesce(n.nombre, n.titulo, n.id) AS nombre
            ORDER BY nombre
            """
        ).data()
    return {str(fila["id"]): str(fila["nombre"]) for fila in filas}


def _opciones(etiqueta, solo_publicadas=False):
    """Devuelve IDs y nombres para los selectores, usando etiquetas controladas."""
    if etiqueta not in ETIQUETAS.values():
        st.error("Tipo de entidad no permitido.")
        return None
    try:
        return _opciones_cacheadas(etiqueta, solo_publicadas)
    except Exception as error:
        st.error(f"No se pudieron cargar los registros: {error}")
        return None


def _selector(etiqueta, titulo, clave, solo_publicadas=False):
    opciones = _opciones(etiqueta, solo_publicadas=solo_publicadas)
    if opciones is None:
        return None
    if not opciones:
        if solo_publicadas and etiqueta == "Oferta":
            st.warning("No hay ofertas publicadas disponibles para seleccionar.")
        else:
            st.warning(f"No hay registros de {etiqueta} para seleccionar.")
        return None
    return st.selectbox(
        titulo,
        list(opciones),
        format_func=lambda registro_id: f"{opciones[registro_id]} (ID: {registro_id})",
        key=clave,
    )


def _ejecutar(consulta, **parametros):
    conn = _conexion()
    if conn is None:
        return False
    try:
        with conn.driver.session() as session:
            resultado = session.run(consulta, **parametros).single()
        ok = resultado is not None and resultado["ok"]
        if ok:
            invalidar_cache_datos()
        return ok
    except Exception as error:
        st.error(f"Neo4j no pudo completar la operación: {error}")
        return False

def renderizar_vinculaciones():
    st.subheader("Crear vínculos de la red profesional")
    tipo = st.selectbox(
        "Vínculo que quieres crear",
        [
            "Conectar dos usuarios",
            "Asignar habilidad a usuario",
            "Vincular usuario con empresa",
            "Vincular usuario con proyecto",
            "Publicar oferta desde empresa",
            "Asociar habilidad requerida a oferta",
        ],
        key="tipo_vinculacion",
    )

    with st.form("form_vinculacion"):
        if tipo == "Conectar dos usuarios":
            usuario_a = _selector("Usuario", "Primer usuario", "vinculo_usuario_a")
            usuario_b = _selector("Usuario", "Segundo usuario", "vinculo_usuario_b")
            fuerza = st.selectbox("Fuerza de la conexión", ["baja", "media", "alta"])
            enviar = st.form_submit_button("Crear conexión")

        elif tipo == "Asignar habilidad a usuario":
            usuario = _selector("Usuario", "Usuario", "habilidad_usuario")
            habilidad = _selector("Habilidad", "Habilidad", "usuario_habilidad")
            nivel = st.selectbox("Nivel de dominio", ["básico", "intermedio", "avanzado"])
            enviar = st.form_submit_button("Asignar habilidad")

        elif tipo == "Vincular usuario con empresa":
            usuario = _selector("Usuario", "Usuario", "trabajo_usuario")
            empresa = _selector("Empresa", "Empresa", "trabajo_empresa")
            cargo = st.text_input("Cargo")
            actual = st.checkbox("Es el trabajo actual", value=True)
            enviar = st.form_submit_button("Guardar vínculo laboral")

        elif tipo == "Vincular usuario con proyecto":
            usuario = _selector("Usuario", "Usuario", "proyecto_usuario")
            proyecto = _selector("Proyecto", "Proyecto", "usuario_proyecto")
            rol = st.text_input("Rol en el proyecto")
            enviar = st.form_submit_button("Guardar participación")

        elif tipo == "Publicar oferta desde empresa":
            empresa = _selector("Empresa", "Empresa", "publicar_empresa")
            oferta = _selector("Oferta", "Oferta", "publicar_oferta")
            fecha_publicacion = st.date_input("Fecha de publicación", value=date.today())
            enviar = st.form_submit_button("Publicar oferta")
        else:
            oferta = _selector("Oferta", "Oferta", "requisito_oferta")
            habilidad = _selector("Habilidad", "Habilidad requerida", "requisito_habilidad")
            obligatoria = st.checkbox("Es obligatoria", value=True)
            enviar = st.form_submit_button("Guardar requisito")

    if not enviar:
        return

    if tipo == "Conectar dos usuarios":
        if not usuario_a or not usuario_b or usuario_a == usuario_b:
            st.warning("Selecciona dos usuarios distintos.")
            return
        consulta = """
        MATCH (a:Usuario {id: $usuario_a}), (b:Usuario {id: $usuario_b})
        WITH a, b,
             EXISTS { MATCH (a)-[:CONECTA_CON]->(b) } OR
             EXISTS { MATCH (b)-[:CONECTA_CON]->(a) } AS ya_existia
        MERGE (a)-[ab:CONECTA_CON]->(b)
        SET ab.fuerza_conexion = $fuerza
        MERGE (b)-[ba:CONECTA_CON]->(a)
        SET ba.fuerza_conexion = $fuerza
        RETURN ya_existia
        """
        conn = _conexion()
        if conn is None:
            return
        try:
            with conn.driver.session() as session:
                resultado = session.run(
                    consulta,
                    usuario_a=usuario_a,
                    usuario_b=usuario_b,
                    fuerza=fuerza,
                ).single()
            if resultado is not None:
                invalidar_cache_datos()
            if resultado is None:
                st.warning("No se encontraron los dos usuarios seleccionados.")
            elif resultado["ya_existia"]:
                st.info("La conexión ya existía; quedó sincronizada en ambos sentidos.")
            else:
                st.success("Conexión profesional creada en ambos sentidos.")
        except Exception as error:
            st.error(f"No se pudo guardar la conexión: {error}")

    elif tipo == "Asignar habilidad a usuario":
        consulta = """
        MATCH (u:Usuario {id: $usuario}), (h:Habilidad {id: $habilidad})
        MERGE (u)-[r:TIENE_HABILIDAD]->(h)
        SET r.nivel_dominio = $nivel
        RETURN count(r) > 0 AS ok
        """
        if usuario and habilidad and _ejecutar(consulta, usuario=usuario, habilidad=habilidad, nivel=nivel):
            st.success("Habilidad vinculada al usuario.")

    elif tipo == "Vincular usuario con empresa":
        if not usuario or not empresa or not cargo.strip():
            st.warning("Selecciona el usuario y la empresa e indica el cargo.")
            return
        consulta = """
        MATCH (u:Usuario {id: $usuario}), (e:Empresa {id: $empresa})
        MERGE (u)-[r:TRABAJA_EN]->(e)
        SET r.cargo = $cargo, r.es_actual = $actual
        RETURN count(r) > 0 AS ok
        """
        if _ejecutar(consulta, usuario=usuario, empresa=empresa, cargo=cargo.strip(), actual=actual):
            st.success("Vínculo laboral guardado.")

    elif tipo == "Vincular usuario con proyecto":
        if not usuario or not proyecto or not rol.strip():
            st.warning("Selecciona el usuario y el proyecto e indica su rol.")
            return
        consulta = """
        MATCH (u:Usuario {id: $usuario}), (p:Proyecto {id: $proyecto})
        MERGE (u)-[r:PARTICIPA_EN]->(p)
        SET r.rol = $rol
        RETURN count(r) > 0 AS ok
        """
        if _ejecutar(consulta, usuario=usuario, proyecto=proyecto, rol=rol.strip()):
            st.success("Participación en el proyecto guardada.")

    elif tipo == "Publicar oferta desde empresa":
        if not empresa or not oferta:
            st.warning("Selecciona la empresa y la oferta que va a publicar.")
            return
        conn = _conexion()
        if conn is None:
            return
        try:
            with conn.driver.session() as session:
                def publicar(tx):
                    registro = tx.run(
                        """
                        MATCH (e:Empresa {id: $empresa}), (o:Oferta {id: $oferta})
                        OPTIONAL MATCH (publicador:Empresa)-[:PUBLICA]->(o)
                        RETURN collect(DISTINCT publicador.id) AS publicadores
                        """,
                        empresa=empresa,
                        oferta=oferta,
                    ).single()
                    if registro is None:
                        return "no_encontrado"

                    publicadores = [id_empresa for id_empresa in registro["publicadores"] if id_empresa]
                    if any(id_empresa != empresa for id_empresa in publicadores):
                        return "otra_empresa"

                    ya_publicada = empresa in publicadores
                    tx.run(
                        """
                        MATCH (e:Empresa {id: $empresa}), (o:Oferta {id: $oferta})
                        MERGE (e)-[r:PUBLICA]->(o)
                        ON CREATE SET r.fecha_publicacion = $fecha
                        ON MATCH SET r.fecha_publicacion = $fecha
                        """,
                        empresa=empresa,
                        oferta=oferta,
                        fecha=fecha_publicacion.isoformat(),
                    ).consume()
                    return "actualizada" if ya_publicada else "creada"

                resultado = session.execute_write(publicar)

            if resultado == "creada":
                invalidar_cache_datos()
                st.success("Oferta publicada por la empresa.")
            elif resultado == "actualizada":
                invalidar_cache_datos()
                st.info("La oferta ya estaba publicada por esta empresa; se actualizó la fecha.")
            elif resultado == "otra_empresa":
                st.error("Esta oferta ya está publicada por otra empresa.")
            else:
                st.warning("No se encontró la empresa o la oferta seleccionadas.")
        except Exception as error:
            st.error(f"No se pudo publicar la oferta: {error}")
    else:
        consulta = """
        MATCH (o:Oferta {id: $oferta}), (h:Habilidad {id: $habilidad})
        MERGE (o)-[r:REQUIERE]->(h)
        SET r.es_obligatoria = $obligatoria
        RETURN count(r) > 0 AS ok
        """
        if oferta and habilidad and _ejecutar(
            consulta, oferta=oferta, habilidad=habilidad, obligatoria=obligatoria
        ):
            st.success("Habilidad requerida vinculada a la oferta.")


def renderizar_portal():
    st.subheader("Postularse a una oferta")
    with st.form("form_postulacion"):
        usuario = _selector("Usuario", "Usuario", "postulacion_usuario")
        oferta = _selector(
            "Oferta", "Oferta", "postulacion_oferta", solo_publicadas=True
        )
        enviar = st.form_submit_button("Enviar postulación")

    if not enviar:
        return
    if not usuario or not oferta:
        st.warning("Selecciona un usuario y una oferta.")
        return

    consulta_estado = """
    MATCH (u:Usuario {id: $usuario}), (o:Oferta {id: $oferta})
    RETURN
        toLower(trim(coalesce(o.estado, ''))) AS estado,
        EXISTS { MATCH (:Empresa)-[:PUBLICA]->(o) } AS publicada,
        EXISTS { MATCH (u)-[:POSTULA_A]->(o) } AS ya_postulado
    """
    conn = _conexion()
    if conn is None:
        return

    try:
        with conn.driver.session() as session:
            def registrar(tx):
                actual = tx.run(
                    consulta_estado, usuario=usuario, oferta=oferta
                ).single()
                if actual is None:
                    return "no_encontrado"
                if actual["estado"] != "abierta":
                    return "cerrada"
                if not actual["publicada"]:
                    return "no_publicada"
                if actual["ya_postulado"]:
                    return "duplicada"

                tx.run(
                    """
                    MATCH (u:Usuario {id: $usuario}), (o:Oferta {id: $oferta})
                    MERGE (u)-[r:POSTULA_A]->(o)
                    ON CREATE SET
                        r.fecha_postulacion = $fecha,
                        r.estado_proceso = 'aplicado'
                    """,
                    usuario=usuario,
                    oferta=oferta,
                    fecha=date.today().isoformat(),
                ).consume()
                return "creada"

            estado = session.execute_write(registrar)

        if estado == "creada":
            invalidar_cache_datos()
            st.success("Postulación registrada.")
        elif estado == "duplicada":
            st.info("Este usuario ya se había postulado a esa oferta.")
        elif estado == "cerrada":
            st.warning("La oferta está cerrada y no acepta postulaciones.")
        elif estado == "no_publicada":
            st.warning("La oferta todavía no ha sido publicada por una empresa.")
        else:
            st.warning("No se encontró el usuario o la oferta seleccionados.")
    except Exception as error:
        st.error(f"No se pudo registrar la postulación: {error}")

def renderizar_buscador():
    st.subheader("Ruta más corta entre usuario y empresa")
    usuario = _selector("Usuario", "Usuario de origen", "ruta_usuario")
    empresa = _selector("Empresa", "Empresa de destino", "ruta_empresa")
    if not usuario or not empresa:
        return

    if not st.button("Buscar ruta", key="boton_buscar_ruta"):
        return

    consulta = """
    MATCH (u:Usuario {id: $usuario}), (e:Empresa {id: $empresa})
    MATCH ruta = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN|TIENE_HABILIDAD|PARTICIPA_EN|PUBLICA|REQUIERE|POSTULA_A|SIGUE_A|USA_TECNOLOGIA*..6]-(e))
    RETURN
        [n IN nodes(ruta) | coalesce(n.nombre, n.titulo, n.id)] AS nombres,
        [r IN relationships(ruta) | type(r)] AS relaciones,
        length(ruta) AS pasos
    LIMIT 1
    """
    conn = _conexion()
    if conn is None:
        return
    try:
        with conn.driver.session() as session:
            resultado = session.run(consulta, usuario=usuario, empresa=empresa).single()
        if resultado is None:
            st.info("No se encontró una ruta de hasta 6 relaciones entre esos registros.")
            return
        st.success(f"Ruta encontrada en {resultado['pasos']} pasos.")
        st.write(" → ".join(resultado["nombres"]))
        st.caption("Relaciones: " + " → ".join(resultado["relaciones"]))
    except Exception as error:
        st.error(f"No se pudo buscar la ruta: {error}")
