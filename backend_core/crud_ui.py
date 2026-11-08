import re
from datetime import date

import streamlit as st
from backend_core.connection import get_db_connection, invalidar_cache_datos
from backend_core.auth import ROL_EMPRESA, ROL_USUARIO, crear_perfil_con_acceso_admin


OPCIONES_OFERTA = {
    "estado": ["abierta", "cerrada"],
    "modalidad": ["remoto", "híbrido", "presencial"],
    "nivel_experiencia": ["Junior", "Semi-Senior", "Senior"],
}
PREFIJOS_ID = {"Usuario": "U", "Empresa": "E", "Oferta": "O", "Proyecto": "P"}
LIMITES_CAMPOS = {
    ("Usuario", "nombre"): 140,
    ("Usuario", "perfil_profesional"): 180,
    ("Usuario", "universidad"): 160,
    ("Empresa", "nombre"): 140,
    ("Empresa", "sector"): 120,
    ("Oferta", "titulo"): 160,
    ("Proyecto", "nombre"): 140,
    ("Proyecto", "descripcion"): 1000,
}


def _id_valido(etiqueta, valor):
    prefijo = PREFIJOS_ID.get(etiqueta)
    return bool(prefijo and re.fullmatch(rf"{prefijo}[A-Za-z0-9_-]{{1,63}}", str(valor or "").strip()))


def _campo_entidad(etiqueta, propiedad, nombre, key, valor=None):
    opciones = OPCIONES_OFERTA.get(propiedad) if etiqueta == "Oferta" else None
    if not opciones:
        max_chars = LIMITES_CAMPOS.get((etiqueta, propiedad), 240)
        if propiedad == "descripcion":
            return st.text_area(nombre, value=valor or "", max_chars=max_chars, key=key)
        return st.text_input(nombre, value=valor or "", max_chars=max_chars, key=key)
    opciones = list(opciones)
    if valor not in (None, "") and valor not in opciones:
        opciones.insert(0, valor)
        st.warning(f"El valor actual de {nombre.lower()} no está entre las opciones válidas; selecciona uno permitido.")
    indice = opciones.index(valor) if valor in opciones else 0
    return st.selectbox(nombre, opciones, index=indice, key=key)


@st.cache_data(ttl=15, show_spinner=False)
def _cargar_registros_cacheados(etiqueta):
    if etiqueta not in {"Usuario", "Empresa", "Oferta", "Proyecto"}:
        raise ValueError("Tipo de entidad no permitido.")
    conn = get_db_connection()
    if conn is None or conn.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j.")
    with conn.driver.session() as session:
        return session.run(
            f"""
            MATCH (n:{etiqueta})
            OPTIONAL MATCH (empresa:Empresa)-[:PUBLICA_PROYECTO]->(n)
            OPTIONAL MATCH (empresa_oferta:Empresa)-[:PUBLICA]->(:Oferta)-[:PERTENECE_A]->(n)
            OPTIONAL MATCH (empresa_publica:Empresa)-[:PUBLICA]->(n)
            RETURN n.id AS id, properties(n) AS datos,
                   coalesce(n.nombre, n.titulo, n.id) AS nombre,
                   coalesce(head(collect(DISTINCT empresa.id)),
                            head(collect(DISTINCT empresa_oferta.id))) AS empresa_id,
                   head(collect(DISTINCT empresa_publica.id)) AS empresa_publicadora_id
            ORDER BY nombre
            """
        ).data()


@st.cache_data(ttl=15, show_spinner=False)
def _cargar_empresas_cacheadas():
    conn = get_db_connection()
    if conn is None or conn.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j.")
    with conn.driver.session() as session:
        return session.run(
            "MATCH (e:Empresa) RETURN e.id AS id, e.nombre AS nombre ORDER BY nombre"
        ).data()


def _cargar_empresas():
    try:
        return _cargar_empresas_cacheadas()
    except Exception as error:
        st.error(f"No se pudieron cargar las empresas: {error}")
        return None


