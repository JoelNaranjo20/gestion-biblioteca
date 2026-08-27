"""Context processors compartidos por todas las plantillas."""

from __future__ import annotations


def operador_actual(request):
    """Expone el operador autenticado y su rol a las plantillas (barra superior, permisos de menú)."""
    user = getattr(request, "user", None)
    operador = None
    es_central = False
    if user is not None and user.is_authenticated:
        operador = getattr(user, "operador", None)
        es_central = bool(operador and operador.es_central) or user.is_superuser
    return {
        "operador_actual": operador,
        "es_central": es_central,
        "inactividad_segundos": _inactividad(),
    }


def _inactividad() -> int:
    from django.conf import settings

    return int(getattr(settings, "SESSION_INACTIVIDAD_SEGUNDOS", 1800))
