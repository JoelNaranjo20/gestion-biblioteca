"""Contrato de endpoints de búsqueda y disponibilidad (T055)."""

import json

import pytest

from catalogo.models import Ejemplar, Titulo

pytestmark = pytest.mark.django_db


@pytest.fixture
def login(client, operador):
    client.force_login(operador.user)
    return client


@pytest.fixture
def catalogo(biblioteca):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="El Quijote", autor="Cervantes", isbn="9788437604947")
    Ejemplar.objects.create(titulo=t, codigo="Q-001")
    Ejemplar.objects.create(titulo=t, codigo="Q-002", estado=Ejemplar.Estado.PRESTADO)
    Ejemplar.objects.create(titulo=t, codigo="Q-003", estado=Ejemplar.Estado.RETIRADO, motivo_retirada="x")
    return t


def test_buscar_requiere_login(client, biblioteca):
    assert client.get("/catalogo/buscar/").status_code == 302


def test_buscar_html_y_recuentos(login, catalogo):
    r = login.get("/catalogo/buscar/", {"q": "quijote", "campo": "titulo"})
    assert r.status_code == 200
    assert b"El Quijote" in r.content


def test_buscar_sin_resultados(login, catalogo):
    r = login.get("/catalogo/buscar/", {"q": "zzzznoexiste", "campo": "titulo"})
    assert r.status_code == 200
    assert b"no se han encontrado" in r.content.lower()


def test_buscar_json_min_2_chars(login, catalogo):
    assert login.get("/catalogo/buscar.json", {"q": "q"}).status_code == 400
    r = login.get("/catalogo/buscar.json", {"q": "quijote"})
    assert r.status_code == 200
    datos = json.loads(r.content)
    assert datos["resultados"][0]["titulo"] == "El Quijote"
    assert datos["resultados"][0]["disponibles"] == 1
    assert datos["resultados"][0]["total"] == 3


def test_ejemplar_por_codigo_json(login, catalogo):
    r = login.get("/catalogo/ejemplar-por-codigo.json", {"codigo": "Q-001"})
    assert r.status_code == 200
    assert json.loads(r.content)["estado"] == "disponible"
    assert login.get("/catalogo/ejemplar-por-codigo.json", {"codigo": "NOEXISTE"}).status_code == 404
