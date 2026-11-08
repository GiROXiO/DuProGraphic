# DuProGraphic

Aplicación web de gestión y análisis de una red profesional. El backend es una API FastAPI conectada a Neo4j Aura, y el frontend es una aplicación React con Vite y Tailwind. Permite registrar usuarios, empresas, habilidades, proyectos y ofertas, además de explorar las relaciones entre esas entidades.

## Modelo de datos

### Nodos

- `Usuario`: nombre, perfil profesional y universidad.
- `Empresa`: nombre y sector.
- `Habilidad`: nombre y categoría.
- `Proyecto`: nombre y descripción.
- `Oferta`: título, estado, modalidad y nivel de experiencia.
- `Cuenta`: correo de acceso, rol y hash de contraseña. Nunca almacena la contraseña en texto plano.
- `Sesion`: token de sesión con vencimiento. Solo se guarda su hash.
- `Conversacion` y `Mensaje`: conversaciones privadas entre cuentas y mensajes con fecha y autor.

### Relaciones

- `CONECTA_CON`: conexiones profesionales entre usuarios.
- `SOLICITA_CONEXION`: invitación pendiente que la persona receptora puede aceptar o rechazar.
- `SOLICITA_DESCONEXION`: solicitud para cerrar una conexión, que requiere respuesta de la otra persona.
- `TRABAJA_EN`: vincula usuarios con empresas.
- `TIENE_HABILIDAD`: relaciona usuarios con habilidades.
- `PARTICIPA_EN`: vincula usuarios con proyectos.
- `PUBLICA`: relaciona empresas con ofertas.
- `PUBLICA_PROYECTO`: vincula una empresa con un proyecto que presenta en su perfil.
- `PERTENECE_A`: relaciona una oferta con el proyecto al que pertenece, cuando aplica.
- `REQUIERE`: conecta ofertas con habilidades requeridas.
- `POSTULA_A`: registra postulaciones de usuarios a ofertas.
- `TRABAJO_EN_OFERTA`: registra que una persona fue contratada para una oferta aceptada.
- `SOLICITA_EXPERIENCIA`: petición de una persona para que una empresa valide su experiencia laboral.
- `SOLICITA_PARTICIPACION`: petición de una persona para que la empresa propietaria valide su participación en un proyecto.
- `SIGUE_A`: usuarios que siguen empresas.
- `USA_TECNOLOGIA`: tecnologías asociadas a proyectos.
- `REPRESENTA_A`: vincula una cuenta con su perfil Usuario o Empresa.
- `INCLUYE`: vincula una conversación con cada cuenta participante.
- `CONTIENE`: vincula una conversación con sus mensajes.
- `ENVIADO_POR`: identifica la cuenta que escribió un mensaje.
- `SOBRE`: relaciona una conversación con un proyecto o una oferta, cuando aplica.

## Estructura

```text
DuProGraphic/
├── main.py
├── requirements.txt
├── backend_core/
│   ├── auth.py
│   ├── company_data.py
│   ├── connection.py
│   ├── messages.py
│   ├── portal_common.py
│   └── user_data.py
├── business_logic/
│   └── logic_ui.py
├── analytics_dashboard/
│   ├── analytics_ui.py
│   └── consultas_cypher/
├── db_scripts/
│   ├── init_db.py
│   ├── asociar_correos.py
│   └── importar_accesos.py
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api.js
        ├── App.jsx
        └── components/
```

`main.py` es la API FastAPI. `frontend/` es la interfaz React.

`business_logic/logic_ui.py` y `analytics_dashboard/analytics_ui.py` son código de la versión anterior con Streamlit. Todavía no están migrados a la API y requieren instalar `streamlit` aparte.

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

## Cuentas y roles

- **Usuario:** tiene un perfil profesional, conexiones, habilidades, proyectos, postulaciones y mensajes.
- **Empresa / reclutador:** administra su perfil público, proyectos, ofertas, postulaciones y mensajes.
- **Administrador:** administra registros, cuentas, roles y analítica. No empareja usuarios ni crea conexiones profesionales desde el portal.

Las cuentas se guardan como nodos Cuenta relacionados con Usuario o Empresa mediante REPRESENTA_A. La contraseña se guarda como hash con sal; no se almacena en texto plano. El correo normalizado es el usuario de acceso, por lo que al iniciar sesión se debe escribir el correo completo.

Un perfil existente de usuario o empresa se puede reclamar con un código de un solo uso generado por el administrador. Las cuentas creadas desde Gestión de datos se crean junto con el perfil en una transacción. Si se elimina un perfil, la cuenta vinculada queda desactivada y se conserva el historial de mensajes.

El prototipo no envía correos de verificación ni de recuperación. Los códigos de activación y las claves temporales se muestran una sola vez al administrador y deben entregarse por un canal privado.

Tras 5 intentos de acceso fallidos con el mismo correo, ese correo queda bloqueado durante 5 minutos.

### Accesos de demostración

La base de ejemplo contiene 16 perfiles de usuario y 5 empresas. Cuatro usuarios tienen también rol de administrador. Las direcciones que terminan en @duprographic.test son nombres de acceso ficticios; no reciben mensajes.

El Excel de accesos está separado en las hojas `Administradores`, `Usuarios` y `Empresas`. El importador necesita reunir esas filas en `db_scripts/accesos_demo.csv`; las cuentas administradoras se registran como perfiles de tipo `Usuario` con los roles `Usuario` y `Administrador`.

