from django.contrib import admin
from django.urls import path, include # include zaten import edilmiş olmalı
from sonuclar import views as sonuclar_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hesap/', include('django.contrib.auth.urls')), 
    
    # /sonuclar/ ile başlayan tüm URL isteklerini sonuclar.urls dosyasına yönlendiriyoruz.
    path('sonuclar/', include('sonuclar.urls')), # YENİ EKLENEN/GÜNCELLENEN SATIR
    
    path('', sonuclar_views.ana_sayfa_view, name='ana_sayfa'), 
]
