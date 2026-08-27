"""US2 — reglas de dominio puras (T041)."""

import datetime

from prestamos.rules import calcular_dias_retraso, calcular_fecha_limite, valida_tope


def test_calcular_fecha_limite_dias_naturales():
    assert calcular_fecha_limite(datetime.date(2026, 8, 27), 15) == datetime.date(2026, 9, 11)


def test_calcular_dias_retraso():
    assert calcular_dias_retraso(datetime.date(2026, 9, 11), datetime.date(2026, 9, 11)) == 0
    assert calcular_dias_retraso(datetime.date(2026, 9, 11), datetime.date(2026, 9, 15)) == 4
    assert calcular_dias_retraso(datetime.date(2026, 9, 11), datetime.date(2026, 9, 1)) == 0


def test_valida_tope():
    assert valida_tope(2, 3) is True
    assert valida_tope(3, 3) is False
    assert valida_tope(4, 3) is False
