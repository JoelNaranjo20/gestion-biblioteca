# Despliegue — Biblioteca Municipal

## 1. Base de datos (Supabase)

1. Crea un proyecto en Supabase. En **Project Settings → Database** copia la cadena del
   **Session pooler** (host `*.pooler.supabase.com`, puerto `5432`).
2. En cada puesto, `\.env`:

   ```env
   APP_ENTORNO=desktop
   SECRET_KEY=<clave única por instalación>
   DATABASE_URL=postgres://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
   SESSION_INACTIVIDAD_SEGUNDOS=1800
   RETENCION_PRESTATARIOS_DIAS=730
   ```

3. La primera vez (desde un puesto con la BD accesible):

   ```bash
   python manage.py migrate
   python manage.py crear_biblioteca --nombre "Biblioteca Municipal" --email direccion@ayto.example
   python manage.py crear_operador --username mostrador1
   ```

   El resto de operadores se crean desde la aplicación (menú **Operadores**, solo cuenta central).

## 2. Aplicación de escritorio

- Desarrollo: `python desktop/launcher.py`.
- Empaquetado (Windows): `pyinstaller desktop/build.spec` → `dist/BibliotecaMunicipal/`.
  Copia esa carpeta a cada puesto junto con su `.env`. Crea un acceso directo a
  `BibliotecaMunicipal.exe`. Coloca `desktop/icono.ico` antes de empaquetar si quieres icono.
- Requisito: **Microsoft Edge WebView2 Runtime** (presente por defecto en Windows 11 y en la
  mayoría de Windows 10). El lanzador avisa si falta.

## 3. Anonimización RGPD (tarea diaria)

En **un** puesto designado (el que esté más horas encendido), crea una tarea en el
**Programador de tareas de Windows**:

- Programa/script: `C:\ruta\a\dist\BibliotecaMunicipal\BibliotecaMunicipal.exe` no —
  usa el ejecutable de gestión: `manage.exe anonimizar_prestatarios`
  (PyInstaller genera `manage.exe` si se añade al `build.spec`; alternativamente, instala
  el proyecto con `uv` en ese puesto y programa `python manage.py anonimizar_prestatarios`).
- Frecuencia: diaria, fuera del horario de atención.

La cuenta central también puede lanzarla manualmente desde **RGPD → Ejecutar anonimización ahora**.

## 4. Copias de seguridad

- Supabase realiza copias automáticas (según el plan contratado). **Verifica mensualmente**
  desde el panel de Supabase (Database → Backups) que existen copias recientes y prueba una
  restauración en un proyecto de staging al menos una vez al año.
- Exporta además un volcado lógico periódico:
  `pg_dump "<DATABASE_URL>" -Fc -f biblioteca_$(date +%Y%m%d).dump` y guárdalo fuera de la nube.

## 5. Actualizaciones

- `uv lock --upgrade` + revisar cambios + `pytest` en verde antes de reempaquetar.
- Al desplegar una versión nueva, el lanzador aplica `migrate` en el primer arranque.
