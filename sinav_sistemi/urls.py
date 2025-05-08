
from django.contrib import admin
from django.urls import path, include 
from sonuclar import views as sonuclar_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hesap/', include('django.contrib.auth.urls')),
    path('sonuclar/', include('sonuclar.urls')),
    path('', sonuclar_views.ana_sayfa_view, name='ana_sayfa'),
]
