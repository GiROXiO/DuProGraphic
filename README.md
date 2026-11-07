# DuProGraphic

Aplicación web de gestión y análisis de una red profesional. Usa Streamlit y Neo4j Aura para registrar usuarios, empresas, habilidades, proyectos y ofertas, además de explorar las relaciones entre esas entidades.

## Modelo de datos

### Nodos

- `Usuario`: nombre, perfil profesional y universidad.
- `Empresa`: nombre y sector.
- `Habilidad`: nombre y categoría.
- `Proyecto`: nombre y descripción.
- `Oferta`: título, estado, modalidad y nivel de experiencia.
- `Cuenta`: correo de acceso, rol y hash de contraseña. Nunca almacena la contraseña en texto plano.
- `Conversacion` y `Mensaje`: conversaciones privadas entre cuentas y mensajes con fecha y autor.

### Relaciones

- `CONECTA_CON`: conexiones profesionales entre usuarios.
- `TRABAJA_EN`: vincula usuarios con empresas.
- `TIENE_HABILIDAD`: relaciona usuarios con habilidades.
- `PARTICIPA_EN`: vincula usuarios con proyectos.
- `PUBLICA`: relaciona empresas con ofertas.
- `REQUIERE`: conecta ofertas con habilidades requeridas.
- `POSTULA_A`: registra postulaciones de usuarios a ofertas.
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
├── app.py
├── requirements.txt
├── backend_core/
│   ├── auth.py
│   ├── auth_ui.py
│   ├── accounts_ui.py
│   ├── connection.py
│   ├── crud_ui.py
│   ├── messages.py
│   ├── messages_ui.py
│   └── role_ui.py
├── business_logic/
│   └── logic_ui.py
├── analytics_dashboard/
│   ├── analytics_ui.py
│   └── consultas_cypher/
└── db_scripts/
    ├── init_db.py
    ├── asociar_correos.py
    └── importar_accesos.py
