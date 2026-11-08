"""Enrutamiento de las pantallas privadas por tipo de cuenta."""

from backend_core import company_portal, user_portal


PAGINAS_USUARIO = {
    "Inicio": ("Inicio", "Resumen de tu perfil, red y oportunidades.") ,
    "Mi perfil": ("Mi perfil", "Presenta y actualiza tu trayectoria profesional."),
    "Mi red": ("Mi red", "Gestiona invitaciones y conexiones aceptadas."),
    "Usuarios": ("Profesionales", "Explora perfiles y conecta con otras personas."),
    "Empresas": ("Empresas", "Conoce organizaciones y sigue sus novedades."),
    "Ofertas": ("Oportunidades", "Vacantes ordenadas por cercanía y afinidad."),
    "Proyectos": ("Proyectos", "Explora proyectos y añade tu trayectoria."),
    "Recomendaciones": ("Recomendaciones", "Personas, empresas, proyectos y ofertas para ti."),
    "Consultas": ("Explorar la red", "Busca rutas profesionales entre tu perfil y una empresa."),
    "Mensajes": ("Mensajes", "Conversa con usuarios y empresas."),
}

PAGINAS_EMPRESA = {
    "Inicio": ("Inicio", "Actividad, postulaciones y perfiles afines."),
    "Mi empresa": ("Mi empresa", "Completa el perfil público de tu organización."),
    "Proyectos y ofertas": ("Proyectos y ofertas", "Crea proyectos y publica vacantes relacionadas."),
    "Postulaciones": ("Postulaciones", "Evalúa candidatos y actualiza cada proceso."),
    "Mensajes": ("Mensajes", "Conversa con profesionales y otras empresas."),
}


def renderizar_usuario(cuenta, pagina):
    user_portal.renderizar(cuenta, pagina)


def renderizar_empresa(cuenta, pagina):
    company_portal.renderizar(cuenta, pagina)
