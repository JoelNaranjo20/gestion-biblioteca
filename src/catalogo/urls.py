from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("titulos/nuevo/", views.titulo_nuevo, name="titulo_nuevo"),
    path("titulos/<int:pk>/", views.titulo_detalle, name="titulo_detalle"),
    path("titulos/<int:pk>/editar/", views.titulo_editar, name="titulo_editar"),
    path("titulos/<int:pk>/ejemplares/nuevo/", views.ejemplar_nuevo, name="ejemplar_nuevo"),
    path("ejemplares/<int:pk>/retirar/", views.ejemplar_retirar, name="ejemplar_retirar"),
    path(
        "ejemplares/<int:pk>/anular-retirada/",
        views.ejemplar_anular_retirada,
        name="ejemplar_anular_retirada",
    ),
    path("ejemplares/<int:pk>/historial/", views.ejemplar_historial, name="ejemplar_historial"),
    path("buscar/", views.buscar, name="buscar"),
    path("buscar.json", views.buscar_json, name="buscar_json"),
    path(
        "ejemplar-por-codigo.json",
        views.ejemplar_por_codigo_json,
        name="ejemplar_por_codigo_json",
    ),
]
