# DuProGraphic

Aplicación web de gestión y análisis de una red profesional. Usa Streamlit y Neo4j Aura para registrar usuarios, empresas, habilidades, proyectos y ofertas, además de explorar las relaciones entre esas entidades.

## Modelo de datos

### Nodos

- `Usuario`: nombre, perfil profesional y universidad.
- `Empresa`: nombre y sector.
- `Habilidad`: nombre y categoría.
- `Proyecto`: nombre y descripción.
- `Oferta`: título, estado, modalidad y nivel de experiencia.

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

## Estructura

```text
DuProGraphic/
├── app.py
├── requirements.txt
├── backend_core/
│   ├── connection.py
│   └── crud_ui.py
├── business_logic/
│   └── logic_ui.py
├── analytics_dashboard/
│   ├── analytics_ui.py
│   └── consultas_cypher/
└── db_scripts/
    └── init_db.py
```

## Requisitos

- Python 3.8 o superior.
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
```

El archivo `.env` está excluido de Git. No subas credenciales al repositorio.

## Inicialización de la base

Con el entorno virtual activo y el `.env` configurado, ejecuta:

```cmd
python db_scripts\init_db.py
```

El script crea las restricciones de unicidad que falten y carga el conjunto de datos de ejemplo. Usa `MERGE` y `ON CREATE SET`: al volver a ejecutarlo no borra nodos ni reemplaza propiedades de nodos o relaciones que ya existan. En una base que ya tenga datos, solo completa los registros o vínculos faltantes del conjunto de ejemplo.

## Ejecutar la aplicación

```cmd
streamlit run app.py
```

Streamlit abrirá la aplicación en `http://localhost:8501`.

## Funciones de la aplicación

- **Gestión de entidades:** crear, consultar, actualizar y eliminar usuarios, empresas y ofertas.
- **Lógica de negocio:** crear conexiones profesionales, asignar habilidades, vincular usuarios con empresas y proyectos, asociar habilidades requeridas a ofertas, registrar postulaciones y buscar rutas entre usuarios y empresas.
- **Analítica:** recomendaciones de contactos, colaboradores y candidatos; contactos en común; habilidades similares; usuarios con más conexiones; habilidades más demandadas; conexiones entre proyectos y rutas en el grafo.

La vista de comunidades aplica Label Propagation sobre `CONECTA_CON`; no requiere Graph Data Science (GDS).
