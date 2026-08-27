"""Servicios de préstamos: circulación, correcciones, consultas y reclamación."""

from __future__ import annotations

import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from catalogo.models import Ejemplar
from configuracion.models import get_parametros
from cuentas.models import Biblioteca, EntradaAuditoria
from cuentas.services import registrar_auditoria

from .models import CorreccionOperacion, GestionReclamacion, PersonaPrestataria, Prestamo
from .rules import calcular_dias_retraso, calcular_fecha_limite, valida_tope


class EjemplarNoDisponible(ValidationError):
    pass


class TopeAlcanzado(ValidationError):
    pass


class NombreDistinto(ValidationError):
    """El documento ya existe con otro nombre; hay que confirmar o corregir."""


def _aud(actor, tipo, entidad, entidad_id, detalle=None):
    registrar_auditoria(actor=actor, tipo=tipo, entidad=entidad, entidad_id=entidad_id, detalle=detalle or {})


def _resolver_ejemplar(ejemplar=None, codigo=None) -> Ejemplar:
    if ejemplar is not None:
        return ejemplar
    try:
        return Ejemplar.objects.get(codigo=(codigo or "").strip())
    except Ejemplar.DoesNotExist as exc:
        raise ValidationError("No se ha encontrado ningún ejemplar con ese código.") from exc


def _prestamos_activos_de(persona: PersonaPrestataria) -> int:
    return Prestamo.objects.filter(
        persona=persona,
        estado_registro=Prestamo.EstadoRegistro.EFECTIVO,
        fecha_devolucion_real__isnull=True,
    ).count()


@transaction.atomic
def _get_or_create_persona(
    *, biblioteca: Biblioteca, documento: str, nombre: str, contacto: str, confirmar_nombre: bool
) -> PersonaPrestataria:
    documento = documento.strip()
    nombre = nombre.strip()
    if not documento or not nombre:
        raise ValidationError("El documento y el nombre de la persona son obligatorios.")
    persona = PersonaPrestataria.objects.filter(
        biblioteca=biblioteca, documento=documento, estado=PersonaPrestataria.Estado.ACTIVA
    ).first()
    if persona is None:
        return PersonaPrestataria.objects.create(
            biblioteca=biblioteca, documento=documento, nombre=nombre, contacto=contacto.strip()
        )
    if persona.nombre.strip().lower() != nombre.lower() and not confirmar_nombre:
        raise NombreDistinto(
            f"El documento {documento} ya consta a nombre de «{persona.nombre}». "
            "Confirma para continuar o corrige el nombre."
        )
    if confirmar_nombre and persona.nombre != nombre:
        persona.nombre = nombre
    if contacto.strip():
        persona.contacto = contacto.strip()
    persona.save()
    return persona


@transaction.atomic
def registrar_prestamo(
    *,
    actor: User,
    documento: str,
    nombre: str,
    contacto: str = "",
    ejemplar: Ejemplar | None = None,
    codigo: str | None = None,
    confirmar_nombre: bool = False,
    hoy: datetime.date | None = None,
) -> Prestamo:
    biblioteca = Biblioteca.actual()
    hoy = hoy or timezone.localdate()
    ej = _resolver_ejemplar(ejemplar, codigo)
    ej = Ejemplar.objects.select_for_update().get(pk=ej.pk)

    if ej.estado != Ejemplar.Estado.DISPONIBLE:
        if ej.estado == Ejemplar.Estado.RETIRADO:
            raise EjemplarNoDisponible("El ejemplar está dado de baja (retirado).")
        activo = (
            Prestamo.objects.filter(
                ejemplar=ej,
                estado_registro=Prestamo.EstadoRegistro.EFECTIVO,
                fecha_devolucion_real__isnull=True,
            )
            .select_related("persona")
            .first()
        )
        tenedor = activo.persona.nombre if activo and activo.persona else "otra persona"
        desde = activo.fecha_prestamo if activo else "?"
        raise EjemplarNoDisponible(f"El ejemplar no está disponible: lo tiene {tenedor} desde {desde}.")

    persona = _get_or_create_persona(
        biblioteca=biblioteca,
        documento=documento,
        nombre=nombre,
        contacto=contacto,
        confirmar_nombre=confirmar_nombre,
    )

    params = get_parametros(biblioteca)
    if not valida_tope(_prestamos_activos_de(persona), params.max_prestamos_persona):
        raise TopeAlcanzado(
            f"La persona ya tiene {params.max_prestamos_persona} préstamos activos "
            f"(máximo permitido: {params.max_prestamos_persona})."
        )

    prestamo = Prestamo.objects.create(
        biblioteca=biblioteca,
        ejemplar=ej,
        persona=persona,
        fecha_prestamo=hoy,
        fecha_limite=calcular_fecha_limite(hoy, params.plazo_dias),
        registrado_por=actor,
    )
    ej.estado = Ejemplar.Estado.PRESTADO
    ej.save(update_fields=["estado", "actualizado_en"])
    persona.fecha_ultimo_prestamo = hoy
    persona.save(update_fields=["fecha_ultimo_prestamo", "actualizado_en"])
    _aud(
        actor,
        "prestamo",
        EntradaAuditoria.Entidad.PRESTAMO,
        prestamo.id,
        {"ejemplar": ej.codigo, "documento": persona.documento},
    )
    return prestamo


