import os
from pathlib import Path
from threading import RLock

import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self._lock = RLock()

    def connect(self):
        """Crea y valida el driver; permite reintentar si Aura estuvo temporalmente caído."""
        with self._lock:
            if self.driver is not None:
                return self.driver

            if not self.uri or not self.user or not self.password:
                st.error("Configura NEO4J_URI, NEO4J_USER y NEO4J_PASSWORD en el archivo .env.")
                return None

            driver = None
            try:
                driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                driver.verify_connectivity()
                self.driver = driver
            except Exception:
                if driver is not None:
                    driver.close()
                st.error("No se pudo conectar con Neo4j Aura. Revisa la red y las credenciales del archivo .env.")
            return self.driver

    def close(self):
        with self._lock:
            if self.driver is not None:
                self.driver.close()
                self.driver = None


@st.cache_resource
def _connection_resource():
    return Neo4jConnection()


def get_db_connection():
    # Se intenta conectar en cada acceso si la creación anterior falló.
    conexion = _connection_resource()
    conexion.connect()
    return conexion


def invalidar_cache_datos():
    """Invalida resultados de lectura después de una escritura confirmada."""
    st.cache_data.clear()
