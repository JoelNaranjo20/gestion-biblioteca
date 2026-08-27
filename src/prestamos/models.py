"""Modelos de préstamos: personas prestatarias, préstamos, correcciones y reclamaciones."""

from __future__ import annotations

import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from catalogo.models import Ejemplar
from common.models import ModeloBase
from cuentas.models import Biblioteca


class PersonaPrestataria(ModeloBase):
    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa"
        ANONIMIZADA = "anonimizada", "Anonimizada"

    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="prestatarios")
    documento = models.CharField("documento", max_length=40, blank=True)
    nombre = models.CharField("nombre", max_length=200, blank=True)
    contacto = models.CharField("contacto", max_length=200, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA)
    fecha_alta = models.DateField("fecha de alta", auto_now_add=True)
    fecha_ultimo_prestamo = models.DateField("fecha del último préstamo", null=True, blank=True)

    class Meta:
        verbose_name = "persona prestataria"
        verbose_name_plural = "personas prestatarias"
        constraints = [
            models.UniqueConstraint(
                fields=["biblioteca", "documento"],
                condition=Q(estado="activa"),
                name="persona_documento_unico_activa",
            )
        ]

    def __str__(self) -> str:
        if self.estado == self.Estado.ANONIMIZADA:
            return "(persona anonimizada)"
        return f"{self.nombre} ({self.documento})"

    @property
    def esta_activa(self) -> bool:
        return self.estado == self.Estado.ACTIVA


class Prestamo(ModeloBase):
    class EstadoRegistro(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        ANULADO = "anulado", "Anulado"

    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="prestamos")
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.PROTECT, related_name="prestamos")
    persona = models.ForeignKey(
        PersonaPrestataria, on_delete=models.SET_NULL, null=True, blank=True, related_name="prestamos"
    )
    persona_anonimizada = models.BooleanField(default=False)
    fecha_prestamo = models.DateField("fecha de préstamo")
    fecha_limite = models.DateField("fecha límite de devolución")
    fecha_devolucion_real = models.DateField("fecha real de devolución", null=True, blank=True)
    dias_retraso = models.PositiveIntegerField("días de retraso", default=0)
    estado_registro = models.CharField(max_length=10, choices=EstadoRegistro.choices, default=EstadoRegistro.EFECTIVO)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prestamos_registrados"
    )
    devolucion_registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="devoluciones_registradas",
    )

    class Meta:
        verbose_name = "préstamo"
        verbose_name_plural = "préstamos"
        ordering = ["-fecha_prestamo", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["ejemplar"],
                condition=Q(estado_registro="efectivo", fecha_devolucion_real__isnull=True),
                name="un_prestamo_activo_por_ejemplar",
            )
        ]
        indexes = [
            models.Index(fields=["ejemplar", "-fecha_prestamo"]),
            models.Index(fields=["persona"]),
            models.Index(
                fields=["fecha_limite"],
                name="prestamo_vencidos_idx",
                condition=Q(estado_registro="efectivo", fecha_devolucion_real__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ejemplar.codigo} → {self.persona or '—'} ({self.fecha_prestamo})"

    @property
    def activo(self) -> bool:
        return self.estado_registro == self.EstadoRegistro.EFECTIVO and self.fecha_devolucion_real is None

    def dias_retraso_a(self, fecha: datetime.date | None = None) -> int:
        fecha = fecha or timezone.localdate()
        ref = self.fecha_devolucion_real or fecha
        return max(0, (ref - self.fecha_limite).days)

    @property
    def esta_vencido(self) -> bool:
        return self.activo and timezone.localdate() > self.fecha_limite

    @property
    def etiqueta_estado(self) -> str:
        if self.estado_registro == self.EstadoRegistro.ANULADO:
            return "Anulado"
        if self.activo:
            return "Vencido" if self.esta_vencido else "Activo"
        return "Devuelto con retraso" if self.dias_retraso > 0 else "Devuelto"


class CorreccionOperacion(ModeloBase):
    class Tipo(models.TextChoices):
        ANULACION = "anulacion", "Anulación"
        CORRECCION = "correccion", "Corrección"

    class Operacion(models.TextChoices):
        PRESTAMO = "prestamo", "Préstamo"
        DEVOLUCION = "devolucion", "Devolución"
        RETIRADA = "retirada", "Retirada"

    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="correcciones")
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    operacion = models.CharField(max_length=12, choices=Operacion.choices)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.PROTECT, null=True, blank=True, related_name="correcciones")
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.PROTECT, null=True, blank=True, related_name="correcciones")
    motivo = models.CharField(max_length=300)
    realizada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="correcciones")
    fecha_hora = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "corrección de operación"
        verbose_name_plural = "correcciones de operación"
        ordering = ["-fecha_hora", "-id"]


class GestionReclamacion(ModeloBase):
    class Medio(models.TextChoices):
        TELEFONO = "telefono", "Teléfono"
        CORREO = "correo", "Correo electrónico"
        PRESENCIAL = "presencial", "Presencial"
        OTRO = "otro", "Otro"

    prestamo = models.ForeignKey(Prestamo, on_delete=models.PROTECT, related_name="reclamaciones")
    fecha = models.DateField()
    medio = models.CharField(max_length=12, choices=Medio.choices)
    notas = models.CharField(max_length=500, blank=True)
    registrada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reclamaciones")

    class Meta:
        verbose_name = "gestión de reclamación"
        verbose_name_plural = "gestiones de reclamación"
        ordering = ["-fecha", "-id"]

    def __str__(self) -> str:
        return f"{self.fecha} · {self.get_medio_display()}"
