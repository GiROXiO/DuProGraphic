# DuProGraphic

Aplicación web de gestión y análisis de una red profesional. El backend es una API FastAPI conectada a Neo4j Aura, y el frontend es una aplicación React con Vite y Tailwind. Permite registrar usuarios, empresas, habilidades, proyectos y ofertas, y explorar las relaciones entre esas entidades con consultas de grafos: rutas más cortas, contactos en común, habilidades similares, recomendaciones y comunidades.

## Qué permite hacer

**Persona (rol Usuario)**

- Crear su cuenta, completar su perfil personal y profesional, y editar su información.
- Registrar sus habilidades con nivel de dominio, las empresas donde ha trabajado (cargo, periodo y si es actual) y los proyectos en los que participa (con su rol).
- Conectarse con otras personas: enviar, aceptar, rechazar o cancelar solicitudes, y ver su red.
- Ver el perfil público de otras personas, con sus contactos en común.
- Recibir recomendaciones de ofertas, contactos y colaboradores, y consultar la ruta más corta hacia una empresa.
- Postularse a ofertas abiertas, seguir el estado de cada postulación y retirarla mientras no tenga una decisión.

**Empresa**

- Crear su cuenta y editar su perfil público.
- Publicar, editar, cerrar y reabrir ofertas, con las habilidades que requieren (obligatorias u opcionales).
- Ver quién se postuló a cada oferta, con las habilidades que coinciden y las que faltan, y cuántos de sus contactos ya trabajan en la empresa.
- Mover a cada postulante por el proceso de selección y ver los candidatos que el grafo recomienda para la oferta.

**Administrador**

- Crear, editar y eliminar usuarios, empresas, ofertas y proyectos desde el panel de administración.
- Dar o quitar el permiso de administrador a otros usuarios.
- Ver el panel de analítica global: usuarios más influyentes, comunidades detectadas, habilidades más demandadas, contactos en común, habilidades similares y proyectos relacionados.

## Modelo de datos

La base es schemaless: una propiedad existe en un nodo o relación desde que se escribe por primera vez. Las que se listan son las que usa la aplicación.

### Nodos

| Nodo        | Propiedades                                                                                                                                                                                                                                                             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Usuario`   | `id`, `nombre`, `perfil_profesional`, `universidad`, `correo_contacto`. Al editar su perfil también: `ubicacion`, `acerca_de`, `experiencia`, `areas_interes`, `educacion_detalle`, `anios_experiencia`, `modalidad_preferida`, `sitio_portafolio`, `idiomas`, `logros` |
| `Empresa`   | `id`, `nombre`, `sector`, `correo_contacto`, `descripcion`, `ubicacion`, `tamano`, `sitio_web`                                                                                                                                                                          |
| `Habilidad` | `id`, `nombre`, `categoria`                                                                                                                                                                                                                                             |
| `Proyecto`  | `id`, `nombre`, `descripcion`                                                                                                                                                                                                                                           |
| `Oferta`    | `id`, `titulo`, `descripcion`, `estado` (abierta o cerrada), `modalidad`, `nivel_experiencia`                                                                                                                                                                           |
| `Cuenta`    | Acceso a la aplicación: correo normalizado, `rol`, `roles`, `activa`, `auth_version`, hash y sal de la contraseña. Nunca guarda la contraseña en texto plano                                                                                                            |
| `Sesion`    | Token de sesión con vencimiento. Solo se guarda su hash                                                                                                                                                                                                                 |

### Relaciones

| Relación            | Significado                                                                                 | Propiedades                                                  |
| ------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `CONECTA_CON`       | Conexión profesional entre usuarios. Se guarda en las dos direcciones                       | `fuerza_conexion`                                            |
| `SOLICITA_CONEXION` | Invitación pendiente que la otra persona puede aceptar o rechazar                           | `estado`, `fecha`                                            |
| `TRABAJA_EN`        | Usuario vinculado a una empresa                                                             | `cargo`, `periodo`, `es_actual`                              |
| `TIENE_HABILIDAD`   | Usuario posee una habilidad                                                                 | `nivel_dominio`                                              |
| `PARTICIPA_EN`      | Usuario participa en un proyecto                                                            | `rol`                                                        |
| `PUBLICA`           | Empresa publica una oferta                                                                  | `fecha_publicacion`                                          |
| `REQUIERE`          | Oferta requiere una habilidad                                                               | `es_obligatoria`                                             |
| `POSTULA_A`         | Usuario se postula a una oferta                                                             | `estado_proceso`, `fecha_postulacion`, `fecha_actualizacion` |
| `USA_TECNOLOGIA`    | Tecnología (habilidad) que usa un proyecto                                                  |                                                              |
| `SIGUE_A`           | Usuario sigue a una empresa. Solo existe en los datos de ejemplo y alimenta las sugerencias |                                                              |
| `REPRESENTA_A`      | Cuenta vinculada a su perfil `Usuario` o `Empresa`                                          |                                                              |

Las restricciones de unicidad (ids, correos y token de sesión) las crea `db_scripts/init_db.py`.

## Estructura

```text
DuProGraphic/
├── main.py                       # API FastAPI (rutas y validaciones)
├── requirements.txt
├── backend_core/
│   ├── auth.py                   # cuentas, contraseñas, sesiones y registro
│   ├── user_data.py              # perfil, habilidades y recomendaciones del usuario
│   ├── links_data.py             # experiencia en empresas y proyectos del usuario
│   ├── network_data.py           # conexiones y perfil público
│   ├── applications_data.py      # postulaciones y proceso de selección
│   ├── company_data.py           # perfil de empresa y ofertas
│   ├── analytics_data.py         # consultas del panel de analítica
│   ├── admin_data.py             # operaciones del panel de administración
│   ├── connection.py             # conexión con Neo4j
│   ├── portal_common.py          # ejecución de consultas
│   └── messages.py               # mensajería interna (sin endpoints todavía)
├── analytics_dashboard/
│   ├── consultas_cypher/         # scripts Cypher de análisis
│   └── analytics_ui.py           # código heredado de Streamlit (no se usa)
├── business_logic/
│   └── logic_ui.py               # código heredado de Streamlit (no se usa)
├── db_scripts/
│   ├── init_db.py                # restricciones y datos de ejemplo
│   ├── importar_accesos.py       # crea cuentas de acceso desde un CSV
│   └── asociar_correos.py        # opcional: asocia correos a U1-U4
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api.js                # cliente HTTP con el token de sesión
        ├── useFetch.js
        ├── formErrors.js
        ├── App.jsx               # rutas
        └── components/
            ├── main_views/       # pantallas
            ├── nav_layout/       # menú y estructura de la página
            └── reusable/         # componentes reutilizables
