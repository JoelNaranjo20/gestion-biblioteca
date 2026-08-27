"""US2 — un solo préstamo activo por ejemplar bajo concurrencia (T037).

Se comprueba la invariante a nivel de base de datos: el índice único parcial
`un_prestamo_activo_por_ejemplar` impide dos préstamos activos del mismo ejemplar,
aunque la comprobación de aplicación fallara.
"""

import datetime

import pytest
from django.db import IntegrityError, transaction

from catalogo.services import crear_ejemplar, crear_titulo
from prestamos.models import PersonaPrestataria, Prestamo

pytestmark = pytest.mark.django_db(transaction=True)


def test_indice_unico_parcial_impide_dos_prestamos_activos(biblioteca, central):
    t = crear_titulo(biblioteca=biblioteca, titulo="T", autor="A", actor=central.user)
    ej = crear_ejemplar(titulo_obj=t, codigo="X-1", actor=central.user)
    p1 = PersonaPrestataria.objects.create(biblioteca=biblioteca, documento="1", nombre="A")
    p2 = PersonaPrestataria.objects.create(biblioteca=biblioteca, documento="2", nombre="B")
    hoy = datetime.date(2026, 8, 27)

    Prestamo.objects.create(
        biblioteca=biblioteca,
        ejemplar=ej,
        persona=p1,
        fecha_prestamo=hoy,
        fecha_limite=hoy,
        registrado_por=central.user,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Prestamo.objects.create(
            biblioteca=biblioteca,
            ejemplar=ej,
            persona=p2,
            fecha_prestamo=hoy,
            fecha_limite=hoy,
            registrado_por=central.user,
        )

    activos = Prestamo.objects.filter(
        ejemplar=ej,
        estado_registro=Prestamo.EstadoRegistro.EFECTIVO,
        fecha_devolucion_real__isnull=True,
    ).count()
    assert activos == 1
