"""Pruebas de las utilidades de dominio (T011)."""

import datetime

import pytest

from common.utils import normalizar_isbn, normalizar_texto, sumar_dias_naturales


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("El Quijóte", "el quijote"),
        ("  MÚLTIPLES   espacios ", "multiples espacios"),
        ("Ábaco Ñandú Über", "abaco nandu uber"),
        (None, ""),
        ("", ""),
    ],
)
def test_normalizar_texto(entrada, esperado):
    assert normalizar_texto(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("978-84-376-0494-7", "9788437604947"),
        ("  84 376 0494 X ", "843760494X"),
        (None, ""),
    ],
)
def test_normalizar_isbn(entrada, esperado):
    assert normalizar_isbn(entrada) == esperado


def test_sumar_dias_naturales_no_ajusta_por_findes():
    viernes = datetime.date(2026, 8, 28)  # viernes
    assert sumar_dias_naturales(viernes, 15) == datetime.date(2026, 9, 12)
