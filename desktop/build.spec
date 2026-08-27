# PyInstaller spec — Biblioteca Municipal (Windows, one-dir)
# Uso: pyinstaller desktop/build.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

RAIZ = Path.cwd()

hiddenimports = (
    collect_submodules("gestion_biblioteca")
    + collect_submodules("common")
    + collect_submodules("cuentas")
    + collect_submodules("catalogo")
    + collect_submodules("prestamos")
    + collect_submodules("configuracion")
    + collect_submodules("privacidad")
    + ["waitress", "psycopg", "argon2", "environ", "crispy_forms", "crispy_bootstrap5", "axes"]
)

datas = [
    (str(RAIZ / "src" / app / "templates"), f"{app}/templates")
    for app in ("common", "cuentas", "catalogo", "prestamos", "configuracion", "privacidad")
    if (RAIZ / "src" / app / "templates").exists()
]
datas += [(str(RAIZ / "src" / "common" / "static"), "common/static")]
datas += collect_data_files("crispy_bootstrap5")

a = Analysis(
    [str(RAIZ / "desktop" / "launcher.py")],
    pathex=[str(RAIZ / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="BibliotecaMunicipal", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="BibliotecaMunicipal")
