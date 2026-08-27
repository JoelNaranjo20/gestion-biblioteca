"""Crea la biblioteca (cuenta central) sin interfaz. Útil para dev/CI y despliegues headless."""

from __future__ import annotations

import getpass

from django.core.management.base import BaseCommand, CommandError

from cuentas.models import Biblioteca
from cuentas.services import alta_biblioteca


class Command(BaseCommand):
    help = "Crea la biblioteca y su cuenta central."

    def add_arguments(self, parser):
        parser.add_argument("--nombre", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", help="Si se omite, se pregunta de forma interactiva.")
        parser.add_argument("--contacto", default="")

    def handle(self, *args, **opts):
        if Biblioteca.objects.exists():
            raise CommandError("La biblioteca ya está dada de alta.")
        password = opts["password"] or getpass.getpass("Contraseña de la cuenta central: ")
        operador = alta_biblioteca(
            nombre=opts["nombre"], email=opts["email"], password=password, contacto=opts["contacto"]
        )
        self.stdout.write(self.style.SUCCESS(f"Cuenta central creada: {operador.user.email}"))
