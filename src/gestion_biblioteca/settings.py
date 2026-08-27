"""Configuración de Django para la Biblioteca Municipal.

Gobernada por la variable de entorno APP_ENTORNO: dev | desktop | test.
Stack fijado en specs/001-catalog-loans/tech-stack.md.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # raíz del repo
SRC_DIR = BASE_DIR / "src"

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    SESSION_INACTIVIDAD_SEGUNDOS=(int, 1800),
    RETENCION_PRESTATARIOS_DIAS=(int, 730),
    SENTRY_DSN=(str, ""),
)
environ.Env.read_env(BASE_DIR / ".env")

APP_ENTORNO = env("APP_ENTORNO", default="dev")
# Detección robusta del entorno de pruebas (aunque no se exporte APP_ENTORNO).
ES_TEST = APP_ENTORNO == "test" or "pytest" in sys.modules
ES_DESKTOP = APP_ENTORNO == "desktop" and not ES_TEST
ES_DESKTOP = APP_ENTORNO == "desktop"

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-no-usar-en-produccion")
DEBUG = False if ES_DESKTOP else env("DJANGO_DEBUG")

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# --- Aplicaciones ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "axes",
    "crispy_forms",
    "crispy_bootstrap5",
    "common",
    "cuentas",
    "catalogo",
    "prestamos",
    "configuracion",
    "privacidad",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.ErrorConexionBDMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "gestion_biblioteca.urls"
WSGI_APPLICATION = "gestion_biblioteca.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.operador_actual",
            ],
        },
    },
]

# --- Base de datos ---
if ES_TEST:
    DATABASES = {
        "default": env.db("DATABASE_TEST_URL", default="postgres://postgres:postgres@localhost:5432/biblioteca_test")
    }
else:
    DATABASES = {"default": env.db("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/biblioteca")}

# Supabase / Postgres: SSL y sin conexiones persistentes (el pooler las reutiliza).
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["CONN_MAX_AGE"] = 0
if "supabase.com" in DATABASES["default"].get("HOST", ""):
    DATABASES["default"]["OPTIONS"].setdefault("sslmode", "require")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticación ---
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "cuentas:entrar"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "cuentas:entrar"

# --- Sesión: cierre por inactividad ---
SESSION_INACTIVIDAD_SEGUNDOS = env("SESSION_INACTIVIDAD_SEGUNDOS")
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = SESSION_INACTIVIDAD_SEGUNDOS
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # localhost HTTP dentro del webview
CSRF_COOKIE_SAMESITE = "Lax"

# --- django-axes: bloqueo por intentos fallidos ---
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=10)
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLED = not ES_TEST  # desactivado en pruebas para no interferir

# --- Internacionalización ---
LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# --- Estáticos ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [SRC_DIR / "common" / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if (DEBUG or ES_TEST)
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
# En dev/test se sirven los estáticos desde los finders (sin `collectstatic`).
WHITENOISE_USE_FINDERS = DEBUG or ES_TEST
WHITENOISE_AUTOREFRESH = DEBUG or ES_TEST

# --- crispy-forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- Parámetros de dominio ---
RETENCION_PRESTATARIOS_DIAS = env("RETENCION_PRESTATARIOS_DIAS")


# --- Logging ---
def _dir_logs() -> Path:
    import os

    base = os.environ.get("LOCALAPPDATA")
    carpeta = Path(base) / "BibliotecaMunicipal" / "logs" if base else BASE_DIR / "logs"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "estandar": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "estandar"},
        "fichero": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(_dir_logs() / "biblioteca.log"),
            "maxBytes": 2_000_000,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "estandar",
        },
    },
    "root": {"handlers": ["consola", "fichero"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["consola", "fichero"], "level": "ERROR", "propagate": False},
        "biblioteca": {"handlers": ["consola", "fichero"], "level": "INFO", "propagate": False},
    },
}

# --- Sentry (opcional, desactivado por defecto) ---
SENTRY_DSN = env("SENTRY_DSN")
if SENTRY_DSN and not ES_TEST:  # pragma: no cover
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.0, send_default_pii=False)
    except ImportError:
        pass
