from collections import Counter, defaultdict
from pathlib import Path

from backend_core.portal_common import consultar

CONSULTAS = Path(__file__).resolve().parents[1] / "analytics_dashboard" / "consultas_cypher"


def _archivo(nombre, **parametros):
    texto = (CONSULTAS / nombre).read_text(encoding="utf-8-sig")
    return consultar(texto, **parametros) or []


# --- Selectores ------------------------------------------------------------------

def usuarios_opciones():
    return consultar("MATCH (u:Usuario) RETURN u.id AS id, u.nombre AS nombre ORDER BY nombre") or []


def empresas_opciones():
    return consultar("MATCH (e:Empresa) RETURN e.id AS id, e.nombre AS nombre ORDER BY nombre") or []


def ofertas_opciones():
    return consultar(
        """
        MATCH (o:Oferta)
        OPTIONAL MATCH (e:Empresa)-[:PUBLICA]->(o)
        RETURN o.id AS id, o.titulo AS nombre, e.nombre AS empresa, o.estado AS estado
        ORDER BY nombre
        """
    ) or []


def empresa_publica_oferta(empresa_id, oferta_id):
    return bool(
        consultar(
            "MATCH (:Empresa {id: $e})-[:PUBLICA]->(o:Oferta {id: $o}) RETURN o.id AS id",
            e=empresa_id, o=oferta_id,
        )
    )


# --- Panel de analítica (global) ---------------------------------------------------

def resumen():
    filas = consultar("MATCH (n) RETURN labels(n)[0] AS entidad, count(*) AS cantidad") or []
    totales = {f["entidad"]: f["cantidad"] for f in filas}
    return {k: totales.get(k, 0) for k in ("Usuario", "Empresa", "Oferta", "Habilidad", "Proyecto")}


def usuarios_influyentes():
    return _archivo("usuarios_mas_influyentes.cypher")


def habilidades_demandadas():
    return _archivo("habilidades_mas_demandadas.cypher")


def comunidades(max_iteraciones=30):
    """Label Propagation sobre CONECTA_CON, calculado aquí (no requiere GDS)."""
    filas = _archivo("comunidades_detectadas.cypher")
    nombres = {f["usuario_id"]: f["usuario"] for f in filas}
    grafo = {uid: set() for uid in nombres}
    for f in filas:
        for contacto in f["contactos_ids"] or []:
            if contacto is not None:
                nombres.setdefault(contacto, contacto)
                grafo.setdefault(f["usuario_id"], set()).add(contacto)
                grafo.setdefault(contacto, set()).add(f["usuario_id"])

    etiquetas = {uid: uid for uid in grafo}
    for _ in range(max_iteraciones):
        cambios = False
        for uid in sorted(grafo):
            vecinos = grafo[uid]
            if not vecinos:
                continue
            frecuencias = Counter(etiquetas[v] for v in vecinos)
            maxima = max(frecuencias.values())
            ganadora = min(e for e, fr in frecuencias.items() if fr == maxima)
            if etiquetas[uid] != ganadora:
                etiquetas[uid] = ganadora
                cambios = True
        if not cambios:
            break

    grupos = defaultdict(list)
    for uid, etiqueta in etiquetas.items():
        grupos[etiqueta].append(uid)
    ordenados = sorted((sorted(m) for m in grupos.values()), key=lambda m: (-len(m), m[0]))
    return [
        {
            "comunidad": numero,
            "usuarios": len(miembros),
            "miembros": [{"id": uid, "nombre": nombres.get(uid, uid)} for uid in miembros],
        }
        for numero, miembros in enumerate(ordenados, start=1)
    ]


# --- Preguntas sobre relaciones (global) ---------------------------------------------

def contactos_en_comun():
    return _archivo("contactos_en_comun.cypher")


def habilidades_similares():
    return _archivo("habilidades_similares.cypher")


def proyectos_por_miembros():
    return _archivo("proyectos_miembros_compartidos.cypher")


def proyectos_por_tecnologias():
    return _archivo("proyectos_tecnologias_compartidas.cypher")


# --- Consultas con parámetros --------------------------------------------------------

def ruta_mas_corta(usuario_id, empresa_id):
    filas = _archivo("ruta_mas_corta_usuario_empresa.cypher", usuario_id=usuario_id, empresa_id=empresa_id)
    return filas[0] if filas else None


def recomendaciones_contactos(usuario_id):
    return _archivo("recomendaciones_contactos.cypher", usuario_id=usuario_id)


def recomendaciones_colaboradores(usuario_id):
    return _archivo("recomendaciones_colaboradores.cypher", usuario_id=usuario_id)


def candidatos_para_oferta(oferta_id):
    return _archivo("candidatos_recomendados_para_oferta.cypher", oferta_id=oferta_id)