```

## Requisitos

- Python 3.11 o superior.
- Acceso a una instancia de Neo4j Aura.

## Instalación en Windows CMD

Desde la carpeta del proyecto:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz del proyecto con las credenciales de tu instancia Aura:

```env
NEO4J_URI=neo4j+ssc://<INSTANCE_ID>.databases.neo4j.io
NEO4J_USER=<USUARIO>
NEO4J_PASSWORD=<CONTRASEÑA>
ADMIN_EMAIL=<CORREO_DEL_ADMINISTRADOR>
ADMIN_PASSWORD=<CONTRASEÑA_LARGA_Y_UNICA>
PERFIL_EMAIL_U1=<CORREO_PROFESIONAL_U1>
PERFIL_EMAIL_U2=<CORREO_PROFESIONAL_U2>
PERFIL_EMAIL_U3=<CORREO_PROFESIONAL_U3>
PERFIL_EMAIL_U4=<CORREO_PROFESIONAL_U4>
```

El archivo `.env` está excluido de Git. No subas credenciales al repositorio. Usa una contraseña única de al menos 10 caracteres para el administrador.
El correo del administrador debe ser distinto de los correos ya asociados a perfiles de usuario; esos correos quedan reservados para que sus titulares reclamen el perfil.

Las variables `PERFIL_EMAIL_U1` a `PERFIL_EMAIL_U4` son opcionales y se usan por el script de asociación para enlazar correos con perfiles existentes. Los valores reales se mantienen en el `.env` local y no deben escribirse en el README ni en archivos versionados.

## Cuentas y roles

- **Usuario:** tiene un perfil profesional, conexiones, habilidades, proyectos, postulaciones y mensajes.
- **Empresa / reclutador:** administra su perfil, ofertas, postulaciones y mensajes.
- **Administrador:** gestiona los datos, las relaciones, los accesos y la analítica. No existe registro público para este rol.

Las cuentas se guardan como nodos Cuenta relacionados con Usuario o Empresa mediante REPRESENTA_A. La contraseña se guarda como hash con sal; no se almacena en texto plano. El correo normalizado es el usuario de acceso.

Un perfil existente de usuario o empresa se puede reclamar con un código de un solo uso generado por el administrador. Las cuentas creadas desde Gestión de datos se crean junto con el perfil en una transacción. Si se elimina un perfil, la cuenta vinculada queda desactivada y se conserva el historial de mensajes.

El prototipo no envía correos de verificación ni de recuperación. Los códigos de activación y las claves temporales se muestran una sola vez al administrador y deben entregarse por un canal privado.

### Accesos de demostración

La base de ejemplo contiene 16 perfiles de usuario y 5 empresas. Cuatro usuarios tienen también rol de administrador. Las direcciones que terminan en @duprographic.test son nombres de acceso ficticios; no reciben mensajes.

Para reconstruir esas cuentas en una base nueva:

1. Ejecuta python db_scripts/init_db.py para crear las restricciones y los perfiles.
2. Desde el Excel de accesos, guarda la hoja Accesos como CSV UTF-8 en db_scripts/accesos_demo.csv.
3. Ejecuta python db_scripts/importar_accesos.py.

El importador enlaza cada cuenta por ID de perfil y guarda en Neo4j los hashes de contraseña. El CSV local está excluido de Git. Repetir el comando conserva las contraseñas existentes; agrega --reemplazar-claves solo si quieres volver a aplicar las claves del CSV. No subas el Excel ni el CSV al repositorio.

## Inicialización de la base

Con el entorno virtual activo y el .env configurado, ejecuta:

    python db_scripts/init_db.py

El script crea las restricciones de unicidad que falten y carga los 16 usuarios de ejemplo, las empresas, las ofertas, las habilidades, los proyectos y sus relaciones. Usa MERGE y ON CREATE SET: al volverlo a ejecutar no borra nodos ni reemplaza propiedades existentes.

Para habilitar los accesos de la hoja, expórtala como db_scripts/accesos_demo.csv en formato CSV UTF-8 y ejecuta:

    python db_scripts/importar_accesos.py

El importador comprueba que los perfiles y correos coincidan antes de escribir. Si se proporciona un CSV con contraseñas ya modificadas en la app, no las reemplaza automáticamente; usa --reemplazar-claves solo si quieres restaurar las claves del archivo.

db_scripts/asociar_correos.py es opcional para asociar los correos configurados en PERFIL_EMAIL_U1 a PERFIL_EMAIL_U4. Si la cuenta ya existe, el script actualiza en la misma transacción el correo del perfil y el de inicio de sesión. No ejecutes este paso con correos distintos de los que quieres usar como usuario.

## Ejecutar la aplicación

```cmd
streamlit run app.py
```

Streamlit abrirá la aplicación en `http://localhost:8501`.

## Funciones de la aplicación

- **Gestión de entidades:** crear, consultar, actualizar y eliminar usuarios, empresas y ofertas. Los perfiles nuevos de usuario o empresa requieren un correo y una contraseña inicial.
- **Acceso por rol:** registro e inicio de sesión para usuarios, empresas y administradores; cada sesión valida que la cuenta siga activa y conserve el rol.
- **Mensajería interna:** conversaciones entre usuarios y empresas, con tema general o asociadas a un proyecto o una oferta. Solo las cuentas que participan pueden leer o enviar mensajes.
- **Lógica de negocio:** crear conexiones profesionales, asignar habilidades, vincular usuarios con empresas y proyectos, publicar ofertas desde empresas, asociar habilidades requeridas, registrar postulaciones a ofertas abiertas y publicadas, y buscar rutas entre usuarios y empresas.
- **Analítica:** recomendaciones de contactos, empleos, colaboradores y candidatos; contactos en común; habilidades similares; usuarios con más conexiones; habilidades más demandadas; conexiones entre proyectos y rutas en el grafo.

La vista de comunidades aplica Label Propagation sobre `CONECTA_CON`; no requiere Graph Data Science (GDS).
