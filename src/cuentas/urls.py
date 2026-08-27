from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("inicio/alta-biblioteca/", views.alta_biblioteca_view, name="alta_biblioteca"),
    path("acceso/entrar/", views.EntrarView.as_view(), name="entrar"),
    path("acceso/salir/", views.SalirView.as_view(), name="salir"),
    path("operadores/", views.OperadorListView.as_view(), name="operador_lista"),
    path("operadores/nuevo/", views.operador_nuevo, name="operador_nuevo"),
    path("operadores/disponible/", views.username_disponible, name="username_disponible"),
    path("operadores/<int:pk>/desactivar/", views.operador_desactivar, name="operador_desactivar"),
    path("operadores/<int:pk>/reactivar/", views.operador_reactivar, name="operador_reactivar"),
    path("operadores/<int:pk>/restablecer-clave/", views.operador_restablecer, name="operador_restablecer"),
    path("auditoria/", views.AuditoriaListView.as_view(), name="auditoria_lista"),
]