@transaction.atomic
def registrar_devolucion(
    *,
    actor: User,
    prestamo: Prestamo | None = None,
    codigo: str | None = None,
    hoy: datetime.date | None = None,
) -> Prestamo:
    hoy = hoy or timezone.localdate()
    if prestamo is None:
        ej = _resolver_ejemplar(codigo=codigo)
        prestamo = (
            Prestamo.objects.filter(
                ejemplar=ej,
                estado_registro=Prestamo.EstadoRegistro.EFECTIVO,
                fecha_devolucion_real__isnull=True,
            )
            .select_for_update()
            .first()
        )
        if prestamo is None:
            raise ValidationError("Ese ejemplar no tiene ningún préstamo activo.")
    else:
        prestamo = Prestamo.objects.select_for_update().get(pk=prestamo.pk)
        if not prestamo.activo:
            raise ValidationError("El préstamo no está activo.")

    prestamo.fecha_devolucion_real = hoy
    prestamo.dias_retraso = calcular_dias_retraso(prestamo.fecha_limite, hoy)
    prestamo.devolucion_registrada_por = actor
    prestamo.save(
        update_fields=["fecha_devolucion_real", "dias_retraso", "devolucion_registrada_por", "actualizado_en"]
    )
    ej = Ejemplar.objects.select_for_update().get(pk=prestamo.ejemplar_id)
    ej.estado = Ejemplar.Estado.DISPONIBLE
    ej.save(update_fields=["estado", "actualizado_en"])
    _aud(actor, "devolucion", EntradaAuditoria.Entidad.PRESTAMO, prestamo.id, {"dias_retraso": prestamo.dias_retraso})
    return prestamo


@transaction.atomic
def anular_prestamo(*, actor: User, prestamo: Prestamo, motivo: str) -> Prestamo:
    if not motivo.strip():
        raise ValidationError("Indica el motivo de la anulación.")
    if prestamo.estado_registro == Prestamo.EstadoRegistro.ANULADO:
        raise ValidationError("El préstamo ya está anulado.")
    prestamo = Prestamo.objects.select_for_update().get(pk=prestamo.pk)
    prestamo.estado_registro = Prestamo.EstadoRegistro.ANULADO
    prestamo.save(update_fields=["estado_registro", "actualizado_en"])
    if prestamo.fecha_devolucion_real is None:
        ej = Ejemplar.objects.select_for_update().get(pk=prestamo.ejemplar_id)
        ej.estado = Ejemplar.Estado.DISPONIBLE
        ej.save(update_fields=["estado", "actualizado_en"])
    _registrar_correccion(
        actor=actor,
        tipo=CorreccionOperacion.Tipo.ANULACION,
        operacion=CorreccionOperacion.Operacion.PRESTAMO,
        prestamo=prestamo,
        motivo=motivo,
    )
    return prestamo


@transaction.atomic
def anular_devolucion(*, actor: User, prestamo: Prestamo, motivo: str) -> Prestamo:
    if not motivo.strip():
        raise ValidationError("Indica el motivo de la anulación.")
    prestamo = Prestamo.objects.select_for_update().get(pk=prestamo.pk)
    if prestamo.fecha_devolucion_real is None:
        raise ValidationError("El préstamo no consta como devuelto.")
    prestamo.fecha_devolucion_real = None
    prestamo.dias_retraso = 0
    prestamo.devolucion_registrada_por = None
    prestamo.save(
        update_fields=["fecha_devolucion_real", "dias_retraso", "devolucion_registrada_por", "actualizado_en"]
    )
    ej = Ejemplar.objects.select_for_update().get(pk=prestamo.ejemplar_id)
    ej.estado = Ejemplar.Estado.PRESTADO
    ej.save(update_fields=["estado", "actualizado_en"])
    _registrar_correccion(
        actor=actor,
        tipo=CorreccionOperacion.Tipo.ANULACION,
        operacion=CorreccionOperacion.Operacion.DEVOLUCION,
        prestamo=prestamo,
        motivo=motivo,
    )
    return prestamo


