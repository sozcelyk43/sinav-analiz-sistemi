# Python'un resmi imajını temel al
# Render'da PYTHON_VERSION olarak 3.13.3 belirtmiştiniz.
# Docker Hub'da python:3.13-slim-bullseye gibi bir etiket arayabilirsiniz.
# Yoksa, projenizle uyumlu en yakın slim versiyonu kullanın (örn: 3.11 veya 3.12).
FROM python:3.11-slim-bullseye

# Ortam değişkenlerini ayarla
ENV PYTHONDONTWRITEBYTECODE 1  # .pyc dosyalarının oluşturulmasını engeller
ENV PYTHONUNBUFFERED 1         # Python çıktılarının doğrudan terminale yazılmasını sağlar

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını kur (PostgreSQL client gibi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt dosyasını kopyala ve paketleri kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarının geri kalanını kopyala
COPY . .

# Statik dosyaları topla
# Bu komut, settings.py'deki STATIC_ROOT ile belirtilen klasöre statik dosyaları toplar.
RUN python manage.py collectstatic --noinput

# Gunicorn'un çalışacağı port (Fly.io bunu fly.toml'dan yönetir)
# EXPOSE 8000 

# Başlatma komutu fly.toml'da tanımlanacak
# CMD ["gunicorn", "sinav_sistemi.wsgi:application", "--bind", "0.0.0.0:8000"]
