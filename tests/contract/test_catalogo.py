"""Contrato de endpoints de catálogo — títulos y ejemplares (T025)."""

import pytest

from catalogo.models import Ejemplar, Titulo

pytestmark = pytest.mark.django_db


@pytest.fixture
def login(client, operador):
    client.force_login(operador.user)
    return client


def test_titulo_nuevo_requiere_login(client, biblioteca):
    r = client.get("/catalogo/titulos/nuevo/")
    assert r.status_code == 302 and "/acceso/entrar/" in r["Location"]


def test_titulo_nuevo_get_y_post(login, biblioteca):
    assert login.get("/catalogo/titulos/nuevo/").status_code == 200
    r = login.post(
        "/catalogo/titulos/nuevo/",
        {
            "titulo": "El Quijote",
            "autor": "Cervantes",
            "isbn": "",
            "editorial": "",
            "anio": "",
            "materia": "",
            "codigo_primer_ejemplar": "Q-001",
            "confirmar_isbn": "",
        },
    )
    assert r.status_code == 302
    t = Titulo.objects.get(titulo="El Quijote")
    assert t.ejemplares.count() == 1


def test_titulo_nuevo_falta_autor_re_renderiza(login, biblioteca):
    r = login.post(
        "/catalogo/titulos/nuevo/",
        {
            "titulo": "Sin autor",
            "autor": "",
            "isbn": "",
            "editorial": "",
            "anio": "",
            "materia": "",
            "codigo_primer_ejemplar": "",
            "confirmar_isbn": "",
        },
    )
    assert r.status_code == 200
    assert not Titulo.objects.filter(titulo="Sin autor").exists()


def test_ejemplar_nuevo_y_codigo_duplicado(login, biblioteca, central):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="T", autor="A")
    r = login.post(f"/catalogo/titulos/{t.pk}/ejemplares/nuevo/", {"codigo": "E-1", "ubicacion": ""})
    assert r.status_code == 302
    r = login.post(f"/catalogo/titulos/{t.pk}/ejemplares/nuevo/", {"codigo": "E-1", "ubicacion": ""})
    assert r.status_code == 200  # re-render con error de duplicado
    assert Ejemplar.objects.filter(codigo="E-1").count() == 1


def test_ejemplar_retirar_pide_motivo_y_cambia_estado(login, biblioteca):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="T", autor="A")
    ej = Ejemplar.objects.create(titulo=t, codigo="R-1")
    assert login.get(f"/catalogo/ejemplares/{ej.pk}/retirar/").status_code == 200
    r = login.post(f"/catalogo/ejemplares/{ej.pk}/retirar/", {"motivo": "deteriorado"})
    assert r.status_code == 302
    ej.refresh_from_db()
    assert ej.estado == Ejemplar.Estado.RETIRADO


def test_titulo_detalle_y_ejemplar_historial(login, biblioteca):
    t = Titulo.objects.create(biblioteca=biblioteca, titulo="T", autor="A")
    ej = Ejemplar.objects.create(titulo=t, codigo="H-1")
    assert login.get(f"/catalogo/titulos/{t.pk}/").status_code == 200
    assert login.get(f"/catalogo/ejemplares/{ej.pk}/historial/").status_code == 200
