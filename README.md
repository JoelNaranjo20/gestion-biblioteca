# Biblioteca Municipal — Catálogo y Préstamos

Aplicación **de escritorio** (Django + pywebview) para el personal de la biblioteca municipal:
catálogo bibliográfico, préstamos y devoluciones, búsqueda con disponibilidad, consulta de
activos e historial, reclamación de vencidos, corrección de operaciones, configuración y
anonimización RGPD de prestatarios.

- Especificación y diseño: [`specs/001-catalog-loans/`](specs/001-catalog-loans/)
  (`spec.md`, `plan.md`, `tech-stack.md`, `data-model.md`, `contracts/`, `quickstart.md`,
  `tasks.md`).
- Principios del proyecto: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## Stack

Python 3.12+ · Django 5.2 LTS · PostgreSQL gestionado por Supabase (vía ORM de Django) ·
pywebview + PyInstaller · HTMX + Bootstrap 5 · `django.contrib.auth` · django-axes · Argon2.
Detalle en `specs/001-catalog-loans/tech-stack.md`.

## Puesta en marcha (desarrollo)

```bash
uv sync
cp .env.example .env          # ajusta DATABASE_URL (Postgres local o proyecto Supabase de dev)
python manage.py makemigrations   # reconcilia las migraciones con los modelos
python manage.py migrate
python manage.py crear_biblioteca --nombre "Biblioteca Municipal" --email admin@ejemplo.org
python manage.py crear_operador --username mostrador1
python manage.py runserver          # o: python desktop/launcher.py  (ventana de escritorio)
```

Pruebas (requieren PostgreSQL; los tests usan features de PostgreSQL):

```bash
createdb biblioteca_test
pytest
```

## Empaquetado para Windows

```bash
pyinstaller desktop/build.spec     # -> dist/BibliotecaMunicipal/
```

## Anonimización RGPD (producción)

Programar a diario en el Programador de tareas de Windows:

```
manage.exe anonimizar_prestatarios
```

## Estado de la implementación

Ver los checkboxes de [`specs/001-catalog-loans/tasks.md`](specs/001-catalog-loans/tasks.md).
