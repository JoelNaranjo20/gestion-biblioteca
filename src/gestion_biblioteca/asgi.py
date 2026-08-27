"""ASGI para la Biblioteca Municipal (no usado en el empaquetado de escritorio)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_biblioteca.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
