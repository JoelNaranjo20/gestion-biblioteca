"""Formularios de préstamos."""

from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import GestionReclamacion


class PrestamoForm(forms.Form):
    codigo = forms.CharField(label="Código de ejemplar", max_length=40)
    documento = forms.CharField(label="Documento de la persona", max_length=40)
    nombre = forms.CharField(label="Nombre de la persona", max_length=200)
    contacto = forms.CharField(label="Contacto (opcional)", max_length=200, required=False)
    confirmar_nombre = forms.BooleanField(widget=forms.HiddenInput, required=False)


class DevolucionForm(forms.Form):
    codigo = forms.CharField(label="Código de ejemplar", max_length=40)


class MotivoForm(forms.Form):
    motivo = forms.CharField(label="Motivo", max_length=300, widget=forms.Textarea(attrs={"rows": 2}))

    def clean_motivo(self):
        return self.cleaned_data["motivo"].strip()


class CorregirEjemplarForm(MotivoForm):
    codigo_correcto = forms.CharField(label="Código del ejemplar correcto", max_length=40)


class ReclamacionForm(forms.ModelForm):
    class Meta:
        model = GestionReclamacion
        fields = ["fecha", "medio", "notas"]
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = timezone.localdate()
