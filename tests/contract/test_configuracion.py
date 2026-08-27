"""Contrato del endpoint de configuración de préstamo (T069)."""

import pytest

pytestmark = pytest.mark.django_db


def test_requiere_login(client, biblioteca):
    assert client.get("/configuracion/prestamos/").status_code == 302


def test_operador_403_central_200(client, central, operador):
    client.force_login(operador.user)
    assert client.get("/configuracion/prestamos/").status_code == 403
    client.force_login(central.user)
    assert client.get("/configuracion/prestamos/").status_code == 200


def test_post_guarda_valores(client, central):
    client.force_login(central.user)
    r = client.post("/configuracion/prestamos/", {"plazo_dias": "21", "max_prestamos_persona": "5"})
    assert r.status_code == 302
    from configuracion.models import get_parametros

    p = get_parametros()
    assert p.plazo_dias == 21 and p.max_prestamos_persona == 5


def test_post_rechaza_valor_invalido(client, central):
    client.force_login(central.user)
    r = client.post("/configuracion/prestamos/", {"plazo_dias": "0", "max_prestamos_persona": "3"})
    assert r.status_code == 200  # re-render con error
