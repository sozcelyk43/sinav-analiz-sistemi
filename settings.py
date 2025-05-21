"""
Django settings for sinav_sistemi project.
"""
from pathlib import Path
import os
import dj_database_url # Veritabanı URL'ini ayrıştırmak için

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY'i ortam değişkeninden al. Canlı ortamda (Render) bunu secret olarak ayarlayacağız.
# Yerel geliştirme için varsayılan bir değer kullanın.
# ÖNEMLİ: Canlıda KESİNLİKLE bu varsayılan anahtarı kullanmayın!
# 'Allalbin435' yerine kendi güçlü yerel SECRET_KEY'inizi yazın.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'Allalbin435')

# DEBUG modunu ortam değişkeninden al. Canlı ortamda (Render) 'False' olmalı.
# Render'da DJANGO_DEBUG="False" olarak bir ortam değişkeni ayarlayabilirsiniz.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []

# Render tarafından sağlanan hostname'i ALLOWED_HOSTS'a ekle
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Yerel geliştirme için localhost'u da ekleyebilirsiniz
if DEBUG:
    ALLOWED_HOSTS.append('127.0.0.1')
    ALLOWED_HOSTS.append('localhost')

# Application definition
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

# Veritabanı Ayarları
# Canlı ortamda (Render) DATABASE_URL ortam değişkeninden alır.
if os.environ.get('DATABASE_URL'): 
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600, 
            ssl_require=True  # DÜZELTME: Render PostgreSQL için 'ssl_require=True' kullanılır
        )
    }
else: # Yerel geliştirme ortamında SQLite kullanmaya devam et
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