Para reconstruir esas cuentas en una base nueva:

1. Ejecuta python db_scripts/init_db.py para crear las restricciones y los perfiles.
2. Coloca el CSV consolidado en `db_scripts/accesos_demo.csv`. Debe incluir las columnas `Tipo de perfil`, `ID perfil`, `Nombre`, `Correo / usuario`, `Rol(es) habilitados` y `Contraseña`.
3. Ejecuta python db_scripts/importar_accesos.py.

El importador enlaza cada cuenta por ID de perfil y guarda en Neo4j los hashes de contraseña. El CSV local está excluido de Git. Repetir el comando conserva las contraseñas existentes; agrega --reemplazar-claves solo si quieres volver a aplicar las claves del CSV. No subas el Excel ni el CSV al repositorio.

## Inicialización de la base

Con el entorno virtual activo y el .env configurado, ejecuta:

    python db_scripts/init_db.py

El script crea las restricciones de unicidad que falten y carga los 16 usuarios de ejemplo, las empresas, las ofertas, las habilidades, los proyectos y sus relaciones. Usa MERGE y ON CREATE SET: al volverlo a ejecutar no borra nodos ni reemplaza propiedades existentes.

Para cargar las cuentas desde ese CSV, ejecuta:

    python db_scripts/importar_accesos.py

El importador comprueba que los perfiles y correos coincidan antes de escribir. Si se proporciona un CSV con contraseñas ya modificadas en la app, no las reemplaza automáticamente; usa --reemplazar-claves solo si quieres restaurar las claves del archivo.

db_scripts/asociar_correos.py es opcional para asociar los correos configurados en PERFIL_EMAIL_U1 a PERFIL_EMAIL_U4. Si la cuenta ya existe, el script actualiza en la misma transacción el correo del perfil y el de inicio de sesión. No ejecutes este paso con correos distintos de los que quieres usar como usuario.

## Ejecutar la aplicación

La aplicación necesita dos procesos al mismo tiempo, cada uno en su propia terminal.

**Terminal 1: backend (API).** Desde la carpeta del proyecto:

```cmd
.venv\Scripts\activate.bat
uvicorn main:app --reload --port 8000
```

La API queda en `http://127.0.0.1:8000`. Su documentación automática está en `http://127.0.0.1:8000/docs`.

**Terminal 2: frontend.** Desde la carpeta del proyecto:

```cmd
cd frontend
npm run dev
```

Vite muestra en la consola dos direcciones: `Local` (este equipo) y `Network` (otros equipos de la misma red). Abre cualquiera en el navegador e inicia sesión con una cuenta existente, eligiendo el tipo de acceso que corresponda (Usuario, Empresa o Admin).

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
- **"Credenciales inválidas":** revisa el correo completo, la contraseña y el tipo de acceso elegido.
- **La página se ve sin estilos:** ejecuta `npm install` dentro de `frontend` y reinicia `npm run dev`.

## Estado de la aplicación

### Disponible en la interfaz React

- **Acceso por rol:** inicio de sesión para usuarios, empresas y administradores. La API entrega un token que el frontend envía en cada petición. La sesión dura hasta 14 días, se valida al recargar la página y se revoca al pulsar "Salir".
- **Rutas protegidas:** las pantallas internas solo se muestran con una sesión válida.
- **Ofertas recomendadas:** listado de ofertas para el usuario según su perfil y su distancia en el grafo.

### Endpoints de la API

Todos requieren el token de sesión, salvo el inicio de sesión. Cada cuenta solo puede consultar sus propios datos; el administrador puede consultar los de cualquiera.

- `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`
- `GET /api/users/{id}/profile`
- `GET /api/users/{id}/feed/jobs`
- `GET /api/users/{id}/network/suggestions`
- `GET /api/companies/{id}/offers`

### Pendiente de migrar a React

- **Portal de usuario:** perfil editable con habilidades, experiencia empresarial y proyectos; directorios de profesionales y empresas; recomendaciones de contactos, empresas y proyectos.
- **Conexiones bilaterales:** una conexión se establece cuando la persona invitada la acepta. También se puede solicitar una desconexión que debe aceptar la otra persona.
- **Portal de empresa:** perfil público editable con equipo, proyectos y ofertas; perfiles de postulantes; candidaturas activas separadas de las aceptadas o rechazadas; aprobación de solicitudes de experiencia y de participación en proyectos.
- **Administración:** CRUD separado para usuarios, empresas, ofertas y proyectos; gestión de roles desde Cuentas y accesos.
- **Mensajería interna:** conversaciones entre usuarios y empresas, con tema general o asociadas a un proyecto o una oferta. Solo las cuentas que participan pueden leer o enviar mensajes.
- **Verificación de trayectoria:** las experiencias laborales nuevas y las participaciones en proyectos publicados por una empresa quedan pendientes hasta que esa organización las apruebe.
- **Analítica:** recomendaciones de contactos, empleos, colaboradores y candidatos; contactos en común; habilidades similares; usuarios con más conexiones; habilidades más demandadas; conexiones entre proyectos y rutas en el grafo. La vista de comunidades aplica Label Propagation sobre `CONECTA_CON`; no requiere Graph Data Science (GDS).
