"""Modelos del catálogo: títulos y ejemplares."""

from __future__ import annotations

from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MaxValueValidator
from django.db import models

from common.models import ModeloBase
from common.utils import normalizar_isbn, normalizar_texto
from cuentas.models import Biblioteca


class Titulo(ModeloBase):
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="titulos")
    titulo = models.CharField("título", max_length=300)
    autor = models.CharField("autor", max_length=200)
    isbn = models.CharField("ISBN", max_length=20, blank=True)
    isbn_norm = models.CharField(max_length=20, blank=True, editable=False, db_index=True)
    editorial = models.CharField("editorial", max_length=200, blank=True)
    anio = models.PositiveIntegerField(
        "año de publicación", null=True, blank=True, validators=[MaxValueValidator(2100)]
    )
    materia = models.CharField("materia / categoría", max_length=120, blank=True)
    busqueda_norm = models.CharField(max_length=700, blank=True, editable=False)

    class Meta:
        verbose_name = "título"
        verbose_name_plural = "títulos"
        ordering = ["titulo", "autor"]
        indexes = [
            GinIndex(
                name="catalogo_titulo_busq_gin",
                fields=["busqueda_norm"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.titulo} — {self.autor}"

    def save(self, *args, **kwargs):
        self.isbn_norm = normalizar_isbn(self.isbn)
        self.busqueda_norm = normalizar_texto(f"{self.titulo} {self.autor} {self.materia}")
        super().save(*args, **kwargs)

    @property
    def total_ejemplares(self) -> int:
        return self.ejemplares.count()

    @property
    def ejemplares_disponibles(self) -> int:
        return self.ejemplares.filter(estado=Ejemplar.Estado.DISPONIBLE).count()


class Ejemplar(ModeloBase):
    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        PRESTADO = "prestado", "Prestado"
        RETIRADO = "retirado", "Retirado"

    titulo = models.ForeignKey(Titulo, on_delete=models.PROTECT, related_name="ejemplares")
    codigo = models.CharField("código de ejemplar", max_length=40, unique=True)
    estado = models.CharField("estado", max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    motivo_retirada = models.CharField("motivo de retirada", max_length=200, blank=True)
    ubicacion = models.CharField("ubicación / signatura", max_length=120, blank=True)

    class Meta:
        verbose_name = "ejemplar"
        verbose_name_plural = "ejemplares"
        ordering = ["codigo"]
        indexes = [models.Index(fields=["titulo", "estado"])]

    def __str__(self) -> str:
        return f"{self.codigo} ({self.get_estado_display()})"

    @property
    def esta_disponible(self) -> bool:
        return self.estado == self.Estado.DISPONIBLE

    @property
    def esta_prestado(self) -> bool:
        return self.estado == self.Estado.PRESTADO

    @property
    def esta_retirado(self) -> bool:
        return self.estado == self.Estado.RETIRADO
