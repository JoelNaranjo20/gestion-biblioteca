"""Lanzador de escritorio: sirve Django en localhost con waitress y abre una ventana pywebview.

Uso en desarrollo:  python desktop/launcher.py
Empaquetado:        pyinstaller desktop/build.spec  ->  dist/BibliotecaMunicipal/
"""

from __future__ import annotations

import os
import socket
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_biblioteca.settings")
os.environ.setdefault("APP_ENTORNO", "desktop")


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _preparar_django() -> None:
    import django
    from django.core.management import call_command

    django.setup()
    # Aplica migraciones pendientes en el primer arranque / tras una actualización.
    try:
        call_command("migrate", interactive=False, verbosity=0)
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] No se pudieron aplicar migraciones: {exc}")


def _servir(puerto: int) -> None:
    from waitress import serve

    from gestion_biblioteca.wsgi import application

    serve(application, host="127.0.0.1", port=puerto, threads=6, _quiet=True)


def _comprobar_webview2() -> None:
    """Avisa si falta el runtime de WebView2 (necesario para la ventana en Windows 10/11)."""
    if sys.platform != "win32":
        return
    import winreg

    claves = [
        r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    ]
    for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for clave in claves:
            try:
                with winreg.OpenKey(raiz, clave) as k:
                    if winreg.QueryValueEx(k, "pv")[0] not in (None, "", "0.0.0.0"):
                        return
            except OSError:
                continue
    print(
        "[aviso] No se detecta el runtime de Microsoft Edge WebView2.\n"
        "        Instálalo desde https://developer.microsoft.com/microsoft-edge/webview2/\n"
        "        (o abre http://127.0.0.1 en el navegador como alternativa)."
    )


def main() -> None:
    _comprobar_webview2()
    _preparar_django()
    puerto = _puerto_libre()
    hilo = threading.Thread(target=_servir, args=(puerto,), daemon=True)
    hilo.start()

    import webview  # pywebview

    icono = RAIZ / "desktop" / "icono.ico"
    webview.create_window(
        "Biblioteca Municipal",
        f"http://127.0.0.1:{puerto}/",
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    webview.start(icon=str(icono) if icono.exists() else None)


if __name__ == "__main__":
    main()
