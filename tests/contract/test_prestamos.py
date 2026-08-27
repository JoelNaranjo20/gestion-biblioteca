"""Contrato de endpoints de préstamos, devoluciones y correcciones (T035)."""

import datetime

import pytest

from catalogo.models import Ejemplar, Titulo
from prestamos.models import Prestamo

pytestmark = pytest.mark.django_db


@pytest.fixture
def login(client, operador):
    client.force_login(operador.user)
    return client


@pytest.fixture
def ejemplar(biblioteca):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="Libro", autor="Autora")
    return Ejemplar.objects.create(titulo=t, codigo="L-001")


def test_nuevo_requiere_login(client, biblioteca):
    assert client.get("/prestamos/nuevo/").status_code == 302


def test_prestar_y_devolver_ciclo(login, parametros, ejemplar):
    r = login.post(
        "/prestamos/nuevo/",
        {"codigo": "L-001", "documento": "1A", "nombre": "Ana", "contacto": ""},
    )
    assert r.status_code == 302
    ejemplar.refresh_from_db()
    assert ejemplar.estado == Ejemplar.Estado.PRESTADO

    r = login.post("/prestamos/devolver/", {"codigo": "L-001"})
    assert r.status_code == 302
    ejemplar.refresh_from_db()
    assert ejemplar.estado == Ejemplar.Estado.DISPONIBLE


def test_prestar_ejemplar_no_disponible_re_renderiza(login, parametros, ejemplar):
    login.post("/prestamos/nuevo/", {"codigo": "L-001", "documento": "1A", "nombre": "Ana", "contacto": ""})
    r = login.post("/prestamos/nuevo/", {"codigo": "L-001", "documento": "2B", "nombre": "Bea", "contacto": ""})
    assert r.status_code == 200
    assert b"no est" in r.content.lower()  # "no está disponible"


def test_devolver_sin_prestamo_activo_re_renderiza(login, parametros, ejemplar):
    r = login.post("/prestamos/devolver/", {"codigo": "L-001"})
    assert r.status_code == 200
    assert b"activo" in r.content.lower()


def test_anular_prestamo_pide_motivo(login, parametros, ejemplar):
    login.post("/prestamos/nuevo/", {"codigo": "L-001", "documento": "1A", "nombre": "Ana", "contacto": ""})
    p = Prestamo.objects.get(ejemplar=ejemplar)
    assert login.get(f"/prestamos/{p.pk}/anular/").status_code == 200
    r = login.post(f"/prestamos/{p.pk}/anular/", {"motivo": "error"})
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.estado_registro == Prestamo.EstadoRegistro.ANULADO


def test_detalle_y_listas(login, parametros, ejemplar):
    login.post("/prestamos/nuevo/", {"codigo": "L-001", "documento": "1A", "nombre": "Ana", "contacto": ""})
    p = Prestamo.objects.get(ejemplar=ejemplar)
    assert login.get(f"/prestamos/{p.pk}/").status_code == 200
    assert login.get("/prestamos/activos/").status_code == 200
    assert login.get("/prestamos/vencidos/").status_code == 200


def test_anular_retirada_endpoint(login, biblioteca):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="T", autor="A")
    ej = Ejemplar.objects.create(titulo=t, codigo="AR-1", estado=Ejemplar.Estado.RETIRADO, motivo_retirada="x")
    r = login.post(f"/catalogo/ejemplares/{ej.pk}/anular-retirada/", {"motivo": "fue un error"})
    assert r.status_code == 302
    ej.refresh_from_db()
    assert ej.estado == Ejemplar.Estado.DISPONIBLE


def test_reclamacion_endpoint_para_prestamo_vencido(login, central, parametros, ejemplar):
    from prestamos.services import registrar_prestamo

    p = registrar_prestamo(
        actor=central.user,
        codigo="L-001",
        documento="1A",
        nombre="Ana",
        hoy=datetime.date(2020, 1, 1),
    )
    assert login.get(f"/prestamos/{p.pk}/reclamaciones/nueva/").status_code == 200
    r = login.post(
        f"/prestamos/{p.pk}/reclamaciones/nueva/",
        {"fecha": datetime.date.today().isoformat(), "medio": "telefono", "notas": ""},
    )
    assert r.status_code == 302
    assert p.reclamaciones.count() == 1


def test_persona_historial_endpoint(login, central, parametros, ejemplar):
    from prestamos.services import registrar_prestamo

    registrar_prestamo(actor=central.user, codigo="L-001", documento="55X", nombre="Marta")
    r = login.get("/personas/historial/?documento=55X")
    assert r.status_code == 200
    assert b"55X" in r.content or b"Marta" in r.content