def _cargar_registros(etiqueta):
    try:
        return _cargar_registros_cacheados(etiqueta)
    except Exception as error:
        st.error(f"No se pudieron cargar los registros: {error}")
        return None


def renderizar_creacion(entidad_fija=None):
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
            "campos": {"nombre": "Nombre", "sector": "Sector"},
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
        "Proyectos": {
            "label": "Proyecto",
            "campos": {"nombre": "Nombre", "descripcion": "Descripción"},
        },
    }

    if entidad_fija is not None and entidad_fija not in entidades:
        st.error("Categoría de datos no válida.")
        return
    seleccion = entidad_fija or st.selectbox(
        "¿Qué quieres registrar?", list(entidades.keys()), key="entidad_crear"
    )
    config = entidades[seleccion]
    etiqueta = config["label"]

    empresas = None
    if etiqueta in {"Oferta", "Proyecto"}:
        empresas = _cargar_empresas()
        if empresas is None:
            return
        if etiqueta == "Oferta" and not empresas:
            st.info("Registra una empresa antes de crear una oferta.")
            return
        empresas_por_id = {e["id"]: e["nombre"] for e in empresas}

    with st.form(f"form_registrar_{etiqueta}", clear_on_submit=True):
        entidad_id = st.text_input("ID", max_chars=64, key=f"crear_{etiqueta}_id")
        valores = {
            propiedad: _campo_entidad(
                etiqueta,
                propiedad,
                etiqueta_campo,
                key=f"crear_{etiqueta}_{propiedad}",
            )
            for propiedad, etiqueta_campo in config["campos"].items()
        }
        correo = ""
        password = ""
        empresa_id = ""
        if etiqueta == "Oferta":
            empresa_id = st.selectbox(
                "Empresa que publica la oferta",
                list(empresas_por_id),
                format_func=lambda x: empresas_por_id[x],
            )
        elif etiqueta == "Proyecto" and empresas:
            opciones_empresa = {"": "Sin empresa vinculada"} | empresas_por_id
            empresa_id = st.selectbox(
                "Organización responsable (opcional)",
                list(opciones_empresa),
                format_func=lambda x: opciones_empresa[x],
            )
        if etiqueta in {"Usuario", "Empresa"}:
            st.markdown("#### Acceso inicial")
            correo = st.text_input("Correo / usuario", max_chars=254, key=f"crear_{etiqueta}_correo")
            password = st.text_input(
                "Contraseña inicial (10 a 256 caracteres)", max_chars=256,
                type="password",
                key=f"crear_{etiqueta}_password",
            )
        guardar = st.form_submit_button("Guardar")

    if not guardar:
        return

    valores_limpios = {
        propiedad: (valor or "").strip()
        for propiedad, valor in valores.items()
    }
    if not entidad_id.strip() or any(not valor for valor in valores_limpios.values()):
        st.warning("Completa el ID y todos los campos.")
        return
    if not _id_valido(etiqueta, entidad_id):
        st.warning(f"El ID debe comenzar con {PREFIJOS_ID[etiqueta]} y usar solo letras, números, guion o guion bajo (máximo 64 caracteres).")
        return

    if etiqueta in {"Oferta", "Proyecto"}:
        if etiqueta == "Proyecto":
            conn = get_db_connection()
            if conn is None or conn.driver is None:
                st.error("No se pudo conectar con Neo4j.")
                return
            try:
                with conn.driver.session() as session:
                    def crear_proyecto(tx):
                        if tx.run("MATCH (p:Proyecto {id: $id}) RETURN p.id AS id", id=entidad_id.strip()).single():
                            return "id_existente", None
                        if empresa_id and not tx.run("MATCH (:Empresa {id: $id}) RETURN 1 AS ok", id=empresa_id).single():
                            return "empresa_no_encontrada", None
                        creado = tx.run(
                            "CREATE (p:Proyecto {id: $id}) SET p += $propiedades "
                            "WITH p OPTIONAL MATCH (e:Empresa {id: $empresa}) "
                            "FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END | "
                            "MERGE (e)-[:PUBLICA_PROYECTO]->(p)) RETURN p.id AS id",
                            id=entidad_id.strip(), propiedades=valores_limpios,
                            empresa=empresa_id,
                        ).single()
                        return ("creado", creado["id"]) if creado else ("error", None)

                    estado, creado_id = session.execute_write(crear_proyecto)
                if estado == "creado":
                    invalidar_cache_datos()
                    st.success(f"Proyecto registrado con ID {creado_id}.")
                elif estado == "id_existente":
                    st.warning(f"Ya existe un proyecto con ID {entidad_id.strip()}.")
                elif estado == "empresa_no_encontrada":
                    st.warning("La empresa seleccionada ya no está disponible. Recarga y vuelve a intentarlo.")
            except Exception:
                st.error("No se pudo registrar el proyecto.")
            return

        for propiedad, opciones in OPCIONES_OFERTA.items():
            if valores_limpios[propiedad] not in opciones:
                st.warning(
                    f"Selecciona un valor válido para {propiedad.replace('_', ' ')}."
                )
                return
        conn = get_db_connection()
        if conn is None or conn.driver is None:
            st.error("No se pudo conectar con Neo4j.")
            return

        def crear_oferta(tx):
            empresa = tx.run(
                "MATCH (e:Empresa {id: $id}) RETURN e.id AS id",
                id=empresa_id,
            ).single()
            if not empresa:
                return "empresa_no_encontrada", None
            existente = tx.run(
                "MATCH (o:Oferta {id: $id}) RETURN o.id AS id",
                id=entidad_id.strip(),
            ).single()
            if existente:
                return "id_existente", None
            resultado = tx.run(
                """
                MATCH (e:Empresa {id: $empresa})
                CREATE (o:Oferta {id: $id})
                SET o += $propiedades
                CREATE (e)-[:PUBLICA]->(o)
                RETURN o.id AS id
                """,
                id=entidad_id.strip(),
                propiedades=valores_limpios,
                empresa=empresa_id,
            ).single()
            return ("creada", resultado["id"]) if resultado else ("error", None)

        try:
            with conn.driver.session() as session:
                estado, nuevo_id = session.execute_write(crear_oferta)
            if estado == "creada":
                invalidar_cache_datos()
                st.success(f"Oferta registrada con ID {nuevo_id}.")
            elif estado == "id_existente":
                st.warning(f"Ya existe una oferta con ID {entidad_id.strip()}.")
            elif estado == "empresa_no_encontrada":
                st.warning("La empresa seleccionada ya no está disponible. Recarga y vuelve a intentarlo.")
            else:
                st.error("Neo4j no confirmó la creación de la oferta.")
        except Exception as error:
            st.error(f"No se pudo registrar la oferta. Detalle: {error}")
        return

    rol = ROL_USUARIO if etiqueta == "Usuario" else ROL_EMPRESA
    estado, _ = crear_perfil_con_acceso_admin(
        rol,
        correo,
        password,
        entidad_id,
        valores_limpios,
    )
    if estado == "creada":
        invalidar_cache_datos()
        st.success(
            f"{etiqueta} y cuenta creadas. El correo ingresado será su usuario de acceso."
        )
    elif estado == "correo_existente":
        st.warning("Ya existe una cuenta con ese correo.")
    elif estado == "correo_perfil_existente":
        st.warning("Ese correo ya está asociado a otro perfil.")
    elif estado == "id_existente":
        st.warning(f"Ya existe un perfil con ID {entidad_id.strip()}.")
    elif estado == "id_invalido":
        st.warning("El ID debe empezar con U para usuarios o E para empresas.")
    elif estado == "correo_invalido":
        st.warning("Escribe un correo válido.")
    elif estado == "password_corto":
        st.warning("La contraseña debe tener al menos 10 caracteres.")
    elif estado == "password_largo":
        st.warning("La contraseña no puede superar 256 caracteres.")
    elif estado == "perfil_incompleto":
        st.warning("Completa el titular profesional o el sector del perfil.")
    elif estado == "datos_invalidos":
        st.warning("Revisa los campos: hay un valor demasiado largo o fuera de las opciones permitidas.")
    elif estado == "url_invalida":
        st.warning("El enlace debe ser una dirección web completa que comience con http:// o https://.")
    elif estado == "datos_incompletos":
        st.warning("Completa el ID y el nombre del perfil.")
    else:
        st.error("No se pudo crear el perfil y su cuenta.")


