"""Habilita las extensiones de PostgreSQL y un wrapper IMMUTABLE de unaccent.

`unaccent` no es IMMUTABLE por defecto, por lo que no puede usarse en columnas generadas ni
en índices funcionales. `immutable_unaccent(text)` fija el diccionario `unaccent` (patrón
habitual y seguro en instalaciones de un solo diccionario).
"""

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations

CREAR_WRAPPER = """
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;
"""

BORRAR_WRAPPER = "DROP FUNCTION IF EXISTS immutable_unaccent(text);"


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        UnaccentExtension(),
        TrigramExtension(),
        migrations.RunSQL(CREAR_WRAPPER, BORRAR_WRAPPER),
    ]
