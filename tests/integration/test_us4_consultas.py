"""US4 — activos/vencidos, historial y reclamación (T062)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from catalogo.services import crear_ejemplar, crear_titulo
from prestamos.models import GestionReclamacion
from prestamos.services import (
    historial_ejemplar,
    historial_persona,
    prestamos_activos,
    prestamos_vencidos,
    registrar_devolucion,
    registrar_prestamo,
    registrar_reclamacion,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def datos(biblioteca, central, parametros):
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    for c in ("A-1", "A-2", "A-3"):
        crear_ejemplar(titulo_obj=t, codigo=c, actor=central.user)
    # A-1: activo y vencido; A-2: activo al día; A-3: devuelto
    registrar_prestamo(actor=central.user, codigo="A-1", documento="1", nombre="Uno", hoy=datetime.date(2020, 1, 1))
    registrar_prestamo(actor=central.user, codigo="A-2", documento="2", nombre="Dos")
    registrar_prestamo(actor=central.user, codigo="A-3", documento="3", nombre="Tres", hoy=datetime.date(2024, 1, 1))
    registrar_devolucion(actor=central.user, codigo="A-3", hoy=datetime.date(2024, 1, 10))
    return central


def test_activos_solo_no_devueltos(datos):
    codigos = {p.ejemplar.codigo for p in prestamos_activos()}
    assert codigos == {"A-1", "A-2"}


def test_vencidos_solo_pasados_de_fecha(datos):
    codigos = {p.ejemplar.codigo for p in prestamos_vencidos()}
    assert codigos == {"A-1"}


def test_historial_por_persona_y_por_ejemplar(datos, biblioteca):
    assert historial_persona("3").count() == 1
    from catalogo.models import Ejemplar

    ej = Ejemplar.objects.get(codigo="A-3")
    assert historial_ejemplar(ej).count() == 1


def test_reclamacion_visible_y_bloqueo_en_cerrado(datos):
    vencido = prestamos_vencidos().first()
    registrar_reclamacion(actor=datos.user, prestamo=vencido, fecha=datetime.date.today(), medio="telefono")
    assert GestionReclamacion.objects.filter(prestamo=vencido).count() == 1
    # cerrar el préstamo e intentar otra gestión
    registrar_devolucion(actor=datos.user, prestamo=vencido)
    with pytest.raises(ValidationError):
        registrar_reclamacion(actor=datos.user, prestamo=vencido, fecha=datetime.date.today(), medio="correo")
