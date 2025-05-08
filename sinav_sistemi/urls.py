
from django.contrib import admin
from django.urls import path, include
from sonuclar import views as sonuclar_views # sonuclar uygulamasının views.py dosyasını import ediyoruz

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sonuclar/', include('sonuclar.urls')), # sonuclar uygulamasının kendi URL'lerini dahil et
    path('', sonuclar_views.ana_sayfa_view, name='ana_sayfa'), # KÖK URL İÇİN BU SATIRIN OLDUĞUNDAN EMİN OLUN
]
