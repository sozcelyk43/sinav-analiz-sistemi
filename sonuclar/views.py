from django.shortcuts import render
from django.db.models import Sum # Toplama işlemi için
from .forms import OgrenciAnalizFormu
from .models import Sonuc, Ders, Ogrenci, Sinav # Gerekli modelleri import ediyoruz
import json # Şablona JSON verisi göndermek için

# Derslerin sabit bir listesini tanımlayalım (grafiklerde bu sırayla gösterilecek)
# Bu liste, DERS_BILGILERI (admin.py'deki) ile tutarlı olmalı veya oradan alınmalı.
# Şimdilik burada elle tanımlayalım.
DERS_ADLARI_SIRALI = [
    "Türkçe",
    "Matematik",
    "Fen Bilimleri",
    "Sosyal Bilgiler",
    "Yabancı Dil",
    "Din Kültürü"
]

def ogrenci_analiz_view(request):
    """
    Öğrenci bazlı, tarih aralığına göre sınav sonuçlarını
    ve ders bazlı pasta grafiklerini gösteren view.
    """
    form = OgrenciAnalizFormu(request.POST or None)
    analiz_verileri = None # Grafik verilerini tutacak
    secilen_ogrenci_adi = None

    if request.method == 'POST' and form.is_valid():
        ogrenci = form.cleaned_data['ogrenci']
        baslangic_tarihi = form.cleaned_data['baslangic_tarihi']
        bitis_tarihi = form.cleaned_data['bitis_tarihi']
        secilen_ogrenci_adi = ogrenci.ad_soyad

        # Belirtilen öğrenci ve tarih aralığındaki sınavları filtrele
        # Sinav modelinde 'tarih' alanı olduğunu varsayıyoruz.
        gecerli_sinavlar = Sinav.objects.filter(
            tarih__gte=baslangic_tarihi,
            tarih__lte=bitis_tarihi
        )

        # Bu sınavlara ait, seçilen öğrencinin sonuçlarını çek
        sonuclar_query = Sonuc.objects.filter(
            ogrenci=ogrenci,
            sinav__in=gecerli_sinavlar
        )

        ders_bazli_sonuclar = {}
        # DERS_ADLARI_SIRALI listesindeki her ders için veri topla
        for ders_adi in DERS_ADLARI_SIRALI:
            try:
                ders_obj = Ders.objects.get(ad=ders_adi) # Ders objesini adıyla bul
                # O derse ait sonuçları filtrele ve doğru, yanlış, boş sayılarını topla
                toplamlar = sonuclar_query.filter(ders=ders_obj).aggregate(
                    toplam_dogru=Sum('dogru_sayisi'),
                    toplam_yanlis=Sum('yanlis_sayisi'),
                    toplam_bos=Sum('bos_sayisi')
                )
                
                # Eğer o ders için hiç sonuç yoksa toplamlar None olabilir, 0 yapalım.
                dogru = toplamlar['toplam_dogru'] if toplamlar['toplam_dogru'] is not None else 0
                yanlis = toplamlar['toplam_yanlis'] if toplamlar['toplam_yanlis'] is not None else 0
                bos = toplamlar['toplam_bos'] if toplamlar['toplam_bos'] is not None else 0

                # Sadece anlamlı veri varsa (en az bir doğru, yanlış veya boş varsa) ekle
                if dogru > 0 or yanlis > 0 or bos > 0:
                    ders_bazli_sonuclar[ders_adi] = {
                        'dogru': dogru,
                        'yanlis': yanlis,
                        'bos': bos,
                    }
            except Ders.DoesNotExist:
                # Eğer DERS_ADLARI_SIRALI listesindeki bir ders DB'de yoksa, bu dersi atla
                # Ya da bir uyarı loglayabilirsiniz.
                pass 
        
        if ders_bazli_sonuclar:
            analiz_verileri = ders_bazli_sonuclar
            # Chart.js için veriyi JSON formatına çevirelim (şablonda kullanılacak)
            # Sadece grafik için gerekli olan kısmı JSON yapalım
            grafik_verisi_json = {}
            for ders, toplamlar in analiz_verileri.items():
                 grafik_verisi_json[ders] = [toplamlar['dogru'], toplamlar['yanlis'], toplamlar['bos']]
            
            # Şablona göndermek için JSON string'e çevir
            analiz_verileri_json = json.dumps(grafik_verisi_json)


    context = {
        'form': form,
        'analiz_verileri': analiz_verileri, # Ham veri (tablo vb. için)
        'analiz_verileri_json': analiz_verileri_json if 'analiz_verileri_json' in locals() else None, # Grafik için JSON string
        'secilen_ogrenci_adi': secilen_ogrenci_adi,
        'ders_etiketleri': json.dumps(["Doğru", "Yanlış", "Boş"]) # Tüm grafikler için ortak etiketler
    }
    return render(request, 'sonuclar/ogrenci_analiz_sayfasi.html', context)

# sonuclar/views.py dosyasının sonuna ekleyin

def ana_sayfa_view(request):
    """
    Uygulamanın ana sayfasını gösterir.
    """
    return render(request, 'sonuclar/ana_sayfa.html')
