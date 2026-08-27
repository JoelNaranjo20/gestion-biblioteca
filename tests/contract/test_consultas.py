"""Contrato de endpoints de consultas y reclamación (T061)."""

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def login(client, operador):
    client.force_login(operador.user)
    return client


def test_endpoints_requieren_login(client, biblioteca):
    for url in ("/prestamos/activos/", "/prestamos/vencidos/", "/personas/historial/"):
        assert client.get(url).status_code == 302


def test_listas_vacias_ok(login, biblioteca):
    assert login.get("/prestamos/activos/").status_code == 200
    assert login.get("/prestamos/vencidos/").status_code == 200


def test_persona_historial_vacio_para_documento_inexistente(login, biblioteca):
    r = login.get("/personas/historial/", {"documento": "NADIE"})
    assert r.status_code == 200
    assert b"sin resultados" in r.content.lower()
