import streamlit as st

from backend_core.auth import generar_codigo_activacion_admin, restablecer_password_admin
from backend_core.connection import get_db_connection


NOMBRES_ROL = {
    "usuario": "Usuario",
    "empresa": "Empresa / reclutador",
    "administrador": "Administrador",
}


def _editor_roles(conexion, cuentas):
    if not cuentas:
        return
    st.markdown("#### Roles y tipo de acceso")
    st.caption("Una cuenta puede tener su rol de perfil y el rol de administrador. Los cambios cierran las sesiones activas de esa cuenta.")
    opciones_cuenta = {c["correo"]: f"{c['nombre']} · {c['correo']}" for c in cuentas}
    correo = st.selectbox("Cuenta que vas a administrar", list(opciones_cuenta), format_func=lambda x: opciones_cuenta[x], key="cuenta_editar_roles")
    cuenta = next(c for c in cuentas if c["correo"] == correo)
    if cuenta["tipo"] == "Usuario":
        roles_permitidos = ["usuario", "administrador"]
        rol_perfil = "usuario"
    elif cuenta["tipo"] == "Empresa":
        roles_permitidos = ["empresa", "administrador"]
        rol_perfil = "empresa"
    else:
        roles_permitidos = ["administrador"]
        rol_perfil = "administrador"
    actuales = [r for r in cuenta["roles"] if r in roles_permitidos]
    if rol_perfil not in actuales:
        actuales.insert(0, rol_perfil)
    if not cuenta["activa"]:
        st.info("Esta cuenta está desactivada. Primero reactívala desde el flujo de acceso o crea una nueva cuenta para el perfil.")
    clave_widget = f"roles_de_{cuenta['correo']}"
    roles = st.multiselect(
        "Roles disponibles para esta cuenta",
        roles_permitidos,
        default=actuales,
        format_func=lambda r: NOMBRES_ROL[r],
        key=clave_widget,
        disabled=not cuenta["activa"],
    )
    if rol_perfil not in roles:
        st.warning(f"Mantén el rol {NOMBRES_ROL[rol_perfil]} para que la cuenta conserve acceso a su perfil.")
    if not cuenta["activa"]:
        return
    principal = st.selectbox(
        "Rol que se abre al iniciar sesión",
        roles_permitidos,
        index=roles_permitidos.index(cuenta["rol"]) if cuenta["rol"] in roles_permitidos else 0,
        key=f"rol_principal_{cuenta['correo']}",
    )
    if st.button("Guardar roles", key=f"guardar_roles_{cuenta['correo']}", disabled=not roles or rol_perfil not in roles):
        if principal not in roles:
            st.warning("El rol principal debe estar incluido entre los roles activos.")
            return
        roles_nuevos = list(dict.fromkeys(roles))
        try:
            with conexion.driver.session() as session:
                def actualizar(tx):
                    actual = tx.run(
                        """
                        MATCH (c:Cuenta {email_normalizado: $correo})
                        RETURN c.id AS id, c.rol AS rol,
                               coalesce(c.roles, [c.rol]) AS roles,
                               coalesce(c.activa, true) AS activa
                        """,
                        correo=correo,
                    ).single()
                    if not actual or not actual["activa"]:
                        return "no_disponible"
                    roles_actuales = set(actual["roles"] or [])
                    if actual["rol"]:
                        roles_actuales.add(actual["rol"])
                    if "administrador" in roles_actuales and "administrador" not in roles_nuevos:
                        admins = tx.run(
                            """
                            MATCH (admin:Cuenta)
                            WHERE coalesce(admin.activa, true) = true
                              AND ('administrador' IN coalesce(admin.roles, [admin.rol])
                                   OR admin.rol = 'administrador')
                            RETURN count(admin) AS total
                            """
                        ).single()["total"]
                        if admins <= 1:
                            return "ultimo_admin"
                    actualizado = tx.run(
                        """
                        MATCH (c:Cuenta {id: $id})
                        WHERE coalesce(c.activa, true) = true
                        SET c.roles = $roles, c.rol = $principal,
                            c.auth_version = coalesce(c.auth_version, 0) + 1
                        RETURN c.id AS id
                        """,
                        id=actual["id"], roles=roles_nuevos, principal=principal,
                    ).single()
                    return "guardado" if actualizado else "no_disponible"

                estado = session.execute_write(actualizar)
            if estado == "guardado":
                st.success("Los roles se actualizaron. La cuenta tendrá que iniciar sesión otra vez.")
                st.rerun()
            elif estado == "ultimo_admin":
                st.error("No se puede quitar el rol al último administrador activo.")
            else:
                st.warning("La cuenta ya no está disponible.")
        except Exception:
            st.error("No se pudieron actualizar los roles de la cuenta.")