```

`analytics_ui.py` y `logic_ui.py` son de la versión anterior con Streamlit. La aplicación actual no los usa y requerirían instalar `streamlit` aparte.

## Requisitos

- Python 3.11 o superior.
- Node.js 20.19 o superior (incluye npm).
- Acceso a una instancia de Neo4j Aura.

## Instalación en Windows CMD

### Backend

Desde la carpeta del proyecto:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

### Frontend

En otra terminal, desde la carpeta del proyecto:

```cmd
cd frontend
npm install
```

`npm install` crea la carpeta `frontend/node_modules` con las dependencias que lista `frontend/package.json`. Esa carpeta no se sube a Git.

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las credenciales de tu instancia Aura:

```env
NEO4J_URI=neo4j+ssc://<INSTANCE_ID>.databases.neo4j.io
NEO4J_USER=<USUARIO>
NEO4J_PASSWORD=<CONTRASEÑA>
```

El archivo `.env` está excluido de Git. No subas credenciales al repositorio.

## Inicializar la base de datos

Con el entorno virtual activo y el `.env` configurado, ejecuta desde la raíz del proyecto:

```cmd
python db_scripts/init_db.py
```

> **Atención:** este script **borra toda la base de datos** antes de cargar los datos de ejemplo. Elimina también las cuentas de acceso y las sesiones. Úsalo en una base nueva o cuando quieras empezar de cero.

El script:

1. Borra todos los nodos y relaciones existentes.
2. Crea las restricciones de unicidad: ids de cada entidad, correos de usuarios, empresas y cuentas, y el token de sesión.
3. Carga los datos de ejemplo: 25 usuarios, 10 empresas, 15 habilidades, 10 proyectos y 12 ofertas, con sus conexiones, habilidades, empresas, proyectos, requisitos de ofertas y postulaciones.

Los datos de ejemplo **no incluyen cuentas de acceso**. Hay dos formas de entrar a la aplicación después de inicializar:

- **Registrándote** desde la pantalla "Crear cuenta" como persona o empresa nueva. Esas cuentas empiezan con sus propios datos, sin relación con los de ejemplo.
- **Importando accesos** para los perfiles de ejemplo, que es la única forma de crear el primer administrador (ver el apartado siguiente).

### Importar cuentas de acceso

En una base recién inicializada no existe ningún administrador. Se crea importando un CSV con las cuentas que quieras, que **no se sube a Git** (`db_scripts/accesos_demo.csv` está excluido).

1. Crea `db_scripts/accesos_demo.csv` con estas columnas:

```csv
Tipo de perfil,ID perfil,Nombre,Correo / usuario,Rol(es) habilitados,Contraseña
Usuario,U1,Jerónimo Castro,admin@duprographic.test,"Usuario, Administrador",una-clave-de-10-o-mas
Usuario,U2,Juan Cáceres,juan@duprographic.test,Usuario,otra-clave-de-10-o-mas
Empresa,E1,Nubank,rrhh@duprographic.test,Empresa,clave-de-empresa-10
```

- `Tipo de perfil` es `Usuario` o `Empresa`.
- `ID perfil` debe ser un perfil que ya exista (por ejemplo `U1`, `E1`). Los de ejemplo van de `U1` a `U25` y de `E1` a `E10`.
- Un usuario con `Usuario, Administrador` puede entrar también como administrador. Las empresas solo usan `Empresa`.
- Las contraseñas deben tener entre 10 y 256 caracteres. Los correos y los ids no se pueden repetir.

2. Ejecuta:

```cmd
python db_scripts/importar_accesos.py
```

El importador comprueba que los perfiles y los correos coincidan antes de escribir, y guarda en Neo4j solo el hash de cada contraseña. Repetir el comando conserva las contraseñas que ya existen; agrega `--reemplazar-claves` solo si quieres volver a aplicar las del CSV.

`db_scripts/asociar_correos.py` es opcional: asocia los correos configurados en las variables `PERFIL_EMAIL_U1` a `PERFIL_EMAIL_U4` a los perfiles U1 a U4. No lo ejecutes con correos distintos de los que quieres usar como usuario.

## Cuentas y roles

- **Usuario:** perfil profesional, conexiones, habilidades, experiencia, proyectos y postulaciones.
- **Empresa:** perfil público, ofertas y candidatos.
- **Administrador:** gestión de usuarios, empresas, ofertas y proyectos, y analítica global.

**Crear una cuenta.** Cualquiera puede registrarse desde la pantalla de inicio de sesión (**Crear cuenta**) como persona o como empresa. El registro pide nombre, correo, contraseña de al menos 10 caracteres y un dato de perfil (titular profesional para una persona, sector para una empresa), e inicia la sesión de inmediato. El rol de administrador **no** se puede elegir al registrarse.

**Correos únicos.** Un correo solo puede estar en una cuenta. Intentar registrarse con uno que ya existe responde "Ese correo ya está registrado", sin dar pistas sobre qué tipo de cuenta lo usa. Aura lo refuerza con restricciones de unicidad.

**Permiso de administrador.** Un administrador puede darlo o quitarlo a otros usuarios desde la pestaña Usuarios del panel de administración. Quien lo recibe entra con la opción **Admin** del inicio de sesión, y con ese mismo correo también puede seguir entrando como Usuario. Un administrador no puede quitarse a sí mismo el permiso ni eliminar su propia cuenta.

**Eliminar.** Eliminar un usuario o una empresa borra su perfil con todas sus relaciones, borra su cuenta de acceso y cierra sus sesiones, así que su correo queda libre para volver a usarlo. Eliminar una empresa borra también sus ofertas y las postulaciones que recibieron.

**Seguridad.**

- Las contraseñas se guardan como hash con sal.
- La API entrega un token de sesión que Neo4j guarda solo como hash. Dura hasta 14 días, se valida al recargar y se revoca al pulsar "Salir".
- Tras 5 intentos de acceso fallidos con el mismo correo, ese correo queda bloqueado 5 minutos.
- El prototipo no envía correos de verificación ni de recuperación de contraseña.

## Ejecutar la aplicación

La aplicación necesita dos procesos al mismo tiempo, cada uno en su propia terminal.

**Terminal 1: backend (API).** Desde la carpeta del proyecto:

```cmd
.venv\Scripts\activate.bat
uvicorn main:app --reload --port 8000
```

La API queda en `http://127.0.0.1:8000`. Su documentación automática está en `http://127.0.0.1:8000/docs`. Casi todos los endpoints requieren el token de sesión (botón **Authorize**, con el token que devuelve el inicio de sesión).

