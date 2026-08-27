"""Servicios de catálogo: alta/edición de títulos y ejemplares, retirada y búsqueda."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q

from common.utils import normalizar_isbn, normalizar_texto
from cuentas.models import Biblioteca, EntradaAuditoria
from cuentas.services import registrar_auditoria

from .models import Ejemplar, Titulo


class IsbnDuplicado(ValidationError):
    """El ISBN ya existe en el catálogo; el personal debe confirmar que es otro título."""


def _aud(actor, tipo, entidad, entidad_id, detalle=None):
    registrar_auditoria(actor=actor, tipo=tipo, entidad=entidad, entidad_id=entidad_id, detalle=detalle)


@transaction.atomic
def crear_titulo(
    *,
    biblioteca: Biblioteca,
    titulo: str,
    autor: str,
    isbn: str = "",
    editorial: str = "",
    anio: int | None = None,
    materia: str = "",
    actor: User | None = None,
    confirmar_isbn: bool = False,
) -> Titulo:
    if not titulo.strip() or not autor.strip():
        raise ValidationError("El título y el autor son obligatorios.")
    isbn_norm = normalizar_isbn(isbn)
    if isbn_norm and not confirmar_isbn and Titulo.objects.filter(isbn_norm=isbn_norm).exists():
        raise IsbnDuplicado(f"Ya hay un título con el ISBN {isbn}. Confirma si es un título distinto.")
    obj = Titulo.objects.create(
        biblioteca=biblioteca,
        titulo=titulo.strip(),
        autor=autor.strip(),
        isbn=isbn.strip(),
        editorial=editorial.strip(),
        anio=anio,
        materia=materia.strip(),
    )
    _aud(actor, "alta_titulo", EntradaAuditoria.Entidad.TITULO, obj.id, {"titulo": obj.titulo})
    return obj


@transaction.atomic
def editar_titulo(*, titulo_obj: Titulo, actor: User | None = None, **campos) -> Titulo:
    permitidos = {"titulo", "autor", "isbn", "editorial", "anio", "materia"}
    for k, v in campos.items():
        if k in permitidos:
            setattr(titulo_obj, k, v)
    if not str(titulo_obj.titulo).strip() or not str(titulo_obj.autor).strip():
        raise ValidationError("El título y el autor son obligatorios.")
    titulo_obj.save()
    _aud(actor, "edicion_titulo", EntradaAuditoria.Entidad.TITULO, titulo_obj.id)
    return titulo_obj


@transaction.atomic
def crear_ejemplar(*, titulo_obj: Titulo, codigo: str, ubicacion: str = "", actor: User | None = None) -> Ejemplar:
    codigo = codigo.strip()
    if not codigo:
        raise ValidationError("El código de ejemplar es obligatorio.")
    try:
        with transaction.atomic():
            ej = Ejemplar.objects.create(titulo=titulo_obj, codigo=codigo, ubicacion=ubicacion.strip())
    except IntegrityError as exc:
        raise ValidationError(f"Ya existe un ejemplar con el código «{codigo}».") from exc
    _aud(actor, "alta_ejemplar", EntradaAuditoria.Entidad.EJEMPLAR, ej.id, {"codigo": ej.codigo})
    return ej


@transaction.atomic
def retirar_ejemplar(*, ejemplar: Ejemplar, motivo: str, actor: User | None = None) -> Ejemplar:
    if not motivo.strip():
        raise ValidationError("Indica el motivo de la retirada.")
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)
    if ejemplar.esta_prestado:
        raise ValidationError("No se puede retirar un ejemplar prestado; regístrese antes la devolución.")
    if ejemplar.esta_retirado:
        raise ValidationError("El ejemplar ya está retirado.")
    ejemplar.estado = Ejemplar.Estado.RETIRADO
    ejemplar.motivo_retirada = motivo.strip()
    ejemplar.save(update_fields=["estado", "motivo_retirada", "actualizado_en"])
    _aud(actor, "retirada_ejemplar", EntradaAuditoria.Entidad.EJEMPLAR, ejemplar.id, {"motivo": motivo})
    return ejemplar


@transaction.atomic
def anular_retirada(*, ejemplar: Ejemplar, motivo: str, actor: User | None = None) -> Ejemplar:
    if not motivo.strip():
        raise ValidationError("Indica el motivo de la corrección.")
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)
    if not ejemplar.esta_retirado:
        raise ValidationError("El ejemplar no está retirado.")
    ejemplar.estado = Ejemplar.Estado.DISPONIBLE
    ejemplar.motivo_retirada = ""
    ejemplar.save(update_fields=["estado", "motivo_retirada", "actualizado_en"])
    _aud(
        actor,
        "correccion",
        EntradaAuditoria.Entidad.EJEMPLAR,
        ejemplar.id,
        {"accion": "anular_retirada", "motivo": motivo},
    )
    return ejemplar


def titulos_con_recuento():
    """Queryset de títulos anotado con nº total y disponible de ejemplares."""
    return Titulo.objects.annotate(
        n_total=Count("ejemplares"),
        n_disponibles=Count("ejemplares", filter=Q(ejemplares__estado=Ejemplar.Estado.DISPONIBLE)),
    )


def buscar_titulos(*, texto: str = "", campo: str = "titulo"):
    """Búsqueda insensible a mayúsculas y acentos. `campo`: titulo|autor|isbn|materia."""
    qs = titulos_con_recuento()
    texto = (texto or "").strip()
    if not texto:
        return qs.none()
    if campo == "isbn":
        return qs.filter(isbn_norm=normalizar_isbn(texto))
    termino = normalizar_texto(texto)
    if campo == "autor":
        return qs.filter(busqueda_norm__contains=termino)
    if campo == "materia":
        return qs.filter(materia__icontains=texto)
    # por defecto: título (usa la columna normalizada, que incluye título + autor + materia)
    return qs.filter(busqueda_norm__contains=termino)