def renderizar_lectura(entidad_fija=None):
    st.subheader("Consultar registros")

    entidades = {
        "Usuarios": "Usuario",
        "Empresas": "Empresa",
        "Ofertas": "Oferta",
        "Proyectos": "Proyecto",
    }
    if entidad_fija is not None and entidad_fija not in entidades:
        st.error("Categoría de datos no válida.")
        return
    seleccion = entidad_fija or st.selectbox("Entidad que quieres consultar", list(entidades.keys()), key="entidad_lectura")

    etiqueta = entidades[seleccion]
    filas = _cargar_registros(etiqueta)
    if filas is None:
        return
    registros = [fila["datos"] for fila in filas]
    if registros:
        st.dataframe(registros, width="stretch", hide_index=True)
    else:
        st.info(f"No hay registros de {seleccion.lower()} todavía.")


def limpiar_campos_actualizacion():
    for clave in list(st.session_state.keys()):
        if clave.startswith("form_actualizacion_campo_"):
            del st.session_state[clave]

def renderizar_actualizacion(entidad_fija=None):
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
        "Proyectos": {
            "label": "Proyecto",
            "campos": {"nombre": "Nombre", "descripcion": "Descripción"},
        },
    }

    if entidad_fija is not None and entidad_fija not in entidades:
        st.error("Categoría de datos no válida.")
        return
    seleccion = entidad_fija or st.selectbox("Entidad que quieres actualizar", list(entidades.keys()), key="entidad_actualizar",on_change=limpiar_campos_actualizacion)
    config = entidades[seleccion]
    etiqueta = config["label"]

    empresas_por_id = {}
    if etiqueta in {"Proyecto", "Oferta"}:
        empresas = _cargar_empresas()
        if empresas is None:
            return
        empresas_por_id = {e["id"]: e["nombre"] for e in empresas}

    filas = _cargar_registros(etiqueta)
    if filas is None:
        return

    datos_por_id = {str(fila["id"]): fila["datos"] for fila in filas}

    if not datos_por_id:
        st.info(f"No hay registros de {seleccion.lower()} para actualizar.")
        return

    id_actual = st.selectbox("Registro que quieres editar", list(datos_por_id.keys()), key=f"registro_actualizar_{etiqueta}",on_change=limpiar_campos_actualizacion,)
    datos = datos_por_id[id_actual]
    empresa_actual = next(
        (
            str(fila.get("empresa_id"))
            for fila in filas
            if str(fila["id"]) == id_actual and fila.get("empresa_id")
        ),
        "",
    )
    empresa_publicadora_actual = next(
        (
            str(fila.get("empresa_publicadora_id"))
            for fila in filas
            if str(fila["id"]) == id_actual and fila.get("empresa_publicadora_id")
        ),
        "",
    )
    opciones_empresa = {"": "Sin empresa vinculada"} | empresas_por_id
    if empresa_actual and empresa_actual not in opciones_empresa:
        opciones_empresa[empresa_actual] = empresa_actual
    opciones_publicadora = {"": "Selecciona una empresa publicadora"} | empresas_por_id
    if empresa_publicadora_actual and empresa_publicadora_actual not in opciones_publicadora:
        opciones_publicadora[empresa_publicadora_actual] = empresa_publicadora_actual

    with st.form(f"form_actualizar_{etiqueta}"):
        id_nuevo = st.text_input("ID", value=id_actual, max_chars=64, key=f"form_actualizacion_campo_{etiqueta}_{id_actual}_id")
        valores = {}

        for propiedad, etiqueta_campo in config["campos"].items():
            valores[propiedad] = _campo_entidad(
                etiqueta,
                propiedad,
                etiqueta_campo,
                key=f"form_actualizacion_campo_{etiqueta}_{id_actual}_{propiedad}",
                valor=str(datos.get(propiedad, "")),
            )

        empresa_nueva = ""
        if etiqueta == "Proyecto":
            empresa_nueva = st.selectbox(
                "Organización responsable",
                list(opciones_empresa),
                index=list(opciones_empresa).index(empresa_actual),
                format_func=lambda x: opciones_empresa[x],
                key=f"proyecto_empresa_{id_actual}",
            )
        empresa_publicadora = ""
        if etiqueta == "Oferta":
            empresa_publicadora = st.selectbox(
                "Empresa que publica la oferta",
                list(opciones_publicadora),
                index=list(opciones_publicadora).index(empresa_publicadora_actual),
                format_func=lambda x: opciones_publicadora[x],
                key=f"oferta_empresa_{id_actual}",
            )

        guardar = st.form_submit_button("Guardar cambios")

    if not guardar:
        return

    if not id_nuevo.strip() or any(not valor.strip() for valor in valores.values()):
        st.warning("Completa todos los campos.")
        return
    if not _id_valido(etiqueta, id_nuevo):
        st.warning(f"El ID debe comenzar con {PREFIJOS_ID[etiqueta]} y usar solo letras, números, guion o guion bajo (máximo 64 caracteres).")
        return

    if etiqueta == "Oferta":
        for propiedad, opciones in OPCIONES_OFERTA.items():
            if valores[propiedad] not in opciones:
                st.warning(f"Selecciona un valor válido para {propiedad.replace('_', ' ')}.")
                return
        if not empresa_publicadora:
            st.warning("Selecciona una empresa para publicar la oferta.")
            return

        conn = get_db_connection()
        if conn is None or conn.driver is None:
            st.error("No se pudo conectar con Neo4j.")
            return

        def actualizar_oferta(tx):
            if not tx.run(
                "MATCH (:Empresa {id: $id}) RETURN 1 AS ok", id=empresa_publicadora
            ).single():
                return "empresa_no_encontrada", None
            if id_nuevo.strip() != id_actual and tx.run(
                "MATCH (o:Oferta {id: $id}) RETURN o.id AS id LIMIT 1",
                id=id_nuevo.strip(),
            ).single():
                return "id_existente", None
            resultado = tx.run(
                """
                MATCH (o:Oferta {id: $id_actual})
                SET o.id = $id_nuevo, o.titulo = $titulo, o.estado = $estado,
                    o.modalidad = $modalidad, o.nivel_experiencia = $experiencia
                WITH o
                OPTIONAL MATCH (publicador_anterior:Empresa)-[anterior:PUBLICA]->(o)
                WITH o, collect({id: publicador_anterior.id,
                                 fecha: anterior.fecha_publicacion}) AS anteriores,
                     collect(anterior) AS relaciones_anteriores
                WITH o,
                     head([r IN anteriores WHERE r.id = $empresa | r.fecha]) AS fecha_actual,
                     relaciones_anteriores
                FOREACH (r IN relaciones_anteriores | DELETE r)
                WITH o, fecha_actual
                MATCH (e:Empresa {id: $empresa})
                CREATE (e)-[:PUBLICA {fecha_publicacion: coalesce(fecha_actual, $fecha)}]->(o)
                RETURN o.id AS id
                """,
                id_actual=id_actual,
                id_nuevo=id_nuevo.strip(),
                titulo=valores["titulo"].strip(),
                estado=valores["estado"],
                modalidad=valores["modalidad"],
                experiencia=valores["nivel_experiencia"],
                empresa=empresa_publicadora,
                fecha=date.today().isoformat(),
            ).single()
            return ("actualizado", resultado["id"]) if resultado else ("no_encontrado", None)

        try:
            with conn.driver.session() as session:
                estado, id_guardado = session.execute_write(actualizar_oferta)
            if estado == "actualizado":
                invalidar_cache_datos()
                st.success(f"Oferta actualizada con ID {id_guardado}.")
            elif estado == "id_existente":
                st.warning(f"El ID {id_nuevo.strip()} ya está asignado a otra oferta.")
            elif estado == "empresa_no_encontrada":
                st.warning("La empresa seleccionada ya no está disponible. Recarga y vuelve a intentarlo.")
            else:
                st.warning("No se encontró la oferta que querías actualizar.")
        except Exception:
            st.error("No se pudo actualizar la oferta. Revisa el ID y la conexión con Neo4j.")
        return

    if etiqueta == "Proyecto":
        conn = get_db_connection()
        if conn is None or conn.driver is None:
            st.error("No se pudo conectar con Neo4j.")
            return

        def actualizar_proyecto(tx):
            if empresa_nueva and not tx.run(
                "MATCH (:Empresa {id: $id}) RETURN 1 AS ok", id=empresa_nueva
            ).single():
                return "empresa_no_encontrada", None
            if id_nuevo.strip() != id_actual and tx.run(
                "MATCH (n:Proyecto {id: $id}) RETURN n.id AS id LIMIT 1",
                id=id_nuevo.strip(),
            ).single():
                return "id_existente", None
            resultado = tx.run(
                """
                MATCH (n:Proyecto {id: $id_actual})
                SET n.id = $id_nuevo, n.nombre = $nombre, n.descripcion = $descripcion
                WITH n
                OPTIONAL MATCH (:Empresa)-[anterior:PUBLICA_PROYECTO]->(n)
                WITH n, collect(anterior) AS relaciones_anteriores
                FOREACH (r IN relaciones_anteriores | DELETE r)
                WITH n
                OPTIONAL MATCH (e:Empresa {id: $empresa})
                FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END |
                    MERGE (e)-[:PUBLICA_PROYECTO]->(n)
                )
                RETURN n.id AS id
                """,
                id_actual=id_actual,
                id_nuevo=id_nuevo.strip(),
                nombre=valores["nombre"].strip(),
                descripcion=valores["descripcion"].strip(),
                empresa=empresa_nueva,
            ).single()
            return ("actualizado", resultado["id"]) if resultado else ("no_encontrado", None)

        try:
            with conn.driver.session() as session:
                estado, id_guardado = session.execute_write(actualizar_proyecto)
            if estado == "actualizado":
                invalidar_cache_datos()
                st.success(f"Proyecto actualizado con ID {id_guardado}.")
            elif estado == "id_existente":
                st.warning(f"El ID {id_nuevo.strip()} ya está asignado a otro proyecto.")
            elif estado == "empresa_no_encontrada":
                st.warning("La empresa seleccionada ya no está disponible. Recarga y vuelve a intentarlo.")
            else:
                st.warning("No se encontró el proyecto que querías actualizar.")
        except Exception as error:
            st.error(f"No se pudo actualizar el proyecto. Revisa el ID y la conexión con Neo4j. Detalle: {error}")
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

    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j.")
        return
    try:
        with conn.driver.session() as session:
            def actualizar(tx):
                if id_nuevo.strip() != id_actual and tx.run(
                    f"MATCH (n:{etiqueta} {{id: $id}}) RETURN n.id AS id LIMIT 1",
                    id=id_nuevo.strip(),
                ).single():
                    return "id_existente", None
                resultado = tx.run(consulta, parametros).single()
                return ("actualizado", resultado) if resultado else ("no_encontrado", None)

            estado, resultado = session.execute_write(actualizar)

        if estado == "actualizado":
            invalidar_cache_datos()
            st.success(f"Registro actualizado con ID {resultado['id']}.")
        elif estado == "id_existente":
            st.warning(f"El ID {id_nuevo.strip()} ya está asignado a otro registro.")
        else:
            st.warning("No se encontró el registro que querías actualizar.")

    except Exception as error:
        codigo = getattr(error, "code", "")
        if "Constraint" in codigo:
            st.warning(f"El ID {id_nuevo.strip()} ya está asignado a otro registro.")
        else:
            st.error("No se pudo actualizar. Revisa el ID y la conexión con Neo4j.")

