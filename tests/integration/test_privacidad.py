"""Polish / RGPD — anonimización de prestatarios (T077)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from catalogo.services import crear_ejemplar, crear_titulo
from prestamos.models import PersonaPrestataria, Prestamo
from prestamos.services import historial_persona, registrar_devolucion, registrar_prestamo
from privacidad.services import anonimizar_persona, anonimizar_vencidas, personas_anonimizables

pytestmark = pytest.mark.django_db


def _persona_con_prestamo_antiguo(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="A-1", actor=central.user)
    hace_3_anios = datetime.date.today() - datetime.timedelta(days=365 * 3)
    registrar_prestamo(actor=central.user, codigo="A-1", documento="OLD", nombre="Vieja Cliente", hoy=hace_3_anios)
    registrar_devolucion(actor=central.user, codigo="A-1", hoy=hace_3_anios)
    return PersonaPrestataria.objects.get(documento="OLD")


def test_anonimiza_vencidas_borra_datos_pero_conserva_prestamos(biblioteca, central, parametros):
    persona = _persona_con_prestamo_antiguo(biblioteca, central)
    assert persona in personas_anonimizables()

    n = anonimizar_vencidas(actor=central.user)
    assert n == 1

    persona.refresh_from_db()
    assert persona.estado == PersonaPrestataria.Estado.ANONIMIZADA
    assert persona.documento == "" and persona.nombre == ""

    p = Prestamo.objects.get(persona__isnull=True)
    assert p.persona_anonimizada is True
    assert p.fecha_prestamo is not None  # el registro de préstamo se conserva
    assert not historial_persona("OLD").exists()  # ya no se puede consultar por documento


def test_no_anonimiza_con_prestamos_activos(biblioteca, central, parametros):
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    crear_ejemplar(titulo_obj=t, codigo="B-1", actor=central.user)
    registrar_prestamo(actor=central.user, codigo="B-1", documento="ACT", nombre="Activa")
    persona = PersonaPrestataria.objects.get(documento="ACT")
    with pytest.raises(ValidationError):
        anonimizar_persona(persona, actor=central.user)