@transaction.atomic
def corregir_ejemplar(
    *,
    actor: User,
    prestamo: Prestamo,
    motivo: str,
    ejemplar_correcto: Ejemplar | None = None,
    codigo_correcto: str | None = None,
) -> Prestamo:
    if not motivo.strip():
        raise ValidationError("Indica el motivo de la corrección.")
    if not prestamo.activo:
        raise ValidationError("Solo se puede corregir el ejemplar de un préstamo activo.")
    correcto = _resolver_ejemplar(ejemplar_correcto, codigo_correcto)
    persona = prestamo.persona
    anular_prestamo(actor=actor, prestamo=prestamo, motivo=f"Corrección de ejemplar: {motivo}")
    nuevo = registrar_prestamo(
        actor=actor,
        documento=persona.documento,
        nombre=persona.nombre,
        contacto=persona.contacto,
        ejemplar=correcto,
        confirmar_nombre=True,
    )
    _registrar_correccion(
        actor=actor,
        tipo=CorreccionOperacion.Tipo.CORRECCION,
        operacion=CorreccionOperacion.Operacion.PRESTAMO,
        prestamo=nuevo,
        motivo=motivo,
    )
    return nuevo


def _registrar_correccion(*, actor, tipo, operacion, motivo, prestamo=None, ejemplar=None):
    CorreccionOperacion.objects.create(
        biblioteca=Biblioteca.actual(),
        tipo=tipo,
        operacion=operacion,
        prestamo=prestamo,
        ejemplar=ejemplar,
        motivo=motivo.strip(),
        realizada_por=actor,
    )
    _aud(
        actor,
        "correccion",
        EntradaAuditoria.Entidad.PRESTAMO,
        prestamo.id if prestamo else (ejemplar.id if ejemplar else None),
        {"tipo": tipo, "operacion": operacion, "motivo": motivo},
    )


# --- Consultas -------------------------------------------------------------


def _con_ultima_reclamacion(qs):
    return qs.prefetch_related(Prefetch("reclamaciones", queryset=GestionReclamacion.objects.order_by("-fecha", "-id")))


def prestamos_activos():
    qs = (
        Prestamo.objects.filter(estado_registro=Prestamo.EstadoRegistro.EFECTIVO, fecha_devolucion_real__isnull=True)
        .select_related("ejemplar__titulo", "persona")
        .order_by("fecha_limite")
    )
    return _con_ultima_reclamacion(qs)


def prestamos_vencidos():
    hoy = timezone.localdate()
    return prestamos_activos().filter(fecha_limite__lt=hoy)


def historial_ejemplar(ejemplar: Ejemplar):
    return Prestamo.objects.filter(ejemplar=ejemplar).select_related("persona").order_by("-fecha_prestamo", "-id")


def historial_persona(documento: str):
    documento = (documento or "").strip()
    if not documento:
        return Prestamo.objects.none()
    return (
        Prestamo.objects.filter(persona__documento=documento, persona__estado=PersonaPrestataria.Estado.ACTIVA)
        .select_related("ejemplar__titulo")
        .order_by("-fecha_prestamo", "-id")
    )


@transaction.atomic
def registrar_reclamacion(
    *, actor: User, prestamo: Prestamo, fecha: datetime.date, medio: str, notas: str = ""
) -> GestionReclamacion:
    prestamo = Prestamo.objects.get(pk=prestamo.pk)
    if not prestamo.activo:
        raise ValidationError("No se pueden añadir gestiones a un préstamo cerrado o anulado.")
    if not prestamo.esta_vencido:
        raise ValidationError("El préstamo todavía no está vencido.")
    gestion = GestionReclamacion.objects.create(
        prestamo=prestamo, fecha=fecha, medio=medio, notas=notas.strip(), registrada_por=actor
    )
    _aud(actor, "reclamacion", EntradaAuditoria.Entidad.PRESTAMO, prestamo.id, {"medio": medio})
    return gestion
