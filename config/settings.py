"""
Django settings for config project.

Soporta dos motores de base de datos mediante la variable de entorno DB_ENGINE:
  DB_ENGINE=sqlite   → SQLite local (por defecto, ideal para POC y pruebas)
  DB_ENGINE=postgres → PostgreSQL real (datos operacionales reales mct_*)

Consultar README.md para instrucciones de cambio de motor.
"""

from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env (si existe)
if _DOTENV_AVAILABLE:
    _env_path = BASE_DIR / '.env'
    if _env_path.exists():
        load_dotenv(_env_path)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-uh(3ifn!9v(jok1d_uqc!m4h#qcmr%^%t)*3ta(^(71&vn&3c4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps de la POC
    'planning',
    'analytics',
    'scheduling',
    'quality',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==============================================================================
# DATABASE CONFIGURATION — Dual Engine Support
# ==============================================================================
# Controlar el motor mediante la variable de entorno DB_ENGINE:
#   DB_ENGINE=sqlite   → SQLite (por defecto) — ideal para POC / desarrollo
#   DB_ENGINE=postgres → PostgreSQL real      — datos operacionales mct_*
#
# Las tablas mct_* en PostgreSQL residen en el esquema 'traking'.
# El search_path garantiza que el ORM las encuentre sin prefijo de esquema.
# ==============================================================================

_DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').lower()

if _DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'np_sis'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            # La contraseña se lee de variable de entorno. NUNCA en código fuente.
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                # Crucial: ubica el search_path en traking para que las
                # tablas mct_* sean visibles sin prefijo de esquema.
                'options': f"-c search_path={os.environ.get('DB_SCHEMA', 'traking')},public"
            },
            # Base de datos para pruebas automatizadas en modo PostgreSQL
            'TEST': {
                'NAME': 'test_planificador_poc',
            },
        }
    }
else:
    # SQLite — modo por defecto de la POC
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Exponer el motor seleccionado para uso en servicios y vistas
# Usar planning.db_utils.is_postgres() / is_sqlite() en lugar de esta variable directamente
DB_ENGINE = _DB_ENGINE


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'planning': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
        'analytics': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
        'scheduling': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
        'quality': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
    },
}