def renderizar():
    st.info(
        "El correo es el usuario de acceso. Neo4j guarda las contraseñas como hashes. "
        "Al desactivar un perfil se bloquea su cuenta y se conserva el historial de mensajes."
    )
    st.caption(
        "Los perfiles sin cuenta aparecerán como pendientes. El administrador puede generar "
        "un código de un solo uso para que su titular reclame el perfil."
    )
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        st.error("No se pudo conectar con Neo4j Aura.")
        return

    try:
        with conexion.driver.session() as session:
            cuentas = session.run(
                """
                MATCH (c:Cuenta)
                OPTIONAL MATCH (c)-[:REPRESENTA_A]->(perfil)
                RETURN c.email_normalizado AS correo,
                       c.rol AS rol,
                       coalesce(c.roles, [c.rol]) AS roles,
                       coalesce(perfil.nombre, c.email_normalizado) AS nombre,
                       perfil.id AS perfil_id,
                       CASE WHEN perfil:Empresa THEN 'Empresa'
                            WHEN perfil:Usuario THEN 'Usuario'
                            ELSE 'Sin perfil' END AS tipo,
                       coalesce(c.activa, true) AS activa,
                       c.fecha_creacion AS fecha_creacion
                ORDER BY activa DESC, rol, correo
                """
            ).data()
    except Exception:
        st.error("No se pudo consultar el listado de cuentas.")
        return

    if not cuentas:
        st.info("Todavía no hay cuentas registradas.")
    else:
        filas = [
            {
                "Correo / usuario": cuenta["correo"],
                "Nombre": cuenta["nombre"],
                "Perfil": cuenta["tipo"],
                "Roles": ", ".join(
                    NOMBRES_ROL.get(rol, rol) for rol in cuenta["roles"]
                ),
                "ID del perfil": cuenta["perfil_id"] or "-",
                "Estado": "Activa" if cuenta["activa"] else "Desactivada",
                "Creada": cuenta["fecha_creacion"] or "-",
            }
            for cuenta in cuentas
        ]
        st.dataframe(filas, width="stretch", hide_index=True)

    with st.expander("Cambiar roles de una cuenta", expanded=False):
        _editor_roles(conexion, cuentas)

    try:
        with conexion.driver.session() as session:
            perfiles = session.run(
                """
                MATCH (perfil)
                WHERE (perfil:Usuario OR perfil:Empresa)
                  AND perfil.correo_contacto IS NOT NULL
                OPTIONAL MATCH (c:Cuenta)-[:REPRESENTA_A]->(perfil)
                RETURN perfil.correo_contacto AS correo,
                       perfil.nombre AS nombre,
                       perfil.id AS perfil_id,
                       CASE WHEN perfil:Empresa THEN 'Empresa' ELSE 'Usuario' END AS tipo,
                       CASE WHEN c IS NULL THEN 'Pendiente de acceso'
                            WHEN NOT coalesce(c.activa, true) THEN 'Cuenta desactivada'
                            ELSE 'Cuenta activa' END AS acceso
                ORDER BY tipo, nombre
                """
            ).data()
    except Exception:
        st.error("No se pudieron consultar los perfiles asociados a correo.")
        perfiles = []

    if perfiles:
        st.markdown("#### Perfiles con correo")
        st.dataframe(
            [
                {
                    "Correo": p["correo"],
                    "Nombre": p["nombre"],
                    "Tipo": p["tipo"],
                    "ID del perfil": p["perfil_id"],
                    "Acceso": p["acceso"],
                }
                for p in perfiles
            ],
            width="stretch",
            hide_index=True,
        )
        pendientes = [p for p in perfiles if p["acceso"] == "Pendiente de acceso"]
        if pendientes:
            st.markdown("#### Dar acceso a un perfil existente")
            st.caption(
                "El código vence en 7 días y solo se muestra una vez. "
                "Entrégalo al titular por un canal privado."
            )
            opciones = {
                p["perfil_id"]: f"{p['nombre']} · {p['tipo']} ({p['correo']})"
                for p in pendientes
            }
            with st.form("form_codigo_activacion"):
                perfil_id = st.selectbox(
                    "Perfil",
                    list(opciones),
                    format_func=lambda x: opciones[x],
                )
                generar = st.form_submit_button(
                    "Generar código de activación", width="stretch"
                )
            if generar:
                seleccionado = next(p for p in pendientes if p["perfil_id"] == perfil_id)
                acceso = generar_codigo_activacion_admin(
                    seleccionado["correo"], seleccionado["tipo"]
                )
                if acceso:
                    st.success(f"Código generado para el perfil {acceso[0]}.")
                    st.code(acceso[1], language=None)
                    st.warning("Cópialo ahora. No volverá a mostrarse.")
                else:
                    st.error("No se pudo generar un código para ese perfil.")

    activas = [c["correo"] for c in cuentas if c["activa"]] if cuentas else []
    st.markdown("#### Restablecer acceso")
    st.caption(
        "Se reemplaza la contraseña anterior y se cierran las sesiones abiertas de esa cuenta. "
        "Comparte la clave temporal por un canal privado."
    )
    if not activas:
        st.info("No hay cuentas activas para restablecer.")
        return
    with st.form("form_resetear_clave"):
        correo = st.selectbox("Cuenta", activas)
        resetear = st.form_submit_button("Generar clave temporal", width="stretch")

    if resetear:
        nueva_clave = restablecer_password_admin(correo)
        if nueva_clave:
            st.success(f"Se generó una clave nueva para {nueva_clave[0]}.")
            st.code(nueva_clave[1], language=None)
            st.warning("Cópiala ahora. No volverá a mostrarse después de salir de esta pantalla.")
        else:
            st.error("No se pudo restablecer la clave de esa cuenta.")
