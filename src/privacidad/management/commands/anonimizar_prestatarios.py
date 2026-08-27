"""Anonimiza los prestatarios que superan la ventana de retención (RGPD).

Programar a diario en el Programador de tareas de Windows:
    manage.exe anonimizar_prestatarios
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from privacidad.services import anonimizar_vencidas


class Command(BaseCommand):
    help = "Anonimiza prestatarios inactivos según la ventana de retención (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo informa; no anonimiza.")

    def handle(self, *args, **opts):
        if opts["dry_run"]:
            from privacidad.services import personas_anonimizables

            n = personas_anonimizables().count()
            self.stdout.write(f"Anonimizables ahora mismo: {n}")
            return
        n = anonimizar_vencidas()
        self.stdout.write(self.style.SUCCESS(f"Personas anonimizadas: {n}"))
