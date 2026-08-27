"""Utilidades transversales de dominio."""

from __future__ import annotations

import datetime
import unicodedata


def normalizar_texto(valor: str | None) -> str:
    """Minúsculas + sin acentos + espacios colapsados.

    Se usa para búsqueda insensible a mayúsculas y acentos (espejo en Python del
    `immutable_unaccent(lower(...))` de PostgreSQL).
    """
    if not valor:
        return ""
    descompuesto = unicodedata.normalize("NFKD", valor)
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_acentos.lower().split())


def normalizar_isbn(valor: str | None) -> str:
    """Deja solo dígitos y una posible 'X' final; sirve para comparar ISBN sin guiones ni espacios."""
    if not valor:
        return ""
    return "".join(c for c in valor.upper() if c.isdigit() or c == "X")


def sumar_dias_naturales(fecha: datetime.date, dias: int) -> datetime.date:
    """Suma días naturales (sin ajustar por fines de semana ni festivos)."""
    return fecha + datetime.timedelta(days=dias)
