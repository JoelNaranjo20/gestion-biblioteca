"""URLconf raíz de la Biblioteca Municipal."""

from django.contrib import admin
from django.urls import include, path

from common import views as common_views

urlpatterns = [
    path("", common_views.raiz, name="raiz"),
    path("inicio/panel/", common_views.inicio, name="inicio"),
    path("estado/conexion.json", common_views.ping_conexion, name="ping_conexion"),
    path("", include("cuentas.urls")),
    path("catalogo/", include("catalogo.urls")),
    path("prestamos/", include("prestamos.urls")),
    path("personas/", include("prestamos.urls_personas")),
    path("configuracion/", include("configuracion.urls")),
    path("privacidad/", include("privacidad.urls")),
    path("gestion-django/", admin.site.urls),
]
