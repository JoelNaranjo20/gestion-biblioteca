"""US1 — ciclo de catálogo (T026)."""

import pytest
from django.core.exceptions import ValidationError

from catalogo.models import Ejemplar, Titulo
from catalogo.services import (
    IsbnDuplicado,
    crear_ejemplar,
    crear_titulo,
    retirar_ejemplar,
    titulos_con_recuento,
)

pytestmark = pytest.mark.django_db


def test_alta_titulo_con_ejemplar_y_recuento(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="El Quijote", autor="Cervantes", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="Q-001", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="Q-002", actor=central.user)
    t = titulos_con_recuento().get(pk=t.pk)
    assert t.n_total == 2
    assert t.n_disponibles == 2


def test_titulo_sin_autor_rechazado(biblioteca):
    with pytest.raises(ValidationError):
        crear_titulo(biblioteca=biblioteca, titulo="Sin autor", autor="  ")


def test_codigo_ejemplar_duplicado_rechazado(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="X", autor="Y", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="DUP-1", actor=central.user)
    with pytest.raises(ValidationError):
        crear_ejemplar(titulo_obj=t, codigo="DUP-1", actor=central.user)


def test_retirar_ejemplar_reduce_disponibles(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="X", autor="Y", actor=central.user)
    ej = crear_ejemplar(titulo_obj=t, codigo="R-1", actor=central.user)
    retirar_ejemplar(ejemplar=ej, motivo="deteriorado", actor=central.user)
    ej.refresh_from_db()
    assert ej.estado == Ejemplar.Estado.RETIRADO
    assert titulos_con_recuento().get(pk=t.pk).n_disponibles == 0


def test_isbn_duplicado_avisa_pero_permite_confirmar(biblioteca, central):
    crear_titulo(biblioteca=biblioteca, titulo="A", autor="B", isbn="978-84-376-0494-7", actor=central.user)
    with pytest.raises(IsbnDuplicado):
        crear_titulo(biblioteca=biblioteca, titulo="C", autor="D", isbn="9788437604947", actor=central.user)
    t2 = crear_titulo(
        biblioteca=biblioteca,
        titulo="C",
        autor="D",
        isbn="9788437604947",
        actor=central.user,
        confirmar_isbn=True,
    )
    assert Titulo.objects.filter(isbn_norm="9788437604947").count() == 2
    assert t2.pk
