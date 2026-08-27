from django.urls import path

from . import views

app_name = "privacidad"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("ejecutar-ahora/", views.ejecutar_ahora, name="ejecutar_ahora"),
    path("personas/<int:pk>/anonimizar/", views.anonimizar_persona_view, name="anonimizar_persona"),
]
