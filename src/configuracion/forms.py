from django import forms

from .models import ParametrosPrestamo


class ParametrosForm(forms.ModelForm):
    class Meta:
        model = ParametrosPrestamo
        fields = ["plazo_dias", "max_prestamos_persona"]

    def clean_plazo_dias(self):
        v = self.cleaned_data["plazo_dias"]
        if v < 1:
            raise forms.ValidationError("El plazo mínimo es 1 día.")
        return v

    def clean_max_prestamos_persona(self):
        v = self.cleaned_data["max_prestamos_persona"]
        if v < 1:
            raise forms.ValidationError("El máximo mínimo es 1.")
        return v
