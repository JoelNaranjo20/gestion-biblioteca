from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from cuentas.permissions import es_central
from prestamos.models import PersonaPrestataria

from .services import anonimizar_persona, anonimizar_vencidas, personas_anonimizables


def _solo_central(request):
    return render(
        request,
        "common/prohibido.html",
        {"detalle": "La anonimización solo puede lanzarla la cuenta central."},
        status=403,
    )


@login_required
def panel(request):
    if not es_central(request.user):
        return _solo_central(request)
    return render(
        request,
        "privacidad/panel.html",
        {"n_anonimizables": personas_anonimizables().count()},
    )


@login_required
def ejecutar_ahora(request):
    if not es_central(request.user):
        return _solo_central(request)
    if request.method == "POST":
        n = anonimizar_vencidas(actor=request.user)
        messages.success(request, f"Anonimización ejecutada: {n} persona(s).")
    return redirect("privacidad:panel")


@login_required
def anonimizar_persona_view(request, pk):
    if not es_central(request.user):
        return _solo_central(request)
    persona = get_object_or_404(PersonaPrestataria, pk=pk)
    if request.method == "POST":
        try:
            anonimizar_persona(persona, actor=request.user, motivo=request.POST.get("motivo", ""))
        except ValidationError as exc:
            messages.error(request, exc.message)
            return redirect("privacidad:panel")
        messages.success(request, "Persona anonimizada.")
    return redirect("privacidad:panel")