def renderizar_eliminacion(entidad_fija=None):
    st.subheader("Eliminar registros")

    entidades = {
        "Usuarios": "Usuario",
        "Empresas": "Empresa",
        "Ofertas": "Oferta",
        "Proyectos": "Proyecto",
    }
    if entidad_fija is not None and entidad_fija not in entidades:
        st.error("Categoría de datos no válida.")
        return
    seleccion = entidad_fija or st.selectbox(
        "Entidad que quieres eliminar", list(entidades.keys()), key="entidad_eliminar"
    )
    etiqueta = entidades[seleccion]
    filas = _cargar_registros(etiqueta)
    if filas is None:
        return

    nombres_por_id = {str(fila["id"]): fila["nombre"] for fila in filas}
    if not nombres_por_id:
        st.info(f"No hay registros de {seleccion.lower()} para eliminar.")
        return

    id_eliminar = st.selectbox(
        "Registro que quieres eliminar",
        list(nombres_por_id),
        format_func=lambda item: f"{nombres_por_id[item]} (ID: {item})",
        key=f"registro_eliminar_{etiqueta}",
    )
    if etiqueta in {"Usuario", "Empresa"}:
        st.warning(
            "El perfil y sus relaciones se eliminarán. Su cuenta quedará desactivada "
            "y los mensajes existentes se conservarán."
        )
    else:
        st.warning("El registro y sus relaciones se eliminarán. Revisa antes si otras partes de la red dependen de este elemento.")
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

    conn = get_db_connection()
    if conn is None or conn.driver is None:
        st.error("No se pudo conectar con Neo4j.")
        return

    def eliminar(tx):
        existe = tx.run(
            f"MATCH (n:{etiqueta} {{id: $id}}) RETURN n.id AS id",
            id=id_eliminar,
        ).single()
        if not existe:
            return "no_encontrado"

        if etiqueta == "Empresa":
            ofertas = tx.run(
                """
                MATCH (e:Empresa {id: $id})-[:PUBLICA]->(:Oferta)
                RETURN count(*) AS total
                """,
                id=id_eliminar,
            ).single()["total"]
            if ofertas:
                return "tiene_ofertas"

        if etiqueta in {"Usuario", "Empresa"}:
            account_ids = tx.run(
                f"""
                MATCH (c:Cuenta)-[:REPRESENTA_A]->(p:{etiqueta} {{id: $id}})
                RETURN collect(c.id) AS ids
                """,
                id=id_eliminar,
            ).single()["ids"]
            for account_id in account_ids:
                tx.run(
                    """
                    MATCH (c:Cuenta {id: $id})
                    SET c.activa = false,
                        c.inactivada = datetime().toString(),
                        c.auth_version = coalesce(c.auth_version, 0) + 1
                    """,
                    id=account_id,
                ).consume()

        eliminada = tx.run(
            f"MATCH (n:{etiqueta} {{id: $id}}) DETACH DELETE n RETURN count(n) AS total",
            id=id_eliminar,
        ).single()
        return "eliminado" if eliminada and eliminada["total"] else "no_encontrado"

    try:
        with conn.driver.session() as session:
            estado = session.execute_write(eliminar)
        if estado == "eliminado":
            invalidar_cache_datos()
            st.success(f"Registro {id_eliminar} eliminado y el acceso asociado desactivado.")
        elif estado == "tiene_ofertas":
            st.error("Primero elimina las ofertas publicadas por esta empresa.")
        else:
            st.warning("El registro ya no existe; la lista estaba desactualizada.")
    except Exception:
        st.error("No se pudo eliminar el registro.")

