import os
import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None

    def connect(self):
        if not self.driver:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except Exception as e:
                st.error(f"Error al conectar con Neo4j: {e}")
        return self.driver

    def close(self):
        if self.driver:
            self.driver.close()

@st.cache_resource
def get_db_connection():
    conn = Neo4jConnection()
    conn.connect()
    return conn