# Duprographic - Plataforma de Red Profesional Basada en Grafos

## Descripción del Proyecto

Duprographic es una plataforma analítica y transaccional desarrollada para gestionar y analizar una red profesional interconectada. A diferencia de los sistemas relacionales tradicionales, este proyecto utiliza **Neo4j** (Base de Datos Orientada a Grafos) para modelar relaciones complejas entre Usuarios, Empresas, Proyectos, Ofertas y Habilidades, permitiendo consultas profundas como detección de comunidades, rutas más cortas y motores de recomendación.

## Equipo de Desarrollo

- **Jerónimo Castro**: Arquitecto de Base de Datos e Integrador (Líder del repositorio).
- **Juan Cáceres**: Desarrollador Backend Core (Modelos ORM y operaciones CRUD).
- **Juan Arrieta**: Especialista en Lógica de Negocio (Flujos de validación, préstamos y multas).
- **Miguel Carrizosa**: Analista de Datos (Consultas SQL, métricas y reportes).

## Estructura del Repositorio

El proyecto está modularizado para evitar conflictos de integración y separar las responsabilidades del equipo:

```text
DuProGraphic/
├── .env                        # Credenciales de conexión a Neo4j Aura (No versionado)
├── .gitignore                  # Archivos ignorados por Git
├── app.py                      # Enrutador principal de la interfaz (Streamlit)
├── requirements.txt            # Dependencias del proyecto
│
├── db_scripts/
│   └── init_db.py              # Script de inicialización y carga masiva de datos
│
├── backend_core/               # Módulo asignado a Juan Cáceres
│   ├── __init__.py
│   ├── connection.py           # Gestor centralizado de la conexión a Neo4j (Singleton)
│   └── crud_ui.py              # Interfaz y controladores para operaciones transaccionales
│
├── business_logic/             # Módulo asignado a Juan Arrieta
│   ├── __init__.py
│   └── logic_ui.py             # Interfaz y controladores para flujos de red y rutas
│
└── analytics_dashboard/        # Módulo asignado a Miguel Carrizosa
    ├── __init__.py
    └── analytics_ui.py         # Interfaz y visualizadores para métricas avanzadas
```

## Requisitos Previos

- Python 3.8 o superior.
- Cuenta activa en [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/).
- Git instalado en el sistema local.

## Instalación y Configuración

**1. Clonar el repositorio:**

```bash
git clone <URL_DEL_REPOSITORIO>
cd DuProGraphic
```

**2. Crear y activar el entorno virtual:**

- En Windows:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
- En macOS/Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

**3. Instalar las dependencias:**

```bash
pip install streamlit neo4j python-dotenv
```

_(Nota: Si se agregan librerías posteriores, actualizar con `pip freeze > requirements.txt`)_

**4. Configurar las variables de entorno:**
Crear un archivo `.env` en la raíz del proyecto con las credenciales entregadas por Neo4j Aura. El protocolo debe ser `neo4j+ssc://` para evitar conflictos de certificados SSL en entornos de desarrollo local:

```env
NEO4J_URI=neo4j+ssc://<TU_INSTANCE_ID>.databases.neo4j.io
NEO4J_USER=<TU_USUARIO>
NEO4J_PASSWORD=<TU_CONTRASEÑA>
```

## Inicialización de la Base de Datos

Antes de ejecutar la aplicación por primera vez, es necesario estructurar la base de datos y cargar el volumen de datos masivos.

Ejecutar en la terminal (asegurando que el entorno virtual esté activo):

```bash
python db_scripts/init_db.py
```

Este script creará las restricciones de unicidad e inyectará la red inicial.

## Ejecución de la Aplicación

Para levantar el servidor local de desarrollo y visualizar la interfaz gráfica:

```bash
streamlit run app.py
```

La aplicación estará disponible en el navegador web en `http://localhost:8501`.
