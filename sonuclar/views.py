from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required # Giriş zorunluluğu için
from django.db.models import Sum
from .forms import OgrenciAnalizFormu # Güncellenmiş formu import ediyoruz
from .models import Sonuc, Ders, Ogrenci, Sinav
import json

# Grafiklerde derslerin gösterileceği sabit sıra
DERS_ADLARI_SIRALI = [
    "Türkçe",
    "Matematik",
    "Fen Bilimleri",
    "Sosyal Bilgiler",
    "Yabancı Dil",
    "Din Kültürü"
]

@login_required # Bu view fonksiyonuna erişim için kullanıcının giriş yapmış olması gerekir.
def ogrenci_analiz_view(request):
    """
    Giriş yapmış öğrenci için, belirtilen tarih aralığındaki sınav sonuçlarını
    ve ders bazlı pasta grafiklerini gösterir.
    """
    ogrenci_nesnesi = None
    try:
        # Giriş yapan kullanıcıya (request.user) bağlı Ogrenci nesnesini al.
        # Ogrenci modelindeki 'user' alanının OneToOneField(User, ...) olduğunu varsayıyoruz.
        ogrenci_nesnesi = Ogrenci.objects.get(user=request.user)
    except Ogrenci.DoesNotExist:
        # Eğer giriş yapan kullanıcıya bağlı bir Ogrenci profili yoksa,
        # bu durumu şablonda ele almak üzere bir işaretçi ayarla.
        # Bu senaryo, her User'ın bir Ogrenci profiline düzgün şekilde bağlanması durumunda oluşmamalıdır.
        context = {
            'form': OgrenciAnalizFormu(), # Formu yine de şablona gönder
            'ogrenci_profili_yok': True,
            'analiz_verileri_json': None, # Hata durumunda bu değişkenlerin None olmasını sağla
            'analiz_verileri': None,
            'secilen_ogrenci_adi': None,
            'ders_etiketleri': json.dumps(["Doğru", "Yanlış", "Boş"])
        }
        return render(request, 'sonuclar/ogrenci_analiz_sayfasi.html', context)

    # Formu POST verisiyle (eğer varsa) veya boş olarak başlat
    form = OgrenciAnalizFormu(request.POST or None)
    analiz_verileri = None
    analiz_verileri_json = None
    # Öğrenci adını doğrudan alınan Ogrenci nesnesinden al
    secilen_ogrenci_adi = ogrenci_nesnesi.ad_soyad if ogrenci_nesnesi else (request.user.get_full_name() or request.user.username)

    if request.method == 'POST' and form.is_valid():
        baslangic_tarihi = form.cleaned_data['baslangic_tarihi']
        bitis_tarihi = form.cleaned_data['bitis_tarihi']

        # Belirtilen tarih aralığındaki sınavları filtrele
        gecerli_sinavlar = Sinav.objects.filter(
            tarih__gte=baslangic_tarihi,
            tarih__lte=bitis_tarihi
        )

        # Sadece giriş yapmış öğrencinin (ogrenci_nesnesi) sonuçlarını çek
        sonuclar_query = Sonuc.objects.filter(
            ogrenci=ogrenci_nesnesi,
            sinav__in=gecerli_sinavlar
        )

        ders_bazli_sonuclar = {}
        for ders_adi in DERS_ADLARI_SIRALI:
            try:
                # Veritabanından Ders nesnesini adıyla bul
                ders_obj = Ders.objects.get(ad=ders_adi)
                # O derse ait sonuçları filtrele ve doğru, yanlış, boş sayılarını topla
                toplamlar = sonuclar_query.filter(ders=ders_obj).aggregate(
                    toplam_dogru=Sum('dogru_sayisi'),
                    toplam_yanlis=Sum('yanlis_sayisi'),
                    toplam_bos=Sum('bos_sayisi')
                )
                
                # Toplamlar None ise (o ders için sonuç yoksa) 0 olarak ayarla
                dogru = toplamlar['toplam_dogru'] if toplamlar['toplam_dogru'] is not None else 0
                yanlis = toplamlar['toplam_yanlis'] if toplamlar['toplam_yanlis'] is not None else 0
                bos = toplamlar['toplam_bos'] if toplamlar['toplam_bos'] is not None else 0

                # Sadece anlamlı veri varsa (en az bir doğru, yanlış veya boş varsa) sözlüğe ekle
                if dogru > 0 or yanlis > 0 or bos > 0:
                    ders_bazli_sonuclar[ders_adi] = {
                        'dogru': dogru,
                        'yanlis': yanlis,
                        'bos': bos,
                    }
            except Ders.DoesNotExist:
                # DERS_ADLARI_SIRALI listesindeki bir ders veritabanında yoksa, bu dersi atla.
                # İsteğe bağlı olarak burada bir uyarı loglanabilir.
                pass 
        
        if ders_bazli_sonuclar:
            analiz_verileri = ders_bazli_sonuclar
            # Chart.js için grafik verisini JSON formatına hazırla
            grafik_verisi_json_hazirla = {}
            for ders, toplam_degerleri in analiz_verileri.items():
                 grafik_verisi_json_hazirla[ders] = [toplam_degerleri['dogru'], toplam_degerleri['yanlis'], toplam_degerleri['bos']]
            # Şablona göndermek için JSON string'e çevir
            analiz_verileri_json = json.dumps(grafik_verisi_json_hazirla)

    context = {
        'form': form,
        'analiz_verileri': analiz_verileri,
        'analiz_verileri_json': analiz_verileri_json,
        'secilen_ogrenci_adi': secilen_ogrenci_adi,
        'ders_etiketleri': json.dumps(["Doğru", "Yanlış", "Boş"]),
        'ogrenci_profili_yok': False # Eğer bu noktaya gelinmişse profil var demektir.
    }
    return render(request, 'sonuclar/ogrenci_analiz_sayfasi.html', context)

def ana_sayfa_view(request):
    """
    Uygulamanın ana sayfasını gösterir.
    """
    return render(request, 'sonuclar/ana_sayfa.html')
