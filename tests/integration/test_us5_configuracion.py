"""US5 — configuración de parámetros de préstamo (T070)."""

import datetime

import pytest

from catalogo.services import crear_ejemplar, crear_titulo
from configuracion.models import get_parametros
from prestamos.services import registrar_prestamo

pytestmark = pytest.mark.django_db


def test_cambio_de_plazo_solo_afecta_a_prestamos_nuevos(biblioteca, central, parametros):
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="P-1", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="P-2", actor=central.user)

    p1 = registrar_prestamo(
        actor=central.user, codigo="P-1", documento="1A", nombre="Ana", hoy=datetime.date(2026, 8, 27)
    )
    assert p1.fecha_limite == datetime.date(2026, 9, 11)  # 15 días

    params = get_parametros(biblioteca)
    params.plazo_dias = 21
    params.save()

    p2 = registrar_prestamo(
        actor=central.user, codigo="P-2", documento="2B", nombre="Bea", hoy=datetime.date(2026, 8, 27)
    )
    assert p2.fecha_limite == datetime.date(2026, 9, 17)  # 21 días
    p1.refresh_from_db()
    assert p1.fecha_limite == datetime.date(2026, 9, 11)  # no cambia


def test_configuracion_403_para_operador(client, central, operador):
    client.force_login(operador.user)
    assert client.get("/configuracion/prestamos/").status_code == 403
    client.force_login(central.user)
    assert client.get("/configuracion/prestamos/").status_code == 200
