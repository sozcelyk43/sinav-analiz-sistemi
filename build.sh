#!/usr/bin/env bash
# exit on error: Herhangi bir komut hata verirse script'i durdurur.
set -o errexit

# requirements.txt dosyasındaki Python paketlerini kurar.
# Render bu komutu çalıştırmadan önce genellikle bir sanal ortam oluşturur.
echo "Python paketleri kuruluyor..."
pip install -r requirements.txt

# Django statik dosyalarını (admin CSS/JS, uygulamanızın statik dosyaları vb.)
# settings.py'deki STATIC_ROOT ile belirtilen klasöre toplar.
# --no-input: Komutun kullanıcıdan onay istemeden çalışmasını sağlar.
echo "Statik dosyalar toplanıyor..."
python manage.py collectstatic --no-input

# Veritabanı şemasındaki değişiklikleri (modellerdeki güncellemeleri)
# veritabanına uygular. Render'da bu, PostgreSQL veritabanına uygulanır.
echo "Veritabanı migration'ları uygulanıyor..."
python manage.py migrate

echo "Build script tamamlandı."
