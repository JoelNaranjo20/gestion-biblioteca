"""Fixtures compartidas de pruebas."""

from __future__ import annotations

import pytest


@pytest.fixture
def biblioteca(db):
    from cuentas.models import Biblioteca

    return Biblioteca.objects.create(nombre="Biblioteca de pruebas", creada_por_email="c@x.org")


@pytest.fixture
def central(db, biblioteca):
    """Cuenta central autenticable (usuario 'central@x.org')."""
    from django.contrib.auth import get_user_model

    from cuentas.models import Operador

    user = get_user_model().objects.create_user(
        username="central@x.org",
        email="central@x.org",
        password="clave-central-1",
        is_staff=True,
        is_superuser=True,
    )
    return Operador.objects.create(user=user, biblioteca=biblioteca, es_central=True, nombre_visible="Cuenta central")


@pytest.fixture
def operador(db, biblioteca):
    """Subcuenta de operador 'mostrador1'."""
    from django.contrib.auth import get_user_model

    from cuentas.models import Operador

    user = get_user_model().objects.create_user(username="mostrador1", email="", password="clave-operador-1")
    return Operador.objects.create(user=user, biblioteca=biblioteca, nombre_visible="Mostrador 1")


@pytest.fixture
def parametros(db, biblioteca):
    from configuracion.models import ParametrosPrestamo

    return ParametrosPrestamo.objects.create(biblioteca=biblioteca)
