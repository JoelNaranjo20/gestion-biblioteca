"""Vistas de cuentas: alta de biblioteca, acceso, gestión de operadores y auditoría."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView

from .forms import (
    AltaBibliotecaForm,
    OperadorForm,
    RenombrarOperadorForm,
    RestablecerPasswordForm,
)
from .models import Biblioteca, EntradaAuditoria, Operador
from .permissions import SoloCentralMixin, es_central
from .services import (
    alta_biblioteca,
    crear_operador,
    fijar_estado_operador,
    renombrar_operador,
    restablecer_password,
)


def alta_biblioteca_view(request):
    """Alta inicial: crea la cuenta central. Solo accesible si no hay biblioteca."""
    if Biblioteca.objects.exists():
        return redirect("cuentas:entrar")
    if request.method == "POST":
        form = AltaBibliotecaForm(request.POST)
        if form.is_valid():
            operador = alta_biblioteca(
                nombre=form.cleaned_data["nombre_biblioteca"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                contacto=form.cleaned_data["contacto"],
            )
            login(request, operador.user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Biblioteca dada de alta. Ya puedes crear operadores.")
            return redirect("inicio")
    else:
        form = AltaBibliotecaForm()
    return render(request, "cuentas/alta_biblioteca.html", {"form": form})


class EntrarView(LoginView):
    template_name = "cuentas/entrar.html"
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if not Biblioteca.objects.exists():
            return redirect("cuentas:alta_biblioteca")
        return super().dispatch(request, *args, **kwargs)


class SalirView(LogoutView):
    next_page = reverse_lazy("cuentas:entrar")


class OperadorListView(SoloCentralMixin, ListView):
    model = Operador
    template_name = "cuentas/operador_lista.html"
    context_object_name = "operadores"

    def get_queryset(self):
        return Operador.objects.select_related("user", "biblioteca")


def operador_nuevo(request):
    if not es_central(request.user):
        return _prohibido(request)
    if request.method == "POST":
        form = OperadorForm(request.POST)
        if form.is_valid():
            crear_operador(
                biblioteca=Biblioteca.actual(),
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                nombre_visible=form.cleaned_data["nombre_visible"],
                actor=request.user,
            )
            messages.success(request, "Subcuenta de operador creada.")
            return redirect("cuentas:operador_lista")
    else:
        form = OperadorForm()
    return render(request, "cuentas/operador_form.html", {"form": form})


def operador_desactivar(request, pk):
    return _cambiar_estado_operador(request, pk, activo=False)


def operador_reactivar(request, pk):
    return _cambiar_estado_operador(request, pk, activo=True)


def _cambiar_estado_operador(request, pk, *, activo: bool):
    if not es_central(request.user):
        return _prohibido(request)
    if request.method != "POST":
        return HttpResponseRedirect(reverse("cuentas:operador_lista"))
    operador = get_object_or_404(Operador, pk=pk)
    if (
        not activo
        and operador.es_central
        and Operador.objects.filter(es_central=True, user__is_active=True).count() <= 1
    ):
        messages.error(request, "No se puede desactivar la única cuenta central.")
        return redirect("cuentas:operador_lista")
    fijar_estado_operador(operador=operador, activo=activo, actor=request.user)
    messages.success(request, f"Operador {'reactivado' if activo else 'desactivado'}.")
    return redirect("cuentas:operador_lista")


def operador_renombrar(request, pk):
    if not es_central(request.user):
        return _prohibido(request)
    operador = get_object_or_404(Operador, pk=pk)
    if request.method == "POST":
        form = RenombrarOperadorForm(request.POST)
        if form.is_valid():
            renombrar_operador(
                operador=operador,
                nombre_visible=form.cleaned_data["nombre_visible"],
                actor=request.user,
            )
            messages.success(request, "Nombre del operador actualizado.")
            return redirect("cuentas:operador_lista")
    else:
        form = RenombrarOperadorForm(initial={"nombre_visible": operador.nombre_visible})
    return render(request, "cuentas/operador_renombrar.html", {"form": form, "operador": operador})


def operador_restablecer(request, pk):
    if not es_central(request.user):
        return _prohibido(request)
    operador = get_object_or_404(Operador, pk=pk)
    if request.method == "POST":
        form = RestablecerPasswordForm(request.POST)
        if form.is_valid():
            restablecer_password(operador=operador, password=form.cleaned_data["password"], actor=request.user)
            messages.success(request, "Contraseña restablecida.")
            return redirect("cuentas:operador_lista")
    else:
        form = RestablecerPasswordForm()
    return render(request, "cuentas/operador_form.html", {"form": form, "operador": operador, "restablecer": True})


def username_disponible(request):
    """Validación en línea (HTMX) del nombre de usuario."""
    from django.contrib.auth import get_user_model

    valor = (request.GET.get("username") or "").strip()
    if not valor:
        return HttpResponse("")
    existe = get_user_model().objects.filter(username__iexact=valor).exists()
    if existe:
        return HttpResponse('<span class="text-danger">Ese nombre de usuario ya existe.</span>')
    return HttpResponse('<span class="text-success">Disponible.</span>')


class AuditoriaListView(LoginRequiredMixin, ListView):
    template_name = "cuentas/auditoria_lista.html"
    context_object_name = "entradas"
    paginate_by = 25

    def get_queryset(self):
        qs = EntradaAuditoria.objects.select_related("actor")
        entidad = self.request.GET.get("entidad")
        entidad_id = self.request.GET.get("entidad_id")
        if entidad:
            qs = qs.filter(entidad=entidad)
        if entidad_id and entidad_id.isdigit():
            qs = qs.filter(entidad_id=int(entidad_id))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["entidad_choices"] = EntradaAuditoria.Entidad.choices
        return ctx


def _prohibido(request):
    return render(
        request,
        "common/prohibido.html",
        {"detalle": "Esta acción está reservada a la cuenta central de la biblioteca."},
        status=403,
    )
