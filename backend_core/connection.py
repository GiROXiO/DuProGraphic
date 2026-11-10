import os
import logging
from pathlib import Path
from threading import RLock
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self._lock = RLock()

    def connect(self):
        with self._lock:
            if self.driver is not None:
                return self.driver
            if not self.uri or not self.user or not self.password:
                logger.error("Faltan variables de conexión de Neo4j en .env.")
                return None
            try:
                driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                driver.verify_connectivity()
                self.driver = driver
            except Exception:
                logger.exception("No se pudo establecer la conexión con Neo4j Aura.")
            return self.driver

    def close(self):
        with self._lock:
            if self.driver is not None:
                self.driver.close()
                self.driver = None

_db_instance = None
_db_lock = RLock()

def get_db_connection():
    global _db_instance
    with _db_lock:
        if _db_instance is None:
            _db_instance = Neo4jConnection()
        _db_instance.connect()
        return _db_instance