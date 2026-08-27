"""Reglas de dominio puras de préstamos (sin acceso a base de datos)."""

from __future__ import annotations

import datetime

from common.utils import sumar_dias_naturales


def calcular_fecha_limite(fecha_prestamo: datetime.date, plazo_dias: int) -> datetime.date:
    return sumar_dias_naturales(fecha_prestamo, plazo_dias)


def calcular_dias_retraso(fecha_limite: datetime.date, fecha_referencia: datetime.date) -> int:
    return max(0, (fecha_referencia - fecha_limite).days)


def valida_tope(prestamos_activos: int, maximo: int) -> bool:
    """True si se puede registrar un préstamo más."""
    return prestamos_activos < maximo
