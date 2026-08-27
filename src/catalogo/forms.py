"""Formularios del catálogo."""

from __future__ import annotations

from django import forms

from .models import Ejemplar, Titulo


class TituloForm(forms.ModelForm):
    codigo_primer_ejemplar = forms.CharField(
        label="Código del primer ejemplar (opcional)", max_length=40, required=False
    )
    confirmar_isbn = forms.BooleanField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Titulo
        fields = ["titulo", "autor", "isbn", "editorial", "anio", "materia"]

    def clean_titulo(self):
        return self.cleaned_data["titulo"].strip()

    def clean_autor(self):
        return self.cleaned_data["autor"].strip()


class EjemplarForm(forms.ModelForm):
    class Meta:
        model = Ejemplar
        fields = ["codigo", "ubicacion"]


class MotivoForm(forms.Form):
    motivo = forms.CharField(label="Motivo", max_length=200, widget=forms.Textarea(attrs={"rows": 2}))

    def clean_motivo(self):
        return self.cleaned_data["motivo"].strip()
