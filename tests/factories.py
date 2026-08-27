"""Factories de prueba."""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model

from catalogo.models import Ejemplar, Titulo
from cuentas.models import Biblioteca, Operador


class BibliotecaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Biblioteca

    nombre = factory.Sequence(lambda n: f"Biblioteca {n}")


class OperadorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Operador

    biblioteca = factory.SubFactory(BibliotecaFactory)
    es_central = False
    nombre_visible = factory.Sequence(lambda n: f"Operador {n}")
    user = factory.LazyAttribute(
        lambda o: get_user_model().objects.create_user(
            username=f"op{factory.Faker('random_int').evaluate(None, None, {'locale': None})}", password="clave-larga-1"
        )
    )


class TituloFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Titulo

    biblioteca = factory.SubFactory(BibliotecaFactory)
    titulo = factory.Sequence(lambda n: f"Título número {n}")
    autor = factory.Sequence(lambda n: f"Autor {n}")


class EjemplarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ejemplar

    titulo = factory.SubFactory(TituloFactory)
    codigo = factory.Sequence(lambda n: f"EJ-{n:05d}")
