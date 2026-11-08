from neo4j import GraphDatabase
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

def limpiar_bd(tx):
    # Ejecuta el borrado total de los nodos y sus relaciones
    tx.run("MATCH (n) DETACH DELETE n")

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
    tx.run("CREATE CONSTRAINT sesion_token_hash_unico IF NOT EXISTS FOR (s:Sesion) REQUIRE s.token_hash IS UNIQUE")

def poblar_datos(tx):
    # 1. NODOS: Usuarios (Se conservan U1-U4 para no romper asociar_correos.py)
    usuarios = [
        {"id": "U1", "nombre": "Jerónimo Castro", "perfil": "Arquitecto BD", "univ": "Universidad del Norte"},
        {"id": "U2", "nombre": "Juan Cáceres", "perfil": "Backend Developer", "univ": "Universidad del Norte"},
        {"id": "U3", "nombre": "Juan Arrieta", "perfil": "Business Logic Eng", "univ": "Universidad del Norte"},
        {"id": "U4", "nombre": "Miguel Carrizosa", "perfil": "Data Analyst", "univ": "Universidad del Norte"},
        {"id": "U5", "nombre": "Andrés Felipe Rojas", "perfil": "DevOps Engineer", "univ": "Universidad Nacional"},
        {"id": "U6", "nombre": "Laura Gómez", "perfil": "Frontend React", "univ": "Universidad de los Andes"},
        {"id": "U7", "nombre": "Carlos Mendoza", "perfil": "Cloud Architect", "univ": "Universidad del Norte"},
        {"id": "U8", "nombre": "Sofía Vergara", "perfil": "Data Scientist", "univ": "UIS"},
        {"id": "U9", "nombre": "David Pérez", "perfil": "Ingeniero de Software", "univ": "EAFIT"},
        {"id": "U10", "nombre": "Camila Ortiz", "perfil": "Scrum Master", "univ": "Sena"},
        {"id": "U11", "nombre": "Luis Martínez", "perfil": "Backend Django", "univ": "Universidad del Norte"},
        {"id": "U12", "nombre": "Ana Rodríguez", "perfil": "QA Tester", "univ": "Universidad de Antioquia"},
        {"id": "U13", "nombre": "Jorge Silva", "perfil": "Database Admin", "univ": "Universidad del Valle"},
        {"id": "U14", "nombre": "Valentina Ríos", "perfil": "UX/UI Designer", "univ": "Universidad de los Andes"},
        {"id": "U15", "nombre": "Mateo Blanco", "perfil": "Fullstack Developer", "univ": "Sena"},
        {"id": "U16", "nombre": "Daniela Santos", "perfil": "Product Manager", "univ": "Universidad Javeriana"},
        {"id": "U17", "nombre": "Javier Rueda", "perfil": "Ingeniero de Datos", "univ": "UIS"},
        {"id": "U18", "nombre": "Natalia Cruz", "perfil": "Security Engineer", "univ": "Universidad Nacional"},
        {"id": "U19", "nombre": "Felipe Vargas", "perfil": "Mobile Developer", "univ": "EAFIT"},
        {"id": "U20", "nombre": "Gabriela León", "perfil": "Machine Learning Eng", "univ": "Universidad de Antioquia"},
        {"id": "U21", "nombre": "Samuel Pino", "perfil": "SRE", "univ": "Universidad del Norte"},
        {"id": "U22", "nombre": "Isabella Mora", "perfil": "Cloud Ops", "univ": "Universidad Javeriana"},
        {"id": "U23", "nombre": "Martín Gil", "perfil": "Frontend Angular", "univ": "Sena"},
        {"id": "U24", "nombre": "Elena Vega", "perfil": "Data Analyst", "univ": "Universidad del Valle"},
        {"id": "U25", "nombre": "Tomás Herrera", "perfil": "Tech Lead", "univ": "Universidad de los Andes"}
    ]
    tx.run("""
        UNWIND $usuarios AS u
        MERGE (n:Usuario {id: u.id})
        ON CREATE SET n.nombre = u.nombre, n.perfil_profesional = u.perfil, n.universidad = u.univ
    """, usuarios=usuarios)

    # 2. NODOS: Empresas
    empresas = [
        {"id": "E1", "nombre": "Nubank", "sector": "Fintech"},
        {"id": "E2", "nombre": "Globant", "sector": "Consultoría IT"},
        {"id": "E3", "nombre": "Mercado Libre", "sector": "E-commerce"},
        {"id": "E4", "nombre": "Promigas", "sector": "Energía"},
        {"id": "E5", "nombre": "Rappi", "sector": "Tecnología Logística"},
        {"id": "E6", "nombre": "Bancolombia", "sector": "Banca"},
        {"id": "E7", "nombre": "Ecopetrol", "sector": "Petróleo y Energía"},
        {"id": "E8", "nombre": "Avianca", "sector": "Aerolíneas"},
        {"id": "E9", "nombre": "Kiwibot", "sector": "Robótica y Delivery"},
        {"id": "E10", "nombre": "Microsoft Colombia", "sector": "Software"}
    ]
    tx.run("UNWIND $empresas AS e MERGE (n:Empresa {id: e.id}) ON CREATE SET n.nombre = e.nombre, n.sector = e.sector", empresas=empresas)

    # 3. NODOS: Proyectos Corporativos (Nada de proyectos académicos)
    proyectos = [
        {"id": "P1", "nombre": "Migración Arquitectura Serverless", "desc": "Paso de monolito a microservicios en AWS Lambda"},
        {"id": "P2", "nombre": "Motor de Recomendación B2C", "desc": "Filtro colaborativo en tiempo real para e-commerce"},
        {"id": "P3", "nombre": "Core Bancario Cloud-Native", "desc": "Renovación transaccional con PostgreSQL y Kafka"},
        {"id": "P4", "nombre": "App Móvil de Inversiones", "desc": "Plataforma Fintech desarrollada en React Native"},
        {"id": "P5", "nombre": "Telemetría IoT", "desc": "Procesamiento de datos en streaming de flota robótica"},
        {"id": "P6", "nombre": "Dashboard Analítico C-Level", "desc": "BI y reporteo gerencial usando Neo4j y PowerBI"},
        {"id": "P7", "nombre": "Pipeline CI/CD Automatizado", "desc": "Reducción de tiempos de despliegue usando Docker y K8s"},
        {"id": "P8", "nombre": "Pasarela de Pagos Cripto", "desc": "Integración de cobros descentralizados y smart contracts"},
        {"id": "P9", "nombre": "Gestor Inteligente de Inventarios", "desc": "Predicción de demanda usando modelos de Machine Learning"},
        {"id": "P10", "nombre": "CRM Omnicanal B2B", "desc": "Plataforma de ventas con frontend React y backend Node.js"}
    ]
    tx.run("UNWIND $proyectos AS p MERGE (n:Proyecto {id: p.id}) ON CREATE SET n.nombre = p.nombre, n.descripcion = p.desc", proyectos=proyectos)

    # 4. NODOS: Habilidades
    habilidades = [
        {"id": "H1", "nombre": "Python", "cat": "técnica"}, {"id": "H2", "nombre": "Neo4j", "cat": "técnica"},
        {"id": "H3", "nombre": "PostgreSQL", "cat": "técnica"}, {"id": "H4", "nombre": "AWS", "cat": "técnica"},
        {"id": "H5", "nombre": "Docker", "cat": "técnica"}, {"id": "H6", "nombre": "Kubernetes", "cat": "técnica"},
        {"id": "H7", "nombre": "React", "cat": "técnica"}, {"id": "H8", "nombre": "Node.js", "cat": "técnica"},
        {"id": "H9", "nombre": "Java", "cat": "técnica"}, {"id": "H10", "nombre": "Machine Learning", "cat": "técnica"},
        {"id": "H11", "nombre": "Scrum", "cat": "blanda"}, {"id": "H12", "nombre": "Liderazgo", "cat": "blanda"},
        {"id": "H13", "nombre": "Comunicación Asertiva", "cat": "blanda"}, {"id": "H14", "nombre": "Kafka", "cat": "técnica"},
        {"id": "H15", "nombre": "Figma", "cat": "técnica"}
    ]
    tx.run("UNWIND $habs AS h MERGE (n:Habilidad {id: h.id}) ON CREATE SET n.nombre = h.nombre, n.categoria = h.cat", habs=habilidades)

    # 5. NODOS: Ofertas de empleo
    ofertas = [
        {"id": "O1", "titulo": "Senior Cloud Architect", "estado": "abierta", "mod": "remoto", "exp": "Senior"},
        {"id": "O2", "titulo": "Desarrollador Backend Python", "estado": "abierta", "mod": "híbrido", "exp": "Semi-Senior"},
        {"id": "O3", "titulo": "Data Engineer", "estado": "abierta", "mod": "remoto", "exp": "Junior"},
        {"id": "O4", "titulo": "Especialista DevOps", "estado": "abierta", "mod": "híbrido", "exp": "Senior"},
        {"id": "O5", "titulo": "Data Analyst Bilingüe", "estado": "abierta", "mod": "remoto", "exp": "Junior"},
        {"id": "O6", "titulo": "Tech Lead Mobile", "estado": "abierta", "mod": "híbrido", "exp": "Senior"},
        {"id": "O7", "titulo": "Frontend Developer React", "estado": "abierta", "mod": "remoto", "exp": "Semi-Senior"},
        {"id": "O8", "titulo": "Machine Learning Engineer", "estado": "abierta", "mod": "presencial", "exp": "Semi-Senior"},
        {"id": "O9", "titulo": "Database Administrator", "estado": "abierta", "mod": "híbrido", "exp": "Senior"},
        {"id": "O10", "titulo": "Product Manager Finanzas", "estado": "abierta", "mod": "híbrido", "exp": "Semi-Senior"},
        {"id": "O11", "titulo": "UX/UI Designer", "estado": "cerrada", "mod": "remoto", "exp": "Junior"},
        {"id": "O12", "titulo": "Security Engineer", "estado": "abierta", "mod": "remoto", "exp": "Senior"}
    ]
    tx.run("UNWIND $ofertas AS o MERGE (n:Oferta {id: o.id}) ON CREATE SET n.titulo = o.titulo, n.estado = o.estado, n.modalidad = o.mod, n.nivel_experiencia = o.exp", ofertas=ofertas)

    # 6. RELACIONES DINÁMICAS (El Grafo a gran escala)
    conexiones = [
        ("U1","U2","alta"), ("U1","U3","alta"), ("U1","U4","alta"), ("U2","U3","alta"), ("U3","U4","alta"),
        ("U1","U7","media"), ("U2","U11","baja"), ("U4","U8","alta"), ("U5","U7","alta"), ("U5","U14","media"),
        ("U6","U15","alta"), ("U8","U12","media"), ("U7","U10","alta"), ("U9","U13","baja"), ("U11","U15","media"),
        ("U16","U1","baja"), ("U17","U8","alta"), ("U18","U5","media"), ("U19","U6","alta"), ("U20","U8","alta"),
        ("U21","U5","media"), ("U22","U7","alta"), ("U23","U6","media"), ("U24","U4","alta"), ("U25","U10","alta"),
        ("U1","U25","media"), ("U3","U16","media"), ("U2","U17","baja"), ("U4","U20","alta"), ("U10","U16","alta")
    ]
    tx.run("""
        UNWIND $conexiones AS c 
        MATCH (u:Usuario {id: c[0]}), (v:Usuario {id: c[1]})
        MERGE (u)-[uv:CONECTA_CON]->(v)
        ON CREATE SET uv.fuerza_conexion = c[2]
        MERGE (v)-[vu:CONECTA_CON]->(u)
        ON CREATE SET vu.fuerza_conexion = c[2]
    """, conexiones=conexiones)

    trabajos = [
        ("U1","E1","Arquitecto BD", True), ("U2","E1","Backend Dev", True), ("U3","E6","Logic Engineer", True), 
        ("U4","E3","Data Analyst", True), ("U5","E2","DevOps Engineer", True), ("U6","E5","Frontend Dev", True),
        ("U7","E4","Cloud Architect", True), ("U8","E3","Data Scientist", True), ("U9","E10","Software Eng", True),
        ("U10","E2","Scrum Master", True), ("U11","E5","Backend Developer", False), ("U12","E7","QA Tester", True),
        ("U13","E6","DBA", True), ("U14","E8","UX Designer", True), ("U15","E9","Fullstack Dev", True),
        ("U16","E1","Product Manager", True), ("U17","E7","Data Engineer", True), ("U18","E6","Security Eng", True),
        ("U19","E5","Mobile Dev", True), ("U20","E3","ML Engineer", True), ("U21","E2","SRE", True),
        ("U22","E4","Cloud Ops", True), ("U23","E8","Frontend Dev", True), ("U24","E3","BI Analyst", True),
        ("U25","E1","Tech Lead", True)
    ]
    tx.run("UNWIND $trabajos AS t MATCH (u:Usuario {id: t[0]}), (e:Empresa {id: t[1]}) MERGE (u)-[r:TRABAJA_EN]->(e) ON CREATE SET r.cargo = t[2], r.es_actual = t[3]", trabajos=trabajos)

    habs_usuarios = [
        ("U1","H1","avanzado"), ("U1","H2","avanzado"), ("U1","H3","avanzado"), ("U1","H12","avanzado"),
        ("U2","H1","avanzado"), ("U2","H3","avanzado"), ("U2","H8","avanzado"), ("U3","H9","avanzado"), 
        ("U3","H1","intermedio"), ("U4","H1","avanzado"), ("U4","H3","avanzado"), ("U4","H2","intermedio"),
        ("U5","H4","avanzado"), ("U5","H5","avanzado"), ("U5","H6","avanzado"), ("U6","H7","avanzado"),
        ("U7","H4","avanzado"), ("U8","H1","avanzado"), ("U8","H10","avanzado"), ("U9","H9","avanzado"),
        ("U10","H11","avanzado"), ("U11","H1","avanzado"), ("U14","H15","avanzado"), ("U16","H11","avanzado"),
        ("U17","H14","avanzado"), ("U20","H10","avanzado"), ("U21","H5","avanzado"), ("U25","H12","avanzado")
    ]
    tx.run("UNWIND $hu AS h MATCH (u:Usuario {id: h[0]}), (hab:Habilidad {id: h[1]}) MERGE (u)-[r:TIENE_HABILIDAD]->(hab) ON CREATE SET r.nivel_dominio = h[2]", hu=habs_usuarios)

    participacion = [
        ("U1","P3","Arquitecto de Datos"), ("U2","P3","Backend Dev"), ("U13","P3","DBA"),
        ("U5","P1","DevOps Lead"), ("U7","P1","Cloud Architect"), ("U21","P1","SRE Support"),
        ("U8","P2","ML Engineer"), ("U20","P2","Data Scientist"), ("U4","P2","Analista"),
        ("U6","P4","Frontend Lead"), ("U19","P4","Mobile Dev"), ("U14","P4","UX/UI"),
        ("U11","P5","Backend Dev"), ("U17","P5","Data Engineer"), ("U25","P6","Tech Lead"),
        ("U4","P6","Data Analyst"), ("U10","P7","Scrum Master"), ("U5","P7","DevOps"),
        ("U9","P8","Software Eng"), ("U3","P8","Logic Eng"), ("U18","P8","SecOps"),
        ("U8","P9","Data Scientist"), ("U24","P9","BI Analyst"), ("U6","P10","Frontend"), 
        ("U2","P10","Backend")
    ]
    tx.run("UNWIND $part AS p MATCH (u:Usuario {id: p[0]}), (proy:Proyecto {id: p[1]}) MERGE (u)-[r:PARTICIPA_EN]->(proy) ON CREATE SET r.rol = p[2]", part=participacion)

    publicaciones = [
        ("E1","O1","2026-10-15"), ("E3","O2","2026-10-20"), ("E6","O3","2026-11-01"), 
        ("E2","O4","2026-10-28"), ("E5","O5","2026-11-02"), ("E1","O6","2026-11-03"),
        ("E8","O7","2026-10-30"), ("E3","O8","2026-11-04"), ("E6","O9","2026-10-15"),
        ("E1","O10","2026-11-05"), ("E5","O11","2026-10-01"), ("E6","O12","2026-11-06")
    ]
    tx.run("UNWIND $pub AS p MATCH (e:Empresa {id: p[0]}), (o:Oferta {id: p[1]}) MERGE (e)-[r:PUBLICA]->(o) ON CREATE SET r.fecha_publicacion = p[2]", pub=publicaciones)

    reqs = [
        ("O1","H4",True), ("O1","H5",True), ("O2","H1",True), ("O2","H3",True), 
        ("O3","H3",True), ("O3","H14",False), ("O4","H5",True), ("O4","H6",True), 
        ("O5","H1",True), ("O5","H3",False), ("O6","H7",True), ("O7","H7",True), 
        ("O8","H10",True), ("O8","H1",True), ("O9","H3",True), ("O9","H2",False),
        ("O10","H11",True), ("O10","H13",True), ("O11","H15",True), ("O12","H4",True)
    ]
    tx.run("UNWIND $req AS r MATCH (o:Oferta {id: r[0]}), (h:Habilidad {id: r[1]}) MERGE (o)-[rel:REQUIERE]->(h) ON CREATE SET rel.es_obligatoria = r[2]", req=reqs)

    posts = [
        ("U11","O2","aplicado","2026-10-25"), ("U17","O3","entrevistado","2026-11-02"), 
        ("U24","O5","en revisión","2026-10-20"), ("U19","O6","aplicado","2026-11-04"),
        ("U23","O7","rechazado","2026-11-01"), ("U20","O8","oferta","2026-11-05"),
        ("U13","O9","entrevistado","2026-10-28"), ("U18","O12","aplicado","2026-11-06")
    ]
    tx.run("UNWIND $post AS p MATCH (u:Usuario {id: p[0]}), (o:Oferta {id: p[1]}) MERGE (u)-[r:POSTULA_A]->(o) ON CREATE SET r.estado_proceso = p[2], r.fecha_postulacion = p[3]", post=posts)

    usa_tech = [
        ("P1","H4"), ("P1","H5"), ("P1","H6"), ("P2","H1"), ("P2","H10"), ("P3","H3"), ("P3","H14"), 
        ("P4","H7"), ("P4","H8"), ("P5","H14"), ("P5","H1"), ("P6","H2"), ("P6","H3"), ("P7","H5"), 
        ("P7","H6"), ("P8","H9"), ("P9","H1"), ("P9","H10"), ("P10","H7"), ("P10","H8")
    ]
    tx.run("UNWIND $ut AS u MATCH (p:Proyecto {id: u[0]}), (h:Habilidad {id: u[1]}) MERGE (p)-[:USA_TECNOLOGIA]->(h)", ut=usa_tech)

    sigue = [
        ("U1","E1"), ("U1","E6"), ("U2","E1"), ("U4","E3"), ("U5","E2"), 
        ("U7","E4"), ("U8","E3"), ("U10","E2"), ("U12","E7"), ("U16","E1"),
        ("U18","E6"), ("U20","E3"), ("U22","E10"), ("U25","E1")
    ]
    tx.run("UNWIND $sig AS s MATCH (u:Usuario {id: s[0]}), (e:Empresa {id: s[1]}) MERGE (u)-[:SIGUE_A]->(e)", sig=sigue)

def inicializar_bd():
    if not URI or not AUTH[0] or not AUTH[1]:
        raise SystemExit("Faltan NEO4J_URI, NEO4J_USER o NEO4J_PASSWORD. Revisa el archivo .env.")

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            # Primero borramos toda la base de datos
            session.execute_write(limpiar_bd)
            print("Base de datos limpiada correctamente.")
            
            # Luego creamos restricciones y poblamos
            session.execute_write(crear_restricciones)
            session.execute_write(poblar_datos)
            print("Base de datos Neo4j inicializada y poblada correctamente con datos corporativos.")

if __name__ == "__main__":
    inicializar_bd()