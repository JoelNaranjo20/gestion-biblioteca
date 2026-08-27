"""Vistas del catálogo: títulos, ejemplares, búsqueda y disponibilidad."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from cuentas.models import Biblioteca

from .forms import EjemplarForm, MotivoForm, TituloForm
from .models import Ejemplar, Titulo
from .services import (
    IsbnDuplicado,
    anular_retirada,
    buscar_titulos,
    crear_ejemplar,
    crear_titulo,
    editar_titulo,
    retirar_ejemplar,
    titulos_con_recuento,
)

PAGINA = 25


@login_required
def titulo_nuevo(request):
    if request.method == "POST":
        form = TituloForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                titulo = crear_titulo(
                    biblioteca=Biblioteca.actual(),
                    titulo=d["titulo"],
                    autor=d["autor"],
                    isbn=d["isbn"],
                    editorial=d["editorial"],
                    anio=d["anio"],
                    materia=d["materia"],
                    actor=request.user,
                    confirmar_isbn=d["confirmar_isbn"],
                )
            except IsbnDuplicado as exc:
                form.data = form.data.copy()
                form.data["confirmar_isbn"] = "on"
                messages.warning(request, f"{exc.message} Vuelve a guardar para confirmar.")
                return render(request, "catalogo/titulo_form.html", {"form": form})
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                if d["codigo_primer_ejemplar"]:
                    try:
                        crear_ejemplar(titulo_obj=titulo, codigo=d["codigo_primer_ejemplar"], actor=request.user)
                    except ValidationError as exc:
                        messages.warning(request, f"Título creado, pero el ejemplar no: {exc.message}")
                messages.success(request, "Título creado.")
                return redirect("catalogo:titulo_detalle", pk=titulo.pk)
    else:
        form = TituloForm()
    return render(request, "catalogo/titulo_form.html", {"form": form})


@login_required
def titulo_editar(request, pk):
    titulo = get_object_or_404(Titulo, pk=pk)
    if request.method == "POST":
        form = TituloForm(request.POST, instance=titulo)
        if form.is_valid():
            try:
                editar_titulo(
                    titulo_obj=titulo,
                    actor=request.user,
                    **{k: form.cleaned_data[k] for k in ("titulo", "autor", "isbn", "editorial", "anio", "materia")},
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Título actualizado.")
                return redirect("catalogo:titulo_detalle", pk=titulo.pk)
    else:
        form = TituloForm(instance=titulo)
    return render(request, "catalogo/titulo_form.html", {"form": form, "titulo": titulo})


@login_required
def titulo_detalle(request, pk):
    from django.db.models import Prefetch

    from prestamos.models import Prestamo

    titulo = get_object_or_404(titulos_con_recuento(), pk=pk)
    activos = Prestamo.objects.filter(
        estado_registro=Prestamo.EstadoRegistro.EFECTIVO, fecha_devolucion_real__isnull=True
    ).select_related("persona")
    ejemplares = titulo.ejemplares.select_related("titulo").prefetch_related(
        Prefetch("prestamos", queryset=activos, to_attr="prestamo_activo_lst")
    )
    return render(request, "catalogo/titulo_detalle.html", {"titulo": titulo, "ejemplares": ejemplares})


@login_required
def ejemplar_nuevo(request, pk):
    titulo = get_object_or_404(Titulo, pk=pk)
    if request.method == "POST":
        form = EjemplarForm(request.POST)
        if form.is_valid():
            try:
                crear_ejemplar(
                    titulo_obj=titulo,
                    codigo=form.cleaned_data["codigo"],
                    ubicacion=form.cleaned_data["ubicacion"],
                    actor=request.user,
                )
            except ValidationError as exc:
                form.add_error("codigo", exc)
            else:
                messages.success(request, "Ejemplar añadido.")
                return redirect("catalogo:titulo_detalle", pk=titulo.pk)
    else:
        form = EjemplarForm()
    return render(request, "catalogo/ejemplar_form.html", {"form": form, "titulo": titulo})


@login_required
def ejemplar_retirar(request, pk):
    ejemplar = get_object_or_404(Ejemplar, pk=pk)
    if request.method == "POST":
        form = MotivoForm(request.POST)
        if form.is_valid():
            try:
                retirar_ejemplar(ejemplar=ejemplar, motivo=form.cleaned_data["motivo"], actor=request.user)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Ejemplar retirado.")
                return redirect("catalogo:titulo_detalle", pk=ejemplar.titulo_id)
    else:
        form = MotivoForm()
    return render(request, "catalogo/ejemplar_retirar.html", {"form": form, "ejemplar": ejemplar})


@login_required
def ejemplar_anular_retirada(request, pk):
    ejemplar = get_object_or_404(Ejemplar, pk=pk)
    if request.method == "POST":
        form = MotivoForm(request.POST)
        if form.is_valid():
            try:
                anular_retirada(ejemplar=ejemplar, motivo=form.cleaned_data["motivo"], actor=request.user)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Retirada anulada; el ejemplar vuelve a estar disponible.")
                return redirect("catalogo:titulo_detalle", pk=ejemplar.titulo_id)
    else:
        form = MotivoForm()
    return render(request, "catalogo/ejemplar_retirar.html", {"form": form, "ejemplar": ejemplar, "anular": True})


@login_required
def ejemplar_historial(request, pk):
    ejemplar = get_object_or_404(Ejemplar.objects.select_related("titulo"), pk=pk)
    from prestamos.services import historial_ejemplar

    prestamos = historial_ejemplar(ejemplar)
    return render(request, "catalogo/ejemplar_historial.html", {"ejemplar": ejemplar, "prestamos": prestamos})


@login_required
def buscar(request):
    q = request.GET.get("q", "")
    campo = request.GET.get("campo", "titulo")
    resultados = buscar_titulos(texto=q, campo=campo) if q else None
    page = None
    if resultados is not None:
        page = Paginator(resultados, PAGINA).get_page(request.GET.get("pagina"))
    plantilla = "catalogo/_resultados.html" if request.headers.get("HX-Request") else "catalogo/buscar.html"
    return render(request, plantilla, {"q": q, "campo": campo, "page": page})


@login_required
def buscar_json(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"error": "Escribe al menos 2 caracteres."}, status=400)
    filas = [
        {
            "id": t.id,
            "titulo": t.titulo,
            "autor": t.autor,
            "total": t.n_total,
            "disponibles": t.n_disponibles,
        }
        for t in buscar_titulos(texto=q, campo="titulo")[:10]
    ]
    return JsonResponse({"resultados": filas})


@login_required
def ejemplar_por_codigo_json(request):
    codigo = (request.GET.get("codigo") or "").strip()
    try:
        ej = Ejemplar.objects.select_related("titulo").get(codigo=codigo)
    except Ejemplar.DoesNotExist:
        return JsonResponse({"error": "Código no encontrado."}, status=404)
    from prestamos.models import Prestamo

    activo = Prestamo.objects.filter(
        ejemplar=ej, estado_registro=Prestamo.EstadoRegistro.EFECTIVO, fecha_devolucion_real__isnull=True
    ).first()
    return JsonResponse(
        {
            "ejemplar_id": ej.id,
            "titulo": str(ej.titulo),
            "estado": ej.estado,
            "prestamo_activo_id": activo.id if activo else None,
        }
    )
