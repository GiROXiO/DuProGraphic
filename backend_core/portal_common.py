import logging
from backend_core.connection import get_db_connection

logger = logging.getLogger(__name__)

def consultar(consulta, **parametros):
    conexion = get_db_connection()
    if conexion is None or conexion.driver is None:
        raise ConnectionError("No se pudo conectar con Neo4j Aura.")
    try:
        with conexion.driver.session() as session:
            return session.run(consulta, **parametros).data()
    except Exception as error:
        codigo = getattr(error, "code", None)
        logger.error("Error al consultar Neo4j: tipo=%s código=%s", type(error).__name__, codigo)
        raise

def escribir(consulta, **parametros):
    return consultar(consulta, **parametros)