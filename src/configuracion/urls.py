from django.urls import path

from . import views

app_name = "configuracion"

urlpatterns = [
    path("prestamos/", views.parametros, name="parametros"),
]
