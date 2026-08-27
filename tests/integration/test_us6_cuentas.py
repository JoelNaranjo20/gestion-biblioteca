"""US6 — alta de biblioteca, gestión de operadores y atribución (T050)."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from cuentas.models import Biblioteca, EntradaAuditoria
from cuentas.services import alta_biblioteca, crear_operador, fijar_estado_operador

pytestmark = pytest.mark.django_db


def test_alta_biblioteca_crea_cuenta_central_y_audita():
    operador = alta_biblioteca(nombre="Biblio", email="dir@ayto.org", password="clave-larga-1", contacto="x")
    assert Biblioteca.objects.count() == 1
    assert operador.es_central is True
    assert operador.user.email == "dir@ayto.org"
    assert EntradaAuditoria.objects.filter(tipo_operacion="alta_biblioteca").exists()


def test_alta_biblioteca_falla_si_ya_existe(biblioteca):
    with pytest.raises(ValidationError):
        alta_biblioteca(nombre="Otra", email="x@x.org", password="clave-larga-1")


def test_crear_operador_sin_correo_y_rechaza_username_duplicado(central):
    op = crear_operador(
        biblioteca=central.biblioteca,
        username="mostrador1",
        password="clave-larga-1",
        actor=central.user,
    )
    assert op.user.email == ""
    assert op.esta_activa is True
    with pytest.raises(ValidationError):
        crear_operador(biblioteca=central.biblioteca, username="MOSTRADOR1", password="clave-larga-1")


def test_desactivar_operador_impide_login_pero_conserva_atribucion(central, client):
    op = crear_operador(biblioteca=central.biblioteca, username="mostrador2", password="clave-larga-1")
    EntradaAuditoria.objects.create(
        biblioteca=central.biblioteca,
        actor=op.user,
        tipo_operacion="prestamo",
        entidad=EntradaAuditoria.Entidad.PRESTAMO,
        entidad_id=1,
    )
    fijar_estado_operador(operador=op, activo=False, actor=central.user)

    op.refresh_from_db()
    assert op.user.is_active is False
    assert client.login(username="mostrador2", password="clave-larga-1") is False
    assert EntradaAuditoria.objects.filter(actor=op.user, tipo_operacion="prestamo").exists()


def test_solo_central_ve_gestion_de_operadores(client, central, operador):
    User = get_user_model()  # noqa: N806
    assert User.objects.filter(username="mostrador1").exists()

    client.force_login(operador.user)
    resp = client.get("/operadores/nuevo/")
    assert resp.status_code == 403

    client.force_login(central.user)
    resp = client.get("/operadores/")
    assert resp.status_code == 200
