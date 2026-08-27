"""Contrato de endpoints de cuentas (T049)."""

import pytest

pytestmark = pytest.mark.django_db


def test_alta_biblioteca_get_sin_biblioteca(client):
    r = client.get("/inicio/alta-biblioteca/")
    assert r.status_code == 200


def test_alta_biblioteca_redirige_si_ya_existe(client, biblioteca):
    r = client.get("/inicio/alta-biblioteca/")
    assert r.status_code == 302
    assert "/acceso/entrar/" in r["Location"]


def test_alta_biblioteca_post_crea_cuenta_central(client):
    r = client.post(
        "/inicio/alta-biblioteca/",
        {
            "nombre_biblioteca": "Biblio",
            "email": "dir@ayto.org",
            "contacto": "",
            "password": "clave-larga-1",
            "password2": "clave-larga-1",
        },
    )
    assert r.status_code == 302
    from cuentas.models import Biblioteca

    assert Biblioteca.objects.count() == 1


def test_operadores_requiere_login(client, biblioteca):
    r = client.get("/operadores/")
    assert r.status_code == 302
    assert "/acceso/entrar/" in r["Location"]


def test_operadores_operador_403_central_200(client, central, operador):
    client.force_login(operador.user)
    assert client.get("/operadores/").status_code == 403
    assert client.get("/operadores/nuevo/").status_code == 403
    client.force_login(central.user)
    assert client.get("/operadores/").status_code == 200


def test_crear_operador_rechaza_username_duplicado(client, central, operador):
    client.force_login(central.user)
    r = client.post(
        "/operadores/nuevo/",
        {"username": "mostrador1", "nombre_visible": "", "password": "clave-larga-1", "password2": "clave-larga-1"},
    )
    assert r.status_code == 200  # re-render con error
    assert b"ya existe" in r.content.lower() or b"mostrador1" in r.content.lower()


def test_username_disponible_htmx(client, central, operador):
    client.force_login(central.user)
    assert b"ya existe" in client.get("/operadores/disponible/?username=mostrador1").content.lower()
    assert b"disponible" in client.get("/operadores/disponible/?username=libre99").content.lower()


def test_auditoria_lista_operador_ok(client, operador):
    client.force_login(operador.user)
    assert client.get("/auditoria/").status_code == 200


def test_renombrar_operador(client, central, operador):
    client.force_login(central.user)
    assert client.get(f"/operadores/{operador.pk}/renombrar/").status_code == 200
    r = client.post(f"/operadores/{operador.pk}/renombrar/", {"nombre_visible": "Mostrador Central"})
    assert r.status_code == 302
    operador.refresh_from_db()
    assert operador.nombre_visible == "Mostrador Central"


def test_renombrar_operador_403_para_operador(client, operador):
    client.force_login(operador.user)
    assert client.get(f"/operadores/{operador.pk}/renombrar/").status_code == 403
