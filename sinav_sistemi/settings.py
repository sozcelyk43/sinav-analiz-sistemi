"""
Django settings for sinav_sistemi project.
"""
from pathlib import Path
import os
import dj_database_url # Fly.io'da veritabanı bağlantısı için

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY'i ortam değişkeninden al. Fly.io'da bunu secret olarak ayarlayacağız.
# Yerel geliştirme için varsayılan bir değer kullanın.
# ÖNEMLİ: Canlıda KESİNLİKLE bu varsayılan anahtarı kullanmayın!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'Allalbin435')

# DEBUG modunu ortam değişkeninden al. Fly.io'da 'False' olmalı.
# FLY_APP_NAME ortam değişkeni Fly.io tarafından otomatik olarak ayarlanır.
DEBUG = not os.environ.get('FLY_APP_NAME') # Eğer FLY_APP_NAME varsa, DEBUG=False olur.

ALLOWED_HOSTS = []

# Fly.io tarafından sağlanan hostname'i ALLOWED_HOSTS'a ekle
FLY_APP_HOSTNAME = os.environ.get('FLY_APP_NAME')
if FLY_APP_HOSTNAME:
    ALLOWED_HOSTS.append(f"{FLY_APP_HOSTNAME}.fly.dev")

# Eğer bir custom domain (özel alan adı) ayarlarsanız, onu da buraya ekleyin:
# ALLOWED_HOSTS.append('www.sizinanalizsiteniz.com')

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
    'whitenoise.runserver_nostatic', # Whitenoise (statik dosyalar için)
    'django.contrib.staticfiles',
    'sonuclar', # Kendi uygulamamız
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise middleware'i SecurityMiddleware'den HEMEN SONRA
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
        'DIRS': [BASE_DIR / 'templates'], # Proje geneli templates klasörü
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
# Fly.io'da PostgreSQL kullanacağız ve bağlantı bilgilerini DATABASE_URL ortam değişkeninden alacağız.
if os.environ.get('DATABASE_URL'): # DATABASE_URL ortam değişkeni varsa
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600, # Bağlantı ömrü (saniye)
            sslmode='prefer' # Veya 'require' - Fly.io PostgreSQL genellikle SSL gerektirir
        )
    }
else: # Yerel geliştirme ortamında SQLite kullanmaya devam et
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# `collectstatic` komutunun tüm statik dosyaları toplayacağı klasör
# Dockerfile'daki WORKDIR /app olduğu için bu yol /app/staticfiles_live olur.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_live') 

# Whitenoise'un sıkıştırılmış statik dosyaları sunmasını sağlar (önerilir)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/hesap/login/'

# Fly.io'da HTTPS üzerinden çalışacağı için ek güvenlik ayarları
if os.environ.get('FLY_APP_NAME'):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # Fly.io proxy için
    SECURE_SSL_REDIRECT = True
    # HSTS ayarları isteğe bağlıdır ama önerilir
    # SECURE_HSTS_SECONDS = 31536000 
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