**Terminal 2: frontend.** Desde la carpeta del proyecto:

```cmd
cd frontend
npm run dev
```

Vite muestra en la consola dos direcciones: `Local` (este equipo) y `Network` (otros equipos de la misma red). Abre cualquiera en el navegador. Inicia sesión con una cuenta existente, eligiendo el tipo de acceso que corresponda (Usuario, Empresa o Admin), o pulsa **Crear cuenta**.

Para generar la versión de producción del frontend: `npm run build` dentro de `frontend`.

### Cómo se conectan frontend y backend

El navegador solo habla con Vite. Las peticiones que empiezan por `/api` las reenvía Vite al backend (proxy), así que para el navegador todo es el mismo origen. Por eso la aplicación funciona con cualquier puerto o dirección con la que abras la página, incluida la IP de tu red local, y no hay errores de CORS.

El proxy apunta por defecto a `http://127.0.0.1:8000`. Si el backend corre en otra dirección, indícala antes de iniciar Vite:

```cmd
set API_TARGET=http://otra-direccion:8000
npm run dev
```

Si abres la aplicación desde otro equipo, Windows puede pedir permiso de firewall para Node.js la primera vez. Acepta solo en redes privadas.

### Comprobar que el proxy funciona

Con los dos servidores corriendo, abre una tercera terminal y ejecuta:

