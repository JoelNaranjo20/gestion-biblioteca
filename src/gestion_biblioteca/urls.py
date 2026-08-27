"""URLconf raíz de la Biblioteca Municipal.

Los includes de catalogo/prestamos/configuracion/privacidad se activan a medida que
cada historia de usuario se implementa (US1–US5). Ver specs/001-catalog-loans/tasks.md.
"""

from django.contrib import admin
from django.urls import include, path

from common import views as common_views

urlpatterns = [
    path("", common_views.raiz, name="raiz"),
    path("inicio/panel/", common_views.inicio, name="inicio"),
    path("estado/conexion.json", common_views.ping_conexion, name="ping_conexion"),
    path("", include("cuentas.urls")),
    path("gestion-django/", admin.site.urls),
    # path("catalogo/", include("catalogo.urls")),          # US1 / US3
    # path("prestamos/", include("prestamos.urls")),        # US2 / US4
    # path("personas/", include("prestamos.urls_personas")),# US4
    # path("configuracion/", include("configuracion.urls")),# US5
    # path("privacidad/", include("privacidad.urls")),      # Polish (RGPD)
]
