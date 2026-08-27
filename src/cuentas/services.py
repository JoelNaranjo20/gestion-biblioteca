"""Servicios de cuentas: auditoría y alta de biblioteca / operadores."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Biblioteca, EntradaAuditoria, Operador

UserModel = get_user_model()


def registrar_auditoria(
    *,
    actor: User | None,
    tipo: str,
    entidad: str,
    entidad_id: int | None = None,
    detalle: dict | None = None,
    biblioteca: Biblioteca | None = None,
) -> EntradaAuditoria:
    """Inserta una entrada de auditoría (append-only). No lanza si `biblioteca` es None y existe una."""
    bib = biblioteca or Biblioteca.actual()
    if bib is None:  # pragma: no cover - no debería ocurrir tras el alta
        raise ValidationError("No hay biblioteca dada de alta.")
    return EntradaAuditoria.objects.create(
        biblioteca=bib,
        actor=actor if (actor and actor.is_authenticated) else None,
        tipo_operacion=tipo,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle or {},
    )


@transaction.atomic
def alta_biblioteca(*, nombre: str, email: str, password: str, contacto: str = "") -> Operador:
    """Crea la biblioteca (cuenta central) y su usuario. Falla si ya existe una biblioteca."""
    if Biblioteca.objects.exists():
        raise ValidationError("La biblioteca ya está dada de alta.")
    biblioteca = Biblioteca.objects.create(nombre=nombre, contacto=contacto, creada_por_email=email)
    user = UserModel.objects.create_user(
        username=email, email=email, password=password, is_staff=True, is_superuser=True
    )
    operador = Operador.objects.create(
        user=user, biblioteca=biblioteca, es_central=True, nombre_visible="Cuenta central"
    )
    registrar_auditoria(
        actor=user,
        tipo="alta_biblioteca",
        entidad=EntradaAuditoria.Entidad.OPERADOR,
        entidad_id=operador.id,
        biblioteca=biblioteca,
    )
    return operador


@transaction.atomic
def crear_operador(
    *,
    biblioteca: Biblioteca,
    username: str,
    password: str,
    nombre_visible: str = "",
    actor: User | None = None,
) -> Operador:
    """Crea una subcuenta de operador (sin correo). `username` único en la biblioteca."""
    username = username.strip()
    if not username:
        raise ValidationError("El nombre de usuario es obligatorio.")
    if UserModel.objects.filter(username__iexact=username).exists():
        raise ValidationError(f"Ya existe una subcuenta con el nombre de usuario «{username}».")
    user = UserModel.objects.create_user(username=username, email="", password=password)
    operador = Operador.objects.create(
        user=user,
        biblioteca=biblioteca,
        es_central=False,
        nombre_visible=nombre_visible or username,
    )
    registrar_auditoria(
        actor=actor,
        tipo="alta_operador",
        entidad=EntradaAuditoria.Entidad.OPERADOR,
        entidad_id=operador.id,
        detalle={"username": username},
        biblioteca=biblioteca,
    )
    return operador


@transaction.atomic
def fijar_estado_operador(*, operador: Operador, activo: bool, actor: User | None = None) -> Operador:
    """Activa o desactiva una subcuenta. No se borra: se conserva la atribución histórica."""
    operador.user.is_active = activo
    operador.user.save(update_fields=["is_active"])
    registrar_auditoria(
        actor=actor,
        tipo="alta_operador" if activo else "baja_operador",
        entidad=EntradaAuditoria.Entidad.OPERADOR,
        entidad_id=operador.id,
        detalle={"username": operador.username, "activo": activo},
        biblioteca=operador.biblioteca,
    )
    return operador


@transaction.atomic
def restablecer_password(*, operador: Operador, password: str, actor: User | None = None) -> None:
    operador.user.set_password(password)
    operador.user.save(update_fields=["password"])
    registrar_auditoria(
        actor=actor,
        tipo="alta_operador",
        entidad=EntradaAuditoria.Entidad.OPERADOR,
        entidad_id=operador.id,
        detalle={"accion": "restablecer_password"},
        biblioteca=operador.biblioteca,
    )
