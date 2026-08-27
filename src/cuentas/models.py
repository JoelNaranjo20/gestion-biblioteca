"""Modelos de cuentas: biblioteca (cuenta central), operadores y auditoría."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import ModeloBase


class Biblioteca(ModeloBase):
    """Organización usuaria del sistema. En v1 hay una sola fila."""

    nombre = models.CharField("nombre", max_length=200)
    contacto = models.CharField("datos de contacto", max_length=200, blank=True)
    creada_por_email = models.EmailField("correo de alta", blank=True)

    class Meta:
        verbose_name = "biblioteca"
        verbose_name_plural = "bibliotecas"

    def __str__(self) -> str:
        return self.nombre

    @classmethod
    def actual(cls) -> Biblioteca | None:
        return cls.objects.order_by("id").first()


class Operador(ModeloBase):
    """Subcuenta de una persona del personal. Perfil sobre auth.User.

    - La cuenta central tiene `es_central=True` y correo en el User.
    - Los operadores tienen `username` y contraseña, sin correo.
    - `user.is_active` = activa/desactivada (FR-030f): desactivada no inicia sesión pero
      se conserva para no perder la atribución histórica.
    """

    TIPO_CENTRAL = "central"
    TIPO_OPERADOR = "operador"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="operador")
    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="operadores")
    es_central = models.BooleanField("es cuenta central", default=False)
    nombre_visible = models.CharField("nombre visible", max_length=120, blank=True)

    class Meta:
        verbose_name = "operador"
        verbose_name_plural = "operadores"
        ordering = ["-es_central", "user__username"]

    def __str__(self) -> str:
        return self.etiqueta

    def save(self, *args, **kwargs):
        if not self.nombre_visible:
            self.nombre_visible = self.user.get_username()
        super().save(*args, **kwargs)

    @property
    def username(self) -> str:
        return self.user.get_username()

    @property
    def esta_activa(self) -> bool:
        return self.user.is_active

    @property
    def etiqueta(self) -> str:
        return self.nombre_visible or self.user.get_username()

    @property
    def puede_gestionar(self) -> bool:
        """Solo la cuenta central gestiona subcuentas y configuración (FR-030e)."""
        return self.es_central or self.user.is_superuser


class EntradaAuditoria(ModeloBase):
    """Registro append-only de cada operación que crea o modifica datos (FR-030d, FR-031)."""

    class Entidad(models.TextChoices):
        EJEMPLAR = "ejemplar", "Ejemplar"
        TITULO = "titulo", "Título"
        PRESTAMO = "prestamo", "Préstamo"
        PERSONA = "persona", "Persona prestataria"
        CONFIGURACION = "configuracion", "Configuración"
        OPERADOR = "operador", "Operador"

    biblioteca = models.ForeignKey(Biblioteca, on_delete=models.PROTECT, related_name="auditoria")
    tipo_operacion = models.CharField("tipo de operación", max_length=60)
    entidad = models.CharField("entidad", max_length=20, choices=Entidad.choices)
    entidad_id = models.BigIntegerField("id de la entidad", null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="auditoria",
        help_text="Subcuenta autora; NULL solo para el proceso automático de anonimización.",
    )
    fecha_hora = models.DateTimeField("fecha y hora", default=timezone.now)
    detalle = models.JSONField("detalle", default=dict, blank=True)

    class Meta:
        verbose_name = "entrada de auditoría"
        verbose_name_plural = "auditoría"
        ordering = ["-fecha_hora", "-id"]
        indexes = [
            models.Index(fields=["entidad", "entidad_id"]),
            models.Index(fields=["-fecha_hora"]),
        ]

    def __str__(self) -> str:
        return f"{self.fecha_hora:%Y-%m-%d %H:%M} · {self.tipo_operacion}"
