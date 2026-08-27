from django.urls import path

from . import views

app_name = "personas"

urlpatterns = [
    path("historial/", views.persona_historial, name="historial"),
]
