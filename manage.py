#!/usr/bin/env python
"""Utilidad de línea de comandos de Django."""

import os
import sys
from pathlib import Path


def main() -> None:
    # Las apps viven bajo src/
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_biblioteca.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y activado el entorno virtual? "
            "Ejecuta 'uv sync'."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
