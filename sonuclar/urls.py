from django.urls import path
from . import views # sonuclar/views.py dosyasını import ediyoruz

app_name = 'sonuclar' # Uygulama için bir ad alanı (namespace) tanımlıyoruz

urlpatterns = [
    # /sonuclar/ogrenci-analiz/ URL'i için ogrenci_analiz_view fonksiyonunu bağlıyoruz
    path('ogrenci-analiz/', views.ogrenci_analiz_view, name='ogrenci_analiz_sayfasi'),
    
    # Gelecekte bu uygulamaya eklenebilecek diğer URL'ler buraya gelebilir.
    # Örneğin, tüm sınavların listelendiği bir sayfa veya belirli bir sınavın detayları vb.
]
