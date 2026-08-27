"""Genera un catálogo de demostración para pruebas de carga y de rendimiento (SC-003 / SC-007).

Ejemplo:
    python manage.py sembrar_datos_demo --titulos 20000 --ejemplares-por-titulo 2
"""

from __future__ import annotations

import random
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogo.models import Ejemplar, Titulo
from common.utils import normalizar_isbn, normalizar_texto
from cuentas.models import Biblioteca

PALABRAS = [
    "sombra",
    "luz",
    "camino",
    "mar",
    "montaña",
    "ciudad",
    "silencio",
    "memoria",
    "tiempo",
    "fuego",
    "agua",
    "viento",
    "historia",
    "jardín",
    "noche",
    "estrella",
    "puente",
    "océano",
    "bosque",
    "desierto",
]
AUTORES = ["García", "Martín", "López", "Sánchez", "Núñez", "Ferrán", "Ibáñez", "Öz", "Müller"]
MATERIAS = ["Narrativa", "Poesía", "Historia", "Ciencia", "Infantil", "Ensayo", "Arte"]


class Command(BaseCommand):
    help = "Crea títulos y ejemplares de demostración (borra los previos de demostración)."

    def add_arguments(self, parser):
        parser.add_argument("--titulos", type=int, default=20000)
        parser.add_argument("--ejemplares-por-titulo", type=int, default=2, dest="ept")
        parser.add_argument("--lote", type=int, default=2000)

    @transaction.atomic
    def handle(self, *args, **opts):
        biblioteca = Biblioteca.actual()
        if biblioteca is None:
            raise CommandError("No hay biblioteca. Ejecuta 'crear_biblioteca' primero.")
        n, ept, lote = opts["titulos"], opts["ept"], opts["lote"]
        rng = random.Random(42)
        t0 = time.perf_counter()

        creados = 0
        for inicio in range(0, n, lote):
            fin = min(inicio + lote, n)
            titulos = []
            for i in range(inicio, fin):
                titulo = f"{rng.choice(PALABRAS).capitalize()} {rng.choice(PALABRAS)} {i}"
                autor = f"{rng.choice(AUTORES)}, {rng.choice(['A.', 'M.', 'J.', 'L.'])}"
                materia = rng.choice(MATERIAS)
                isbn = f"978{rng.randint(1000000000, 9999999999)}"
                titulos.append(
                    Titulo(
                        biblioteca=biblioteca,
                        titulo=titulo,
                        autor=autor,
                        materia=materia,
                        isbn=isbn,
                        isbn_norm=normalizar_isbn(isbn),
                        busqueda_norm=normalizar_texto(f"{titulo} {autor} {materia}"),
                    )
                )
            Titulo.objects.bulk_create(titulos)
            ejemplares = []
            for t in titulos:
                for k in range(ept):
                    ejemplares.append(Ejemplar(titulo=t, codigo=f"D{t.id:07d}-{k}"))
            Ejemplar.objects.bulk_create(ejemplares)
            creados += len(titulos)
            self.stdout.write(f"  {creados}/{n} títulos…", ending="\r")

        seg = time.perf_counter() - t0
        self.stdout.write(self.style.SUCCESS(f"\n{creados} títulos y {creados * ept} ejemplares en {seg:.1f}s."))
