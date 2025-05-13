"""
Django settings for sinav_sistemi project.
"""
from pathlib import Path
import os
import dj_database_url # Render'da veritabanı bağlantısı için

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY'i ortam değişkeninden al, eğer yoksa (yerel geliştirme için) varsayılan bir değer kullan.
# Render'da bu ortam değişkenini ayarlayacağız.
# YEREL_GELISTIRME_SECRET_KEY_BURAYA_KOYUN kısmını kendi yerel SECRET_KEY'inizle değiştirebilirsiniz
# veya yeni bir tane üretebilirsiniz. Canlıda KESİNLİKLE bu varsayılanı kullanmayın.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-YEREL_GELISTIRME_SECRET_KEY_BURAYA_KOYUN')

# DEBUG modunu ortam değişkeninden al. Render'da 'False' olacak.
# 'RENDER' ortam değişkeni Render tarafından otomatik olarak ayarlanır.
DEBUG = 'RENDER' not in os.environ 
# Alternatif: DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True' 
# (Bu durumda Render'da DJANGO_DEBUG=False ayarlamanız gerekir)


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
    'whitenoise.runserver_nostatic', # Whitenoise (statik dosyalar için) - staticfiles'dan ÖNCE olmalı
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
# Render'da PostgreSQL kullanacağız ve bağlantı bilgilerini DATABASE_URL ortam değişkeninden alacağız.
if 'RENDER' in os.environ: # Render ortamında çalışıyorsak
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600, # Bağlantı ömrü (saniye)
            ssl_require=True  # Render PostgreSQL genellikle SSL gerektirir
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
LANGUAGE_CODE = 'tr-tr' # Türkçe ayarı
TIME_ZONE = 'Europe/Istanbul' # Türkiye saat dilimi
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/' # Tarayıcıda statik dosyalara erişim için URL ön eki
# `collectstatic` komutunun tüm statik dosyaları toplayacağı klasör
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_live') # Canlı ortam için farklı bir isim olabilir

# Whitenoise'un sıkıştırılmış statik dosyaları sunmasını sağlar (önerilir)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Kullanıcı giriş/çıkış sonrası yönlendirme ayarları
LOGIN_REDIRECT_URL = '/'  # Başarılı girişten sonra ana sayfaya yönlendir
LOGOUT_REDIRECT_URL = '/' # Başarılı çıkıştan sonra ana sayfaya yönlendir
LOGIN_URL = '/hesap/login/' # Giriş yapılmamışsa yönlendirilecek URL

# Render'da HTTPS üzerinden çalışacağı için ek güvenlik ayarları
if 'RENDER' in os.environ:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True # HTTP isteklerini otomatik olarak HTTPS'ye yönlendir
    SECURE_HSTS_SECONDS = 31536000 # 1 yıl (tarayıcıya siteyi sadece HTTPS ile açmasını söyler)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True # Alt alan adlarını da HSTS kapsamına al
    SECURE_HSTS_PRELOAD = True # Sitenizi HSTS preload listelerine göndermek için (isteğe bağlı)
