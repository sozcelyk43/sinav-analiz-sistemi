from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '*-l9dt$58acv58a%!16r92sbne4y@f=!ot9=_3ciih&y574ad(') # YEREL KEYİNİZİ BURAYA YAZIN

# DEBUG modunu Koyeb ortam değişkeni ile ayarla
# KOYEB_APP_NAME veya KOYEB_SERVICE_ID gibi bir Koyeb ortam değişkeni varsa DEBUG=False olur.
# Alternatif olarak, Koyeb'de DJANGO_DEBUG="False" olarak bir ortam değişkeni ayarlayabilirsiniz.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
if os.environ.get('sinav-analiz-sistemi'): # Koyeb'in otomatik ayarladığı bir ortam değişkeni
    DEBUG = False

ALLOWED_HOSTS = []

# Koyeb tarafından sağlanan hostname'i ALLOWED_HOSTS'a ekle
KOYEB_PUBLIC_HOSTNAME = os.environ.get('vocal-maddy-sozcelyk43-2f45add4.koyeb.app')
if KOYEB_PUBLIC_HOSTNAME:
    ALLOWED_HOSTS.append(KOYEB_PUBLIC_HOSTNAME)

# Koyeb'in eski tip (app-org.koyeb.app) alan adı formatı için de bir kontrol eklenebilir (isteğe bağlı)
KOYEB_APP_NAME = os.environ.get('KOYEB_APP_NAME')
KOYEB_ORGANIZATION_ID = os.environ.get('KOYEB_ORGANIZATION_ID')
if KOYEB_APP_NAME and KOYEB_ORGANIZATION_ID:
    koyeb_legacy_host = f"{KOYEB_APP_NAME}-{KOYEB_ORGANIZATION_ID}.koyeb.app"
    if koyeb_legacy_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(koyeb_legacy_host)

# Eğer özel bir alan adı (custom domain) kullanıyorsanız, onu da buraya ekleyin:
# ALLOWED_HOSTS.append('www.sizinanalizsiteniz.com')

# Yerel geliştirme için
if DEBUG:
    ALLOWED_HOSTS.append('127.0.0.1')
    ALLOWED_HOSTS.append('localhost')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'sonuclar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sinav_sistemi.urls'

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

WSGI_APPLICATION = 'sinav_sistemi.wsgi.application'

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True # Koyeb PostgreSQL genellikle SSL gerektirir
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_live')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/hesap/login/'

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
