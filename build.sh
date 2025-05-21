#!/usr/bin/env bash
set -o errexit

echo "Python paketleri kuruluyor..."
pip install -r requirements.txt

echo "Statik dosyalar toplanıyor..."
python manage.py collectstatic --no-input

echo "Veritabanı migration'ları uygulanıyor..."
python manage.py migrate

echo "Build script tamamlandı."