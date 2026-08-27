# Quickstart & Validación — Catálogo y Préstamos de la Biblioteca Municipal

**Feature**: `001-catalog-loans` · Guía para levantar el entorno y validar la funcionalidad extremo a extremo.
Detalles de modelo y endpoints: [data-model.md](./data-model.md), [contracts/operations.md](./contracts/operations.md).

---

## 1. Prerrequisitos

- Python 3.11+ y `uv` (o `pip`).
- Una cuenta de **Supabase** con un proyecto creado (plan gratuito sirve para desarrollo).
- Conexión a Internet (la app es solo en línea).
- Windows 10/11 para probar el empaquetado de escritorio (el desarrollo funciona en cualquier SO).

## 2. Configurar la base de datos (Supabase)

1. En el panel de Supabase → **Project Settings → Database** copia la cadena de conexión del **Session pooler** (puerto `5432`, host `*.pooler.supabase.com`).
2. Crea `.env` a partir de `.env.example`:

   ```env
   DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
   SECRET_KEY=<genera-una>
   DJANGO_DEBUG=False
   SESSION_INACTIVIDAD_SEGUNDOS=1800
   RETENCION_PRESTATARIOS_DIAS=730
   ```

3. Las extensiones `unaccent` y `pg_trgm` las habilita la primera migración; no hay que tocarlas a mano.

## 3. Instalar y migrar

```bash
uv sync                     # o: pip install -e .[dev]
python manage.py migrate    # crea el esquema en Supabase
python manage.py test       # debe pasar en verde
```

## 4. Crear la biblioteca y un operador

Opción A — por la app (recomendada, valida US6.1–US6.2):

```bash
python manage.py runserver 127.0.0.1:8000
# Abrir /inicio/alta-biblioteca/  → crear cuenta central (nombre, email, password)
# Iniciar sesión → /operadores/nuevo/ → crear "mostrador1" con contraseña
```

Opción B — sin interfaz:

```bash
python manage.py crear_biblioteca --nombre "Biblioteca Municipal" --email admin@ejemplo.org
python manage.py crear_operador --username mostrador1
```

## 5. Ejecutar como aplicación de escritorio

```bash
python desktop/launcher.py          # abre la ventana pywebview con el servidor local
# Empaquetar para Windows:
pyinstaller desktop/build.spec       # genera dist/BibliotecaMunicipal/
```

## 6. Programar la anonimización (producción)

En el puesto designado, crear una tarea en el **Programador de tareas de Windows** que ejecute a diario:

```bat
cd C:\ruta\a\dist\BibliotecaMunicipal && manage.exe anonimizar_prestatarios
```

La cuenta central también puede lanzarla desde `/privacidad/` → "Ejecutar ahora".

---

## 7. Escenarios de validación

Cada escenario referencia historias de usuario (`US`) y criterios de éxito (`SC`) del [spec](./spec.md). Ejecutar con datos limpios.

### E1 — Alta de cuentas y atribución · US6, SC-13, SC-14
1. Crear la cuenta central. **Esperado**: puede iniciar sesión.
2. Crear la subcuenta `mostrador1` (sin correo) en < 1 min. **Esperado**: `mostrador1` inicia sesión. *(SC-14)*
3. Con `mostrador1`, registrar un préstamo (ver E4). Abrir `/catalogo/ejemplares/<id>/historial/`. **Esperado**: el préstamo figura atribuido a `mostrador1` con fecha y hora. *(SC-13)*
4. Con la central, `/operadores/<id>/desactivar/` sobre `mostrador1`. **Esperado**: `mostrador1` ya no puede entrar; el préstamo anterior sigue atribuido a `mostrador1`.
5. Con `mostrador1` (reactívalo primero), entrar en `/configuracion/prestamos/`. **Esperado**: `403` — acción reservada a la central. *(US6.5)*

### E2 — Catálogo · US1
1. Crear un título sin autor. **Esperado**: rechazo indicando "autor" obligatorio. *(US1.4)*
2. Crear "El Quijote / Cervantes" con un ejemplar `Q-001`. **Esperado**: título guardado, `Q-001` = disponible.
3. Añadir ejemplar `Q-001` de nuevo. **Esperado**: rechazo por código duplicado. *(US1.5)*
4. Añadir `Q-002`; retirar `Q-002` con motivo "deteriorado". **Esperado**: disponibles del título pasan de 2 a 1; `Q-002` no aparece como prestable. *(US1.3)*

### E3 — Búsqueda y disponibilidad · US3, SC-3
1. `/catalogo/buscar/?q=quijote&campo=titulo`. **Esperado**: aparece el título con "2 ejemplares, 1 disponible".
2. Buscar `QUIJOTE` y `quijóte`. **Esperado**: mismos resultados (insensible a mayúsculas/acentos). *(FR-010)*
3. `/catalogo/ejemplar-por-codigo.json?codigo=Q-001`. **Esperado**: devuelve el ejemplar y su estado. Con `codigo=NOEXISTE` → `404`.
4. Con ~20.000 títulos de prueba cargados, medir la búsqueda. **Esperado**: < 2 s. *(SC-3)*

