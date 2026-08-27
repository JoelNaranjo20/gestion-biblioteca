"""US2 — préstamos, devoluciones, tope y correcciones (T036)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from catalogo.models import Ejemplar
from catalogo.services import crear_ejemplar, crear_titulo
from configuracion.models import get_parametros
from prestamos.models import PersonaPrestataria, Prestamo
from prestamos.services import (
    EjemplarNoDisponible,
    TopeAlcanzado,
    anular_devolucion,
    anular_prestamo,
    registrar_devolucion,
    registrar_prestamo,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def ejemplar(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="Libro", autor="Autora", actor=central.user)
    return crear_ejemplar(titulo_obj=t, codigo="L-001", actor=central.user)


def test_prestamo_fija_estado_y_fecha_limite(biblioteca, central, parametros, ejemplar):
    p = registrar_prestamo(
        actor=central.user,
        codigo="L-001",
        documento="12345678A",
        nombre="Ana",
        hoy=datetime.date(2026, 8, 27),
    )
    ejemplar.refresh_from_db()
    assert ejemplar.estado == Ejemplar.Estado.PRESTADO
    assert p.fecha_limite == datetime.date(2026, 9, 11)  # +15 días


def test_no_se_puede_prestar_dos_veces(biblioteca, central, parametros, ejemplar):
    registrar_prestamo(actor=central.user, codigo="L-001", documento="1A", nombre="Ana")
    with pytest.raises(EjemplarNoDisponible):
        registrar_prestamo(actor=central.user, codigo="L-001", documento="2B", nombre="Bea")


def test_devolucion_libera_ejemplar_y_marca_retraso(biblioteca, central, parametros, ejemplar):
    registrar_prestamo(
        actor=central.user,
        codigo="L-001",
        documento="1A",
        nombre="Ana",
        hoy=datetime.date(2026, 8, 1),
    )
    p = registrar_devolucion(actor=central.user, codigo="L-001", hoy=datetime.date(2026, 9, 1))
    ejemplar.refresh_from_db()
    assert ejemplar.estado == Ejemplar.Estado.DISPONIBLE
    assert p.dias_retraso == (datetime.date(2026, 9, 1) - datetime.date(2026, 8, 16)).days


def test_devolucion_sin_prestamo_activo(biblioteca, central, parametros, ejemplar):
    with pytest.raises(ValidationError):
        registrar_devolucion(actor=central.user, codigo="L-001")


def test_tope_por_persona(biblioteca, central, parametros):
    get_parametros(biblioteca).__class__.objects.filter(pk=parametros.pk).update(max_prestamos_persona=2)
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    for i in range(2):
        crear_ejemplar(titulo_obj=t, codigo=f"C-{i}", actor=central.user)
        registrar_prestamo(actor=central.user, codigo=f"C-{i}", documento="99Z", nombre="Zoe")
    crear_ejemplar(titulo_obj=t, codigo="C-3", actor=central.user)
    with pytest.raises(TopeAlcanzado):
        registrar_prestamo(actor=central.user, codigo="C-3", documento="99Z", nombre="Zoe")


def test_retirar_prestado_bloqueado(biblioteca, central, parametros, ejemplar):
    from catalogo.services import retirar_ejemplar

    registrar_prestamo(actor=central.user, codigo="L-001", documento="1A", nombre="Ana")
    with pytest.raises(ValidationError):
        retirar_ejemplar(ejemplar=ejemplar, motivo="x", actor=central.user)


def test_anular_prestamo_libera_y_no_cuenta_para_tope(biblioteca, central, parametros, ejemplar):
    p = registrar_prestamo(actor=central.user, codigo="L-001", documento="1A", nombre="Ana")
    anular_prestamo(actor=central.user, prestamo=p, motivo="error de mostrador")
    p.refresh_from_db()
    ejemplar.refresh_from_db()
    assert p.estado_registro == Prestamo.EstadoRegistro.ANULADO
    assert ejemplar.estado == Ejemplar.Estado.DISPONIBLE
    persona = PersonaPrestataria.objects.get(documento="1A")
    from prestamos.services import _prestamos_activos_de

    assert _prestamos_activos_de(persona) == 0


def test_anular_devolucion_reactiva(biblioteca, central, parametros, ejemplar):
    registrar_prestamo(actor=central.user, codigo="L-001", documento="1A", nombre="Ana", hoy=datetime.date(2026, 1, 1))
    p = registrar_devolucion(actor=central.user, codigo="L-001", hoy=datetime.date(2026, 2, 1))
    anular_devolucion(actor=central.user, prestamo=p, motivo="se registró por error")
    p.refresh_from_db()
    ejemplar.refresh_from_db()
    assert p.fecha_devolucion_real is None
    assert ejemplar.estado == Ejemplar.Estado.PRESTADO


def test_documento_con_nombre_distinto_pide_confirmacion(biblioteca, central, parametros):
    from prestamos.services import NombreDistinto

    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="N-1", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="N-2", actor=central.user)
    registrar_prestamo(actor=central.user, codigo="N-1", documento="55X", nombre="Marta López")
    registrar_devolucion(actor=central.user, codigo="N-1")
    with pytest.raises(NombreDistinto):
        registrar_prestamo(actor=central.user, codigo="N-2", documento="55X", nombre="Marta Pérez")
    p = registrar_prestamo(
        actor=central.user, codigo="N-2", documento="55X", nombre="Marta Pérez", confirmar_nombre=True
    )
    assert p.persona.nombre == "Marta Pérez"
