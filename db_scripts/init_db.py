from neo4j import GraphDatabase
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

def crear_restricciones(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:Usuario) REQUIRE u.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Empresa) REQUIRE e.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Proyecto) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Oferta) REQUIRE o.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT cuenta_email_unico IF NOT EXISTS FOR (c:Cuenta) REQUIRE c.email_normalizado IS UNIQUE")
    tx.run("CREATE CONSTRAINT usuario_correo_unico IF NOT EXISTS FOR (u:Usuario) REQUIRE u.correo_contacto IS UNIQUE")
    tx.run("CREATE CONSTRAINT empresa_correo_unico IF NOT EXISTS FOR (e:Empresa) REQUIRE e.correo_contacto IS UNIQUE")
    tx.run("CREATE CONSTRAINT conversacion_clave_unica IF NOT EXISTS FOR (c:Conversacion) REQUIRE c.clave IS UNIQUE")
    tx.run("CREATE CONSTRAINT mensaje_id_unico IF NOT EXISTS FOR (m:Mensaje) REQUIRE m.id IS UNIQUE")

def poblar_datos(tx):
    # ON CREATE conserva los nodos y relaciones que ya existen en Aura.
    # 1. NODOS: Usuarios 
    usuarios = [
        {"id": "U1", "nombre": "Jerónimo Castro", "perfil": "Arquitecto BD", "univ": "Universidad del Norte"},
        {"id": "U2", "nombre": "Juan Cáceres", "perfil": "Backend Developer", "univ": "Universidad del Norte"},
        {"id": "U3", "nombre": "Juan Arrieta", "perfil": "Business Logic Eng", "univ": "Universidad del Norte"},
        {"id": "U4", "nombre": "Miguel Carrizosa", "perfil": "Data Analyst", "univ": "Universidad del Norte"},
        {"id": "U5", "nombre": "Andrés Felipe Rojas", "perfil": "DevOps Engineer", "univ": "Universidad Nacional"},
        {"id": "U6", "nombre": "Laura Gómez", "perfil": "Frontend React", "univ": "Universidad de los Andes"},
        {"id": "U7", "nombre": "Carlos Mendoza", "perfil": "Cloud Architect", "univ": "Universidad del Norte"},
        {"id": "U8", "nombre": "Sofía Vergara", "perfil": "Data Scientist", "univ": "UIS"},
        {"id": "U9", "nombre": "David Pérez", "perfil": "Ingeniero de Hardware", "univ": "Universidad del Norte"},
        {"id": "U10", "nombre": "Camila Ortiz", "perfil": "Scrum Master", "univ": "Sena"},
        {"id": "U11", "nombre": "Luis Martínez", "perfil": "Backend Django", "univ": "Universidad del Norte"},
        {"id": "U12", "nombre": "Ana Rodríguez", "perfil": "QA Tester", "univ": "Universidad de Antioquia"},
        {"id": "U13", "nombre": "Jorge Silva", "perfil": "Database Admin", "univ": "Universidad del Valle"},
        {"id": "U14", "nombre": "Valentina Ríos", "perfil": "UX/UI Designer", "univ": "Universidad de los Andes"},
        {"id": "U15", "nombre": "Mateo Blanco", "perfil": "Fullstack Developer", "univ": "Sena"},
        # Perfil de prueba conservado en la instancia original de Aura.
        {"id": "U322", "nombre": "Juan", "perfil": "Profesor de Parafrasis", "univ": "UniSimon"}
    ]
    tx.run("""
        UNWIND $usuarios AS u
        MERGE (n:Usuario {id: u.id})
        ON CREATE SET n.nombre = u.nombre, n.perfil_profesional = u.perfil, n.universidad = u.univ
    """, usuarios=usuarios)

    # 2. NODOS: Empresas, Proyectos, Habilidades y Ofertas
    empresas = [
        {"id": "E1", "nombre": "Sibilab Tech", "sector": "Desarrollo de Software"},
        {"id": "E2", "nombre": "Globant", "sector": "Consultoría IT"},
        {"id": "E3", "nombre": "Mercado Libre", "sector": "E-commerce"},
        {"id": "E4", "nombre": "Promigas", "sector": "Energía y Tecnología"},
        {"id": "E5", "nombre": "Rappi", "sector": "Tecnología Logística"}
    ]
    tx.run("UNWIND $empresas AS e MERGE (n:Empresa {id: e.id}) ON CREATE SET n.nombre = e.nombre, n.sector = e.sector", empresas=empresas)

    proyectos = [
        {"id": "P1", "nombre": "Duprographic", "desc": "Red Profesional con BD Grafos"},
        {"id": "P2", "nombre": "Sibilab", "desc": "Sistema de gestión de biblioteca con Django y PostgreSQL"},
        {"id": "P3", "nombre": "Arrieta_Carrizosa_Castro FPGA", "desc": "Arquitectura VHDL para juego Pong y PS/2"},
        {"id": "P4", "nombre": "Infraestructura Cisco", "desc": "Ruteo estático en Cisco 1841 con subredes"}
    ]
    tx.run("UNWIND $proyectos AS p MERGE (n:Proyecto {id: p.id}) ON CREATE SET n.nombre = p.nombre, n.descripcion = p.desc", proyectos=proyectos)

    habilidades = [
        {"id": "H1", "nombre": "Python", "cat": "técnica"}, {"id": "H2", "nombre": "Neo4j", "cat": "técnica"},
        {"id": "H3", "nombre": "PostgreSQL", "cat": "técnica"}, {"id": "H4", "nombre": "Django", "cat": "técnica"},
        {"id": "H5", "nombre": "VHDL", "cat": "técnica"}, {"id": "H6", "nombre": "Cisco Routing", "cat": "técnica"},
        {"id": "H7", "nombre": "Liderazgo", "cat": "blanda"}, {"id": "H8", "nombre": "C#", "cat": "técnica"},
        {"id": "H9", "nombre": "React", "cat": "técnica"}, {"id": "H10", "nombre": "AWS", "cat": "técnica"}
    ]
    tx.run("UNWIND $habs AS h MERGE (n:Habilidad {id: h.id}) ON CREATE SET n.nombre = h.nombre, n.categoria = h.cat", habs=habilidades)

    ofertas = [
        {"id": "O1", "titulo": "Arquitecto de Datos Grafos", "estado": "abierta", "mod": "remoto", "exp": "Senior"},
        {"id": "O2", "titulo": "Desarrollador Backend Django", "estado": "abierta", "mod": "híbrido", "exp": "Junior"},
        {"id": "O3", "titulo": "Ingeniero FPGA", "estado": "abierta", "mod": "presencial", "exp": "Semi-Senior"},
        {"id": "O4", "titulo": "Especialista en Redes Cisco", "estado": "abierta", "mod": "híbrido", "exp": "Senior"},
        {"id": "O5", "titulo": "Data Analyst", "estado": "abierta", "mod": "remoto", "exp": "Junior"}
    ]
    tx.run("UNWIND $ofertas AS o MERGE (n:Oferta {id: o.id}) ON CREATE SET n.titulo = o.titulo, n.estado = o.estado, n.modalidad = o.mod, n.nivel_experiencia = o.exp", ofertas=ofertas)

    # 3. RELACIONES DINÁMICAS (El Grafo)
    # Red de contactos densa (Simulando universidad y ecosistema Barranquilla/Colombia)
    conexiones = [
        ("U1","U2","alta"), ("U1","U3","alta"), ("U1","U4","alta"), ("U2","U3","alta"), ("U3","U4","alta"),
        ("U1","U7","media"), ("U1","U9","media"), ("U2","U11","baja"), ("U4","U8","alta"),
        ("U5","U7","alta"), ("U5","U14","media"), ("U6","U15","alta"), ("U8","U12","media"),
        ("U7","U10","alta"), ("U9","U13","baja"), ("U11","U15","media")
    ]
    tx.run("""
        UNWIND $conexiones AS c 
        MATCH (u:Usuario {id: c[0]}), (v:Usuario {id: c[1]})
        MERGE (u)-[uv:CONECTA_CON]->(v)
        ON CREATE SET uv.fuerza_conexion = c[2]
        MERGE (v)-[vu:CONECTA_CON]->(u)
        ON CREATE SET vu.fuerza_conexion = c[2]
    """, conexiones=conexiones)

    # Trabajos y Empresas
    trabajos = [
        ("U5","E3","DevOps Engineer", True), ("U6","E2","Frontend Dev", True),
        ("U7","E4","Cloud Architect", True), ("U8","E3","Data Scientist", True),
        ("U10","E2","Scrum Master", True), ("U11","E1","Backend Developer", False),
        ("U14","E5","UX Designer", True), ("U15","E1","Fullstack Dev", True)
    ]
    tx.run("UNWIND $trabajos AS t MATCH (u:Usuario {id: t[0]}), (e:Empresa {id: t[1]}) MERGE (u)-[r:TRABAJA_EN]->(e) ON CREATE SET r.cargo = t[2], r.es_actual = t[3]", trabajos=trabajos)

    # Habilidades
    habs_usuarios = [
        ("U1","H1","avanzado"), ("U1","H2","avanzado"), ("U1","H3","avanzado"), ("U1","H7","avanzado"),
        ("U2","H1","avanzado"), ("U2","H3","avanzado"), ("U2","H4","avanzado"),
        ("U3","H5","avanzado"), ("U3","H8","avanzado"), ("U3","H1","intermedio"),
        ("U4","H1","avanzado"), ("U4","H3","avanzado"), ("U4","H2","intermedio"),
        ("U9","H5","avanzado"), ("U7","H10","avanzado"), ("U8","H1","avanzado"), ("U11","H4","avanzado")
    ]
    tx.run("UNWIND $hu AS h MATCH (u:Usuario {id: h[0]}), (hab:Habilidad {id: h[1]}) MERGE (u)-[r:TIENE_HABILIDAD]->(hab) ON CREATE SET r.nivel_dominio = h[2]", hu=habs_usuarios)

    # Participación en Proyectos
    participacion = [
        ("U1","P1","Arquitecto BD"), ("U2","P1","Backend Core"), ("U3","P1","Lógica de Negocio"), ("U4","P1","Analista de Datos"),
        ("U1","P2","Arquitecto BD"), ("U2","P2","Backend Core"), ("U3","P2","Lógica de Negocio"), ("U4","P2","Analista de Datos"),
        ("U3","P3","Diseño Lógico"), ("U4","P3","Validación"), ("U1","P3","Integración"), ("U9","P3","Hardware Tester"),
        ("U1","P4","Network Admin"), ("U7","P4","Consultor Externo")
    ]
    tx.run("UNWIND $part AS p MATCH (u:Usuario {id: p[0]}), (proy:Proyecto {id: p[1]}) MERGE (u)-[r:PARTICIPA_EN]->(proy) ON CREATE SET r.rol = p[2]", part=participacion)

    # Ofertas, Requisitos y Postulaciones
    publicaciones = [("E2","O1","2026-10-15"), ("E1","O2","2026-10-20"), ("E4","O3","2026-11-01"), ("E2","O4","2026-10-28"), ("E3","O5","2026-11-02")]
    tx.run("UNWIND $pub AS p MATCH (e:Empresa {id: p[0]}), (o:Oferta {id: p[1]}) MERGE (e)-[r:PUBLICA]->(o) ON CREATE SET r.fecha_publicacion = p[2]", pub=publicaciones)

    reqs = [("O1","H2",True), ("O1","H1",True), ("O2","H4",True), ("O2","H3",True), ("O3","H5",True), ("O4","H6",True), ("O5","H1",True), ("O5","H3",False)]
    tx.run("UNWIND $req AS r MATCH (o:Oferta {id: r[0]}), (h:Habilidad {id: r[1]}) MERGE (o)-[rel:REQUIERE]->(h) ON CREATE SET rel.es_obligatoria = r[2]", req=reqs)

    posts = [("U11","O2","aplicado","2026-10-25"), ("U9","O3","entrevistado","2026-11-02"), ("U8","O1","en revisión","2026-10-20")]
    tx.run("UNWIND $post AS p MATCH (u:Usuario {id: p[0]}), (o:Oferta {id: p[1]}) MERGE (u)-[r:POSTULA_A]->(o) ON CREATE SET r.estado_proceso = p[2], r.fecha_postulacion = p[3]", post=posts)

    # Conexiones Analíticas
    usa_tech = [("P1","H1"), ("P1","H2"), ("P2","H1"), ("P2","H4"), ("P2","H3"), ("P3","H5"), ("P4","H6")]
    tx.run("UNWIND $ut AS u MATCH (p:Proyecto {id: u[0]}), (h:Habilidad {id: u[1]}) MERGE (p)-[:USA_TECNOLOGIA]->(h)", ut=usa_tech)

    sigue = [("U1","E1"), ("U1","E2"), ("U2","E1"), ("U4","E3"), ("U9","E4")]
    tx.run("UNWIND $sig AS s MATCH (u:Usuario {id: s[0]}), (e:Empresa {id: s[1]}) MERGE (u)-[:SIGUE_A]->(e)", sig=sigue)

def inicializar_bd():
    if not URI or not AUTH[0] or not AUTH[1]:
        raise SystemExit("Faltan NEO4J_URI, NEO4J_USER o NEO4J_PASSWORD. Revisa el archivo .env.")

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.execute_write(crear_restricciones)
            session.execute_write(poblar_datos)
            print("Base de datos Neo4j inicializada correctamente.")


if __name__ == "__main__":
    inicializar_bd()