```cmd
curl -i http://127.0.0.1:5173/api/auth/me
```

Debe responder `401 Unauthorized` con `{"detail":"Falta el token de sesión"}`. Esa respuesta viene del backend e indica que Vite y la API están conectados.

### Solución de problemas

- **"No se pudo conectar con Neo4j":** revisa que el `.env` tenga `NEO4J_URI`, `NEO4J_USER` y `NEO4J_PASSWORD`, y que la instancia de Aura no esté pausada.
- **"No se pudo conectar con el servidor":** el backend no está corriendo en el puerto 8000, o Vite no se reinició después de cambiar `vite.config.js`.
- **"Credenciales inválidas":** revisa el correo completo, la contraseña y el tipo de acceso elegido. Si acabas de ejecutar `init_db.py`, las cuentas se borraron: regístrate de nuevo o importa los accesos.
- **"Ese correo ya está registrado":** ese correo ya tiene cuenta. Inicia sesión, o usa otro correo.
- **La página se ve sin estilos:** ejecuta `npm install` dentro de `frontend` y reinicia `npm run dev`.

## Proceso de selección

Cuando una persona se postula a una oferta abierta, la postulación empieza en **Recibida**. La empresa la mueve por estas etapas:

`Recibida` → `En revisión` → `Entrevista` → `Oferta enviada` → `Aceptada` o `Rechazada`

- Mientras la postulación está en Recibida, En revisión o Entrevista, la persona puede retirarla. Desde Oferta enviada ya no.
- **Aceptada** y **Rechazada** son definitivas: no se pueden cambiar después.
- La empresa ve en cada oferta la lista de personas aceptadas como contratadas.

## Consultas Cypher

Las consultas de análisis están como scripts en `analytics_dashboard/consultas_cypher/`. La API las carga desde ahí, salvo la que se indica.

| Script                                       | Pregunta que responde                                                                                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `usuarios_mas_influyentes.cypher`            | ¿Qué usuarios tienen más contactos directos?                                                                                                                       |
| `comunidades_detectadas.cypher`              | ¿Qué comunidades hay en la red? (datos de entrada del algoritmo Label Propagation, que se ejecuta en Python; no requiere Graph Data Science)                       |
| `habilidades_mas_demandadas.cypher`          | ¿Qué habilidades piden más las ofertas?                                                                                                                            |
| `habilidades_similares.cypher`               | ¿Qué usuarios tienen habilidades similares?                                                                                                                        |
| `contactos_en_comun.cypher`                  | ¿Qué contactos en común tienen dos profesionales?                                                                                                                  |
| `ruta_mas_corta_usuario_empresa.cypher`      | ¿Cuál es la ruta más corta entre un usuario y una empresa?                                                                                                         |
| `candidatos_recomendados_para_oferta.cypher` | ¿Qué candidatos recomendar para una oferta según sus habilidades y conexiones?                                                                                     |
| `proyectos_miembros_compartidos.cypher`      | ¿Qué proyectos comparten miembros?                                                                                                                                 |
| `proyectos_tecnologias_compartidas.cypher`   | ¿Qué proyectos comparten tecnologías?                                                                                                                              |
| `recomendaciones_contactos.cypher`           | ¿A quién conviene conectar a una persona?                                                                                                                          |
| `recomendaciones_colaboradores.cypher`       | ¿Con quién podría colaborar según las tecnologías en común?                                                                                                        |
| `recomendaciones_empleos.cypher`             | Versión de referencia de las ofertas recomendadas. Solo la usa el código heredado de Streamlit: la API las calcula con una variante en `backend_core/user_data.py` |

Las consultas de altas, bajas, edición y relaciones están escritas dentro de los módulos de `backend_core/`.

## Endpoints de la API

Todos requieren el token de sesión (`Authorization: Bearer <token>`), salvo el inicio de sesión y el registro. Cada cuenta solo puede consultar y modificar sus propios datos; el administrador puede gestionar los de cualquiera.

**Autenticación**

- `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`, `POST /api/auth/logout`

**Usuario**

- `GET` y `PUT /api/users/{id}/profile`
- `GET /api/skills` y `GET`, `PUT`, `DELETE /api/users/{id}/skills/{habilidad}`
- `GET /api/users/{id}/experience` y `PUT`, `DELETE /api/users/{id}/experience/{empresa}`
- `GET /api/projects` y `GET /api/users/{id}/projects`, `PUT`, `DELETE /api/users/{id}/projects/{proyecto}`
- `GET /api/users/{id}/feed/jobs`, `GET /api/users/{id}/network/suggestions`, `GET /api/users/{id}/recommendations`
- `GET /api/users/{id}/path-to/{empresa}`

**Red y personas**

- `GET /api/users/{id}/connections`
- `POST /api/users/{id}/connections/{otra}` (enviar solicitud; si la otra persona ya había enviado una, se acepta)
- `POST /api/users/{id}/connection-requests/{otra}/accept` y `DELETE /api/users/{id}/connection-requests/{otra}`
- `GET /api/people/{id}` (perfil público)

**Postulaciones**

- `GET /api/users/{id}/applications`, `POST`, `DELETE /api/users/{id}/applications/{oferta}`

**Empresa**

- `GET`, `PUT /api/companies/{id}/profile`
- `GET`, `POST /api/companies/{id}/offers` y `PUT /api/companies/{id}/offers/{oferta}`
- `PUT /api/companies/{id}/offers/{oferta}/status` (abrir o cerrar)
- `GET /api/companies/{id}/offers/{oferta}/applications` (postulantes con su afinidad)
- `PUT /api/companies/{id}/offers/{oferta}/applications/{usuario}` (cambiar la etapa)
- `GET /api/offers/{oferta}/candidates` (candidatos recomendados por el grafo)

**Analítica (solo administrador)**

- `GET /api/analytics/summary`, `influential-users`, `communities`, `demanded-skills`, `common-contacts`, `similar-skills`, `project-overlaps`
- `GET /api/lookups/users`, `/api/lookups/offers` y `GET /api/lookups/companies` (esta última la puede leer cualquier cuenta)

**Administración (solo administrador)**

- Usuarios: `GET`, `POST /api/admin/users`, `DELETE /api/admin/users/{id}` y `PUT /api/admin/users/{id}/admin`
- Empresas: `GET`, `POST /api/admin/companies` y `DELETE /api/admin/companies/{id}`
- Ofertas: `GET /api/admin/offers` y `DELETE /api/admin/offers/{id}`
- Proyectos: `GET`, `POST /api/admin/projects` y `PUT`, `DELETE /api/admin/projects/{id}`
- Para editar perfiles, empresas y ofertas existentes, el administrador usa los mismos endpoints que sus dueños.

## Limitaciones conocidas

- **Aceptar a una persona no crea `TRABAJA_EN`.** La empresa la ve como contratada, pero el grafo no la vincula a la empresa. Las rutas y los contactos en la empresa no cambian.
- **Cerrar una oferta no afecta a los postulantes pendientes.** Siguen en su etapa y la empresa puede seguir gestionándolos. Tampoco hay número de vacantes: se puede aceptar a varias personas en una misma oferta.
- **Las habilidades más demandadas cuentan también las ofertas cerradas.**
- **Un usuario no puede eliminar su propia cuenta.** Solo un administrador elimina perfiles.
- **Sin pruebas automáticas.** Las consultas se verificaron contra Aura con pruebas manuales.
- **Registro abierto sin límite de intentos.** El inicio de sesión sí limita los intentos fallidos, pero el registro no, así que cualquiera puede crear cuentas.

## Pendiente

- **Mensajería interna:** el módulo `backend_core/messages.py` existe, pero no tiene endpoints ni pantalla.
- **Directorios** de profesionales y empresas, y seguir empresas desde la interfaz.
- **Validación de trayectoria por la empresa:** hoy la experiencia y la participación en proyectos las declara la persona sin aprobación.
- **Desconexión entre usuarios** y proyectos propiedad de una empresa.
- **Códigos de activación y recuperación de contraseña:** hay funciones en `auth.py`, sin endpoints ni pantalla.
