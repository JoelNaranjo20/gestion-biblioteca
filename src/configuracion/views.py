from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render

from cuentas.models import EntradaAuditoria
from cuentas.permissions import es_central
from cuentas.services import registrar_auditoria

from .forms import ParametrosForm
from .models import get_parametros


def parametros(request):
    if not es_central(request.user):
        return render(
            request,
            "common/prohibido.html",
            {"detalle": "La configuración de préstamo solo puede cambiarla la cuenta central."},
            status=403,
        )
    obj = get_parametros()
    if request.method == "POST":
        form = ParametrosForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            registrar_auditoria(
                actor=request.user,
                tipo="cambio_configuracion",
                entidad=EntradaAuditoria.Entidad.CONFIGURACION,
                entidad_id=obj.id,
                detalle={
                    "plazo_dias": obj.plazo_dias,
                    "max_prestamos_persona": obj.max_prestamos_persona,
                },
            )
            messages.success(request, "Configuración actualizada. Solo afecta a préstamos nuevos.")
            return redirect("configuracion:parametros")
    else:
        form = ParametrosForm(instance=obj)
    return render(request, "configuracion/parametros.html", {"form": form, "obj": obj})
