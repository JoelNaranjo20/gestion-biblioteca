"""Middleware transversal."""

from __future__ import annotations

import logging

from django.db import Error as DBError
from django.db import InterfaceError, OperationalError
from django.shortcuts import render

log = logging.getLogger("biblioteca")


class ErrorConexionBDMiddleware:
    """Captura fallos de conexión con la base de datos en la nube y muestra una página clara.

    La app es solo en línea: si Supabase no responde, no se puede operar. Las escrituras son
    transaccionales, así que un corte a mitad no deja datos inconsistentes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, (OperationalError, InterfaceError)) or (
            isinstance(exception, DBError) and "could not connect" in str(exception).lower()
        ):
            log.error("Sin conexión con la base de datos: %s", exception)
            return render(request, "common/sin_conexion.html", status=503)
        return None
