"""Formularios de cuentas."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

UserModel = get_user_model()


class _ConPasswordConfirmada(forms.Form):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput)

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get("password"), datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return datos


class AltaBibliotecaForm(_ConPasswordConfirmada):
    nombre_biblioteca = forms.CharField(label="Nombre de la biblioteca", max_length=200)
    email = forms.EmailField(label="Correo de la cuenta central")
    contacto = forms.CharField(label="Datos de contacto (opcional)", max_length=200, required=False)

    field_order = ["nombre_biblioteca", "email", "contacto", "password", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if UserModel.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email


class OperadorForm(_ConPasswordConfirmada):
    username = forms.CharField(label="Nombre de usuario", max_length=150)
    nombre_visible = forms.CharField(label="Nombre visible (opcional)", max_length=120, required=False)

    field_order = ["username", "nombre_visible", "password", "password2"]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise forms.ValidationError("El nombre de usuario es obligatorio.")
        if UserModel.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(f"Ya existe una subcuenta con el nombre «{username}».")
        return username


class RestablecerPasswordForm(_ConPasswordConfirmada):
    pass
