# Proyecto I+D: Red Profesional con Base de Datos de Grafos

Este repositorio contiene la implementación de una aplicación orientada a la gestión y análisis de relaciones en una red profesional, utilizando una base de datos de grafos para superar las limitaciones del modelo relacional en consultas profundas.

## Equipo de Trabajo y Roles

Cada integrante trabajará en su área creando ramas a partir de `main` (ej. `feature/nombre-de-la-tarea`):

- **Jerónimo Castro (Arquitecto de BD e Integrador):** Diseño del modelo de grafos, scripts de inicio de la BD y líder del repositorio.
- **Juan Cáceres (Desarrollador Backend Core):** Operaciones CRUD para usuarios, empresas e información profesional.
- **Juan Arrieta (Especialista en Lógica de Negocio):** Flujos de validación, postulación a ofertas y vinculación de habilidades.
- **Miguel Carrizosa (Analista de Datos):** Consultas de grafos nativas, métricas del panel y algoritmos de recomendación.

## Configuración del Entorno de Desarrollo local

Sigan estos pasos para levantar el proyecto en sus máquinas locales:

1. **Clonar el repositorio:**
   git clone <URL_DEL_REPOSITORIO>
   cd DuProGraphic

2. **Crear y activar el entorno virtual:**
   python -m venv venv

   # En Windows (Git Bash):

   source venv/Scripts/activate

   # En Mac/Linux:

   source venv/bin/activate

3. **Instalar dependencias:**
   pip install -r requirements.txt

4. **Variables de Entorno (.env):**
   Solicitar a Jerónimo las credenciales de conexión de la base de datos Neo4j y crear un archivo `.env` en la raíz con la siguiente estructura:

   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=tu_contraseña

## Tecnologías

- **Base de Datos:** Neo4j
- **Lenguaje:** Python
- **Driver de conexión:** neo4j
