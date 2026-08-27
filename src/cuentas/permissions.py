"""Mixins y helpers de autorización."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def es_central(user) -> bool:
    if not user.is_authenticated:
        return False
    operador = getattr(user, "operador", None)
    return bool(operador and operador.es_central) or user.is_superuser


class SoloCentralMixin(LoginRequiredMixin):
    """Restringe la vista a la cuenta central (FR-030e)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not es_central(request.user):
            raise PermissionDenied("Esta acción está reservada a la cuenta central de la biblioteca.")
        return super().dispatch(request, *args, **kwargs)
