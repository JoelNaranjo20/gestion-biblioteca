"""Parámetros operativos de préstamo (una fila por biblioteca)."""

from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models

from common.models import ModeloBase
from cuentas.models import Biblioteca

PLAZO_DIAS_DEFECTO = 15
MAX_PRESTAMOS_PERSONA_DEFECTO = 3


class ParametrosPrestamo(ModeloBase):
    biblioteca = models.OneToOneField(Biblioteca, on_delete=models.PROTECT, related_name="parametros_prestamo")
    plazo_dias = models.PositiveIntegerField(
        "plazo de préstamo (días naturales)",
        default=PLAZO_DIAS_DEFECTO,
        validators=[MinValueValidator(1)],
    )
    max_prestamos_persona = models.PositiveIntegerField(
        "máximo de préstamos activos por persona",
        default=MAX_PRESTAMOS_PERSONA_DEFECTO,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "parámetros de préstamo"
        verbose_name_plural = "parámetros de préstamo"

    def __str__(self) -> str:
        return f"Plazo {self.plazo_dias} d · máx. {self.max_prestamos_persona}/persona"


def get_parametros(biblioteca: Biblioteca | None = None) -> ParametrosPrestamo:
    """Devuelve (creándola si hace falta) la configuración vigente de la biblioteca."""
    biblioteca = biblioteca or Biblioteca.actual()
    obj, _ = ParametrosPrestamo.objects.get_or_create(biblioteca=biblioteca)
    return obj
