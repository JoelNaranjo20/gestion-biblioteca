"""Vistas transversales: página de inicio y comprobación de conexión."""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render

from cuentas.models import Biblioteca


@login_required
def inicio(request):
    """Panel de inicio con accesos a las tareas de mostrador."""
    return render(request, "common/inicio.html")


def raiz(request):
    """Redirige según el estado: alta de biblioteca, login o inicio."""
    if not Biblioteca.objects.exists():
        return redirect("cuentas:alta_biblioteca")
    if not request.user.is_authenticated:
        return redirect("cuentas:entrar")
    return redirect("inicio")


def ping_conexion(request):
    """Comprueba que la base de datos responde (indicador de estado en la cabecera)."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return JsonResponse({"ok": True})
    except Exception:  # noqa: BLE001 - cualquier fallo cuenta como "sin conexión"
        return JsonResponse({"ok": False}, status=503)
