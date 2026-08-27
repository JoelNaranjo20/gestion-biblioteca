"""US3 — búsqueda insensible a acentos/mayúsculas y disponibilidad (T056)."""

import pytest

from catalogo.models import Ejemplar, Titulo
from catalogo.services import buscar_titulos

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo(biblioteca):
    t1 = Titulo.objects.create(
        biblioteca=biblioteca, titulo="El Camión de la Ñora", autor="José Ibáñez", materia="Infantil"
    )
    t2 = Titulo.objects.create(biblioteca=biblioteca, titulo="Óptica moderna", autor="Ana Pérez", isbn="978-84-1-2")
    Ejemplar.objects.create(titulo=t1, codigo="C-1")
    Ejemplar.objects.create(titulo=t1, codigo="C-2", estado=Ejemplar.Estado.PRESTADO)
    Ejemplar.objects.create(titulo=t1, codigo="C-3", estado=Ejemplar.Estado.RETIRADO, motivo_retirada="x")
    Ejemplar.objects.create(titulo=t2, codigo="O-1")
    return t1, t2


def test_busqueda_ignora_acentos_y_mayusculas(catalogo):
    assert buscar_titulos(texto="camion", campo="titulo").count() == 1
    assert buscar_titulos(texto="CAMIÓN", campo="titulo").count() == 1
    assert buscar_titulos(texto="nora", campo="titulo").count() == 1


def test_busqueda_por_autor_y_materia(catalogo):
    assert buscar_titulos(texto="ibanez", campo="autor").count() == 1
    assert buscar_titulos(texto="infantil", campo="materia").count() == 1


def test_busqueda_por_isbn_normalizado(catalogo):
    assert buscar_titulos(texto="9788412", campo="isbn").count() == 1


def test_recuento_disponibles_con_3_estados(catalogo):
    t1, _ = catalogo
    fila = buscar_titulos(texto="camion", campo="titulo").get(pk=t1.pk)
    assert fila.n_total == 3
    assert fila.n_disponibles == 1


def test_busqueda_vacia_no_devuelve_nada(catalogo):
    assert buscar_titulos(texto="", campo="titulo").count() == 0
