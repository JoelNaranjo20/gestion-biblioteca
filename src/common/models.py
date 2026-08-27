from django.db import models


class ModeloBase(models.Model):
    """Campos comunes a todas las entidades: marcas de tiempo de creación y actualización."""

    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        abstract = True
