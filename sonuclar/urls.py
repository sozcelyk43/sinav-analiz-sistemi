from django.urls import path
from . import views # sonuclar/views.py dosyasını import ediyoruz

app_name = 'sonuclar' # Uygulama için bir namespace tanımlıyoruz (URL'leri tersine çevirirken kullanışlı)

urlpatterns = [
    path('ogrenci-analiz/', views.ogrenci_analiz_view, name='ogrenci_analiz_sayfasi'),
    # Gelecekte eklenebilecek diğer sonuclar uygulaması URL'leri buraya gelebilir.
]
