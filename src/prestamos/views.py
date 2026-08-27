"""Vistas de préstamos: circulación, listas, correcciones y reclamación."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CorregirEjemplarForm, DevolucionForm, MotivoForm, PrestamoForm, ReclamacionForm
from .models import Prestamo
from .services import (
    EjemplarNoDisponible,
    NombreDistinto,
    TopeAlcanzado,
    anular_devolucion,
    anular_prestamo,
    corregir_ejemplar,
    historial_persona,
    prestamos_activos,
    prestamos_vencidos,
    prestamos_vencidos_de_persona,
    registrar_devolucion,
    registrar_prestamo,
    registrar_reclamacion,
)


@login_required
def nuevo(request):
    if request.method == "POST":
        form = PrestamoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                prestamo = registrar_prestamo(
                    actor=request.user,
                    codigo=d["codigo"],
                    documento=d["documento"],
                    nombre=d["nombre"],
                    contacto=d["contacto"],
                    confirmar_nombre=d["confirmar_nombre"],
                )
            except NombreDistinto as exc:
                form.data = form.data.copy()
                form.data["confirmar_nombre"] = "on"
                messages.warning(request, f"{exc.message} Vuelve a guardar para confirmar.")
                return render(request, "prestamos/nuevo.html", {"form": form})
            except (EjemplarNoDisponible, TopeAlcanzado) as exc:
                form.add_error(None, exc.message)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                vencidos = prestamos_vencidos_de_persona(prestamo.persona).exclude(pk=prestamo.pk)
                if vencidos:
                    codigos = ", ".join(p.ejemplar.codigo for p in vencidos)
                    messages.warning(
                        request,
                        f"Aviso: esta persona tiene {len(vencidos)} préstamo(s) vencido(s) sin "
                        f"devolver ({codigos}). El préstamo se ha registrado igualmente.",
                    )
                messages.success(
                    request,
                    f"Préstamo registrado. Fecha límite: {prestamo.fecha_limite:%d/%m/%Y}.",
                )
                return redirect("prestamos:detalle", pk=prestamo.pk)
    else:
        form = PrestamoForm()
    return render(request, "prestamos/nuevo.html", {"form": form})


@login_required
def devolver(request):
    if request.method == "POST":
        form = DevolucionForm(request.POST)
        if form.is_valid():
            try:
                prestamo = registrar_devolucion(actor=request.user, codigo=form.cleaned_data["codigo"])
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                if prestamo.dias_retraso:
                    messages.warning(request, f"Devuelto con retraso ({prestamo.dias_retraso} días).")
                else:
                    messages.success(request, "Devolución registrada.")
                return redirect("prestamos:detalle", pk=prestamo.pk)
    else:
        form = DevolucionForm()
    return render(request, "prestamos/devolver.html", {"form": form})


@login_required
def activos(request):
    return render(request, "prestamos/lista.html", {"prestamos": prestamos_activos(), "titulo": "Préstamos activos"})


@login_required
def vencidos(request):
    return render(
        request,
        "prestamos/lista.html",
        {"prestamos": prestamos_vencidos(), "titulo": "Préstamos vencidos", "solo_vencidos": True},
    )


@login_required
def detalle(request, pk):
    prestamo = get_object_or_404(
        Prestamo.objects.select_related("ejemplar__titulo", "persona", "registrado_por"), pk=pk
    )
    return render(
        request,
        "prestamos/detalle.html",
        {
            "p": prestamo,
            "reclamaciones": prestamo.reclamaciones.all(),
            "correcciones": prestamo.correcciones.all(),
        },
    )


def _accion_motivo(request, pk, funcion, exito, plantilla="prestamos/motivo.html", **extra):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == "POST":
        form = MotivoForm(request.POST)
        if form.is_valid():
            try:
                funcion(actor=request.user, prestamo=prestamo, motivo=form.cleaned_data["motivo"])
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, exito)
                return redirect("prestamos:detalle", pk=prestamo.pk)
    else:
        form = MotivoForm()
    return render(request, plantilla, {"form": form, "p": prestamo, **extra})


@login_required
def anular(request, pk):
    return _accion_motivo(request, pk, anular_prestamo, "Préstamo anulado.", accion="Anular préstamo")


@login_required
def anular_devolucion_view(request, pk):
    return _accion_motivo(
        request,
        pk,
        anular_devolucion,
        "Devolución anulada; el préstamo vuelve a estar activo.",
        accion="Anular devolución",
    )


@login_required
def corregir_ejemplar_view(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == "POST":
        form = CorregirEjemplarForm(request.POST)
        if form.is_valid():
            try:
                nuevo_p = corregir_ejemplar(
                    actor=request.user,
                    prestamo=prestamo,
                    motivo=form.cleaned_data["motivo"],
                    codigo_correcto=form.cleaned_data["codigo_correcto"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Ejemplar corregido: préstamo anterior anulado.")
                return redirect("prestamos:detalle", pk=nuevo_p.pk)
    else:
        form = CorregirEjemplarForm()
    return render(request, "prestamos/corregir_ejemplar.html", {"form": form, "p": prestamo})


@login_required
def reclamacion_nueva(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == "POST":
        form = ReclamacionForm(request.POST)
        if form.is_valid():
            try:
                registrar_reclamacion(
                    actor=request.user,
                    prestamo=prestamo,
                    fecha=form.cleaned_data["fecha"],
                    medio=form.cleaned_data["medio"],
                    notas=form.cleaned_data["notas"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                if prestamo.persona and not prestamo.persona.contacto:
                    messages.info(request, "Gestión registrada. La persona no tiene contacto guardado.")
                else:
                    messages.success(request, "Gestión de reclamación registrada.")
                return redirect("prestamos:detalle", pk=prestamo.pk)
    else:
        form = ReclamacionForm()
    return render(request, "prestamos/reclamacion_form.html", {"form": form, "p": prestamo})


@login_required
def persona_historial(request):
    documento = request.GET.get("documento", "").strip()
    prestamos = historial_persona(documento) if documento else None
    return render(request, "prestamos/persona_historial.html", {"documento": documento, "prestamos": prestamos})
