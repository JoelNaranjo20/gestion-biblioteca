"""Anonimización de prestatarios (RGPD/LOPD): FR-034…FR-037."""

from __future__ import annotations

import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from cuentas.models import EntradaAuditoria
from cuentas.services import registrar_auditoria
from prestamos.models import PersonaPrestataria, Prestamo


def _fecha_corte(hoy: datetime.date | None = None) -> datetime.date:
    hoy = hoy or timezone.localdate()
    return hoy - datetime.timedelta(days=int(settings.RETENCION_PRESTATARIOS_DIAS))


def _tiene_prestamos_activos(persona: PersonaPrestataria) -> bool:
    return Prestamo.objects.filter(
        persona=persona,
        estado_registro=Prestamo.EstadoRegistro.EFECTIVO,
        fecha_devolucion_real__isnull=True,
    ).exists()


def personas_anonimizables(hoy: datetime.date | None = None):
    """Personas activas, sin préstamos activos, con actividad anterior a la ventana de retención."""
    corte = _fecha_corte(hoy)
    base = PersonaPrestataria.objects.filter(estado=PersonaPrestataria.Estado.ACTIVA).filter(
        Q(fecha_ultimo_prestamo__lte=corte) | Q(fecha_ultimo_prestamo__isnull=True, fecha_alta__lte=corte)
    )
    # excluye las que tengan algún préstamo activo
    con_activos = Prestamo.objects.filter(
        estado_registro=Prestamo.EstadoRegistro.EFECTIVO, fecha_devolucion_real__isnull=True
    ).values_list("persona_id", flat=True)
    return base.exclude(id__in=con_activos)


@transaction.atomic
def anonimizar_persona(
    persona: PersonaPrestataria, *, actor: User | None = None, motivo: str = "", automatica: bool = False
) -> PersonaPrestataria:
    persona = PersonaPrestataria.objects.select_for_update().get(pk=persona.pk)
    if persona.estado == PersonaPrestataria.Estado.ANONIMIZADA:
        return persona
    if _tiene_prestamos_activos(persona):
        raise ValidationError("No se puede anonimizar: la persona tiene préstamos activos.")

    Prestamo.objects.filter(persona=persona).update(persona=None, persona_anonimizada=True)
    persona.documento = ""
    persona.nombre = ""
    persona.contacto = ""
    persona.estado = PersonaPrestataria.Estado.ANONIMIZADA
    persona.save(update_fields=["documento", "nombre", "contacto", "estado", "actualizado_en"])

    registrar_auditoria(
        actor=actor,
        tipo="anonimizacion_automatica" if automatica else "anonimizacion_manual",
        entidad=EntradaAuditoria.Entidad.PERSONA,
        entidad_id=persona.id,
        detalle={"motivo": motivo} if motivo else {},
    )
    return persona


def anonimizar_vencidas(*, actor: User | None = None, hoy: datetime.date | None = None) -> int:
    n = 0
    for persona in list(personas_anonimizables(hoy)):
        anonimizar_persona(persona, actor=actor, automatica=True)
        n += 1
    return n