### E4 — Préstamo y devolución · US2, SC-1, SC-2, SC-5, SC-7
1. `/prestamos/nuevo/` con `codigo=Q-001`, `documento=12345678A`, `nombre=Ana`. **Esperado**: `Q-001` = prestado; `fecha_limite` = hoy + 15; operación < 1 min. *(SC-1, SC-5)*
2. Prestar `Q-001` otra vez. **Esperado**: `409` "no disponible", indica que lo tiene Ana. *(US2.2)*
3. Retirar `Q-001`. **Esperado**: bloqueado (está prestado). *(Edge)*
4. `/prestamos/devolver/` con `codigo=Q-001`. **Esperado**: `Q-001` vuelve a disponible < 2 s; sin retraso; operación < 30 s. *(SC-2, SC-7)*
5. Devolver `Q-001` de nuevo. **Esperado**: "no hay préstamo activo para ese ejemplar". *(US2.6)*
6. Crear un préstamo con `fecha_limite` en el pasado (fixture); devolverlo. **Esperado**: marcado "devuelto con retraso" con días de demora. *(US2.5)*

### E5 — Tope por persona · US2.7, US5
1. Config `max_prestamos_persona = 2` (con la central).
2. Prestar 2 ejemplares a `documento=99999999Z`. Intentar un 3.º. **Esperado**: `409` "máximo alcanzado", muestra 2 activos y tope 2. *(US2.7)*
3. Cambiar el tope a 5. **Esperado**: ahora admite el 3.º. Los préstamos previos no cambian. *(US5.4, FR-028)*

### E6 — Corrección de operaciones · US2.8–2.9, SC-11
1. Registrar un préstamo por error; `/prestamos/<id>/anular/` con motivo. **Esperado**: ejemplar disponible, préstamo "anulado", no cuenta para el tope, visible en historial como anulado. *(SC-11)*
2. Devolver un préstamo y luego `/prestamos/<id>/anular-devolucion/`. **Esperado**: vuelve a activo/prestado; vencido si la fecha límite ya pasó. *(Edge)*
3. `/catalogo/ejemplares/<id>/anular-retirada/` sobre un ejemplar retirado. **Esperado**: vuelve a disponible.

### E7 — Reclamación de vencidos · US4.5–4.6, SC-12
1. Tener un préstamo vencido. En `/prestamos/vencidos/` **esperado**: aparece con días de retraso y "sin reclamar".
2. `/prestamos/<id>/reclamaciones/nueva/` con `medio=telefono`. **Esperado**: la lista de vencidos muestra ahora la fecha y "teléfono" como última gestión. *(SC-12)*
3. Devolver ese préstamo e intentar añadir otra gestión. **Esperado**: rechazado (préstamo cerrado); las previas se conservan. *(Edge)*

### E8 — Historial y consultas · US4
1. `/personas/historial/?documento=12345678A`. **Esperado**: lista todos los préstamos de Ana, marcando los activos.
2. `/catalogo/ejemplares/<id>/historial/`. **Esperado**: préstamos del ejemplar del más reciente al más antiguo, con estado y correcciones.

### E9 — Anonimización RGPD · US-priv, SC-10
1. Fixture: persona `B` con último préstamo hace > 2 años, sin activos.
2. `POST /privacidad/ejecutar-ahora/` (o el management command). **Esperado**: `B` pasa a "anonimizada"; sus préstamos quedan sin persona pero conservan fechas; `/personas/historial/?documento=<doc de B>` no devuelve nada. *(SC-10, FR-037)*
3. Persona `C` con un préstamo activo: `POST /personas/<id>/anonimizar/`. **Esperado**: `409` (tiene préstamos activos). *(FR-036)*

### E10 — Concurrencia y coherencia · SC-4
1. Lanzar dos peticiones de préstamo del mismo `codigo` casi simultáneas (script de test `TransactionTestCase`). **Esperado**: exactamente una tiene éxito; la otra recibe `409`. No hay dos préstamos activos para el ejemplar.
2. Comparar en cualquier momento la lista de activos con los ejemplares en estado `prestado`. **Esperado**: coinciden exactamente. *(SC-4)*

### E11 — Sin conexión
1. Cortar la red y abrir cualquier pantalla. **Esperado**: aviso claro "sin conexión con la base de datos"; ninguna operación de escritura se registra a medias.

---

## 8. Mapa de cobertura (resumen)

| Historia / SC | Escenarios |
|---|---|
| US1 catálogo | E2 |
| US2 préstamo/devolución | E4, E5, E6 |
| US3 búsqueda | E3 |
| US4 consultas / reclamación | E7, E8 |
| US5 configuración | E5 |
| US6 cuentas | E1 |
| Protección de datos (FR-034–037) | E9 |
| SC-1..SC-2 tiempos | E4 |
| SC-3 búsqueda < 2 s | E3.4 |
| SC-4 coherencia | E10 |
| SC-5 fecha límite automática | E4.1 |
| SC-7 disponibilidad inmediata | E4.4 |
| SC-10 anonimización | E9 |
| SC-11 corrección | E6 |
| SC-12 reclamación visible | E7 |
| SC-13 atribución | E1.3 |
| SC-14 alta de operador < 1 min | E1.2 |
