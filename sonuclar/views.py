from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .forms import OgrenciAnalizFormu
from .models import Sonuc, Ders, Ogrenci, Sinav, Konu, OgrenciYanlisDetayi
import json
from collections import defaultdict

DERS_ADLARI_SIRALI = [
    "Türkçe", "Matematik", "Fen Bilimleri", 
    "Sosyal Bilgiler", "Yabancı Dil", "Din Kültürü"
]

@login_required
def ogrenci_analiz_view(request):
    ogrenci_nesnesi = None
    try:
        ogrenci_nesnesi = Ogrenci.objects.get(user=request.user)
    except Ogrenci.DoesNotExist:
        context = {
            'form': OgrenciAnalizFormu(),
            'ogrenci_profili_yok': True,
            'ders_analiz_listesi': [],
            'analiz_verileri_json': None,
            'secilen_ogrenci_adi': None,
            'ders_etiketleri': json.dumps(["Doğru", "Yanlış", "Boş"])
        }
        return render(request, 'sonuclar/ogrenci_analiz_sayfasi.html', context)

    form = OgrenciAnalizFormu(request.POST or None)
    ders_analiz_listesi = [] 
    analiz_verileri_json_dict = {} 
    secilen_ogrenci_adi = ogrenci_nesnesi.ad_soyad if ogrenci_nesnesi else (request.user.get_full_name() or request.user.username)

    if request.method == 'POST' and form.is_valid():
        baslangic_tarihi = form.cleaned_data['baslangic_tarihi']
        bitis_tarihi = form.cleaned_data['bitis_tarihi']

        gecerli_sinavlar = Sinav.objects.filter(
            tarih__gte=baslangic_tarihi,
            tarih__lte=bitis_tarihi
        ).order_by('tarih')

        ogrencinin_tum_yanlis_detaylari = OgrenciYanlisDetayi.objects.filter(
            ogrenci=ogrenci_nesnesi,
            sinav__in=gecerli_sinavlar
        ).select_related('ders', 'konu', 'konu__ders', 'sinav')

        gruplanmis_yanlis_detaylari_tum_dersler = defaultdict(lambda: defaultdict(list))
        if ogrencinin_tum_yanlis_detaylari.exists():
            for detay in ogrencinin_tum_yanlis_detaylari:
                ders_adi_grup = detay.ders.ad
                unite_adi_grup = detay.konu.unite_adi
                konu_adi_grup = detay.konu.konu_adi
                gruplanmis_yanlis_detaylari_tum_dersler[ders_adi_grup][unite_adi_grup].append({
                    'konu': konu_adi_grup,
                    'yanlis_adedi': detay.yanlis_adedi,
                    'sinav_adi': detay.sinav.ad
                })

        for ders_adi_sirali in DERS_ADLARI_SIRALI:
            current_ders_data = {
                'ders_adi': ders_adi_sirali,
                'dyb_veriler': None, 
                'yanlis_detay_uniteler': None 
            }
            
            try:
                ders_obj = Ders.objects.get(ad=ders_adi_sirali)
                
                toplamlar = Sonuc.objects.filter(
                    ogrenci=ogrenci_nesnesi,
                    sinav__in=gecerli_sinavlar,
                    ders=ders_obj
                ).aggregate(
                    toplam_dogru=Sum('dogru_sayisi'),
                    toplam_yanlis=Sum('yanlis_sayisi'),
                    toplam_bos=Sum('bos_sayisi')
                )
                
                dogru = toplamlar['toplam_dogru'] if toplamlar['toplam_dogru'] is not None else 0
                yanlis = toplamlar['toplam_yanlis'] if toplamlar['toplam_yanlis'] is not None else 0
                bos = toplamlar['toplam_bos'] if toplamlar['toplam_bos'] is not None else 0
                toplam_soru = dogru + yanlis + bos

                # DÜZELTME: Pasta grafik verisini (analiz_verileri_json_dict) her zaman oluştur,
                #           ancak sadece toplam_soru > 0 ise anlamlı değerler ata.
                #           Şablondaki JavaScript zaten sadece verisi olan grafikleri çizecektir.
                #           Bu, dyb_veriler None olsa bile dersin JSON'da bir anahtarı olmasını sağlar (içi boş olsa da).
                
                # Her ders için JSON'da bir anahtar oluştur, D/Y/B sıfır olsa bile.
                # JavaScript tarafı, verisi [0,0,0] olan grafiği çizmeyecek veya boş gösterecektir.
                analiz_verileri_json_dict[ders_adi_sirali] = [dogru, yanlis, bos]

                if toplam_soru > 0: 
                    current_ders_data['dyb_veriler'] = {
                        'dogru': dogru, 
                        'yanlis': yanlis, 
                        'bos': bos,
                        'toplam_soru': toplam_soru 
                    }

                if ders_adi_sirali in gruplanmis_yanlis_detaylari_tum_dersler:
                    current_ders_data['yanlis_detay_uniteler'] = dict(gruplanmis_yanlis_detaylari_tum_dersler[ders_adi_sirali])

                # Sadece D/Y/B veya yanlış detayı olan dersleri ana listeye ekle
                # VEYA her zaman ekleyip şablonda kontrol edebiliriz. Şimdilik bu kalsın.
                if current_ders_data['dyb_veriler'] or current_ders_data['yanlis_detay_uniteler']:
                    ders_analiz_listesi.append(current_ders_data)
                    
            except Ders.DoesNotExist:
                # Eğer DERS_ADLARI_SIRALI'daki bir ders DB'de yoksa, bu ders için JSON'a boş veri ekle
                analiz_verileri_json_dict[ders_adi_sirali] = [0, 0, 0] # Grafik oluşmaması için
                # Ve ders_analiz_listesi'ne de eklenebilir (isteğe bağlı, sadece "veri yok" mesajı için)
                # current_ders_data['dyb_veriler'] = None 
                # current_ders_data['yanlis_detay_uniteler'] = None
                # ders_analiz_listesi.append(current_ders_data)
                pass # Ya da hiçbir şey yapma, o ders listede görünmez
    
    context = {
        'form': form,
        'ders_analiz_listesi': ders_analiz_listesi,
        'analiz_verileri_json': json.dumps(analiz_verileri_json_dict) if analiz_verileri_json_dict else None,
        'secilen_ogrenci_adi': secilen_ogrenci_adi,
        'ders_etiketleri': json.dumps(["Doğru", "Yanlış", "Boş"]),
        'ogrenci_profili_yok': False 
    }
    
    if ogrenci_nesnesi is None:
        context['ogrenci_profili_yok'] = True

    return render(request, 'sonuclar/ogrenci_analiz_sayfasi.html', context)

def ana_sayfa_view(request):
    context = {} 
    return render(request, 'sonuclar/ana_sayfa.html', context)
