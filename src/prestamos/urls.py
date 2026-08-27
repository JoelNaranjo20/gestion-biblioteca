from django.urls import path

from . import views

app_name = "prestamos"

urlpatterns = [
    path("nuevo/", views.nuevo, name="nuevo"),
    path("devolver/", views.devolver, name="devolver"),
    path("activos/", views.activos, name="activos"),
    path("vencidos/", views.vencidos, name="vencidos"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/anular/", views.anular, name="anular"),
    path("<int:pk>/anular-devolucion/", views.anular_devolucion_view, name="anular_devolucion"),
    path("<int:pk>/corregir-ejemplar/", views.corregir_ejemplar_view, name="corregir_ejemplar"),
    path("<int:pk>/reclamaciones/nueva/", views.reclamacion_nueva, name="reclamacion_nueva"),
]
