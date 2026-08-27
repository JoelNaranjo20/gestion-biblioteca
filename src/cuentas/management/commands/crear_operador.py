"""Crea una subcuenta de operador sin interfaz."""

from __future__ import annotations

import getpass

from django.core.management.base import BaseCommand, CommandError

from cuentas.models import Biblioteca
from cuentas.services import crear_operador


class Command(BaseCommand):
    help = "Crea una subcuenta de operador (sin correo)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", help="Si se omite, se pregunta de forma interactiva.")
        parser.add_argument("--nombre-visible", dest="nombre_visible", default="")

    def handle(self, *args, **opts):
        biblioteca = Biblioteca.actual()
        if biblioteca is None:
            raise CommandError("No hay biblioteca. Ejecuta primero 'crear_biblioteca'.")
        password = opts["password"] or getpass.getpass("Contraseña del operador: ")
        operador = crear_operador(
            biblioteca=biblioteca,
            username=opts["username"],
            password=password,
            nombre_visible=opts["nombre_visible"],
        )
        self.stdout.write(self.style.SUCCESS(f"Operador creado: {operador.username}"))
