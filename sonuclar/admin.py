from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.db import transaction # Atomik işlemler için
from .models import Ders, Ogrenci, Sinav, Sonuc
from .forms import VeriYuklemeFormu
import pandas as pd
import json # JSON işlemek için

# Ders adları ve dosyadaki sütun ön ekleri (Türkçe karakter olmadan)
# Bu liste, işlenecek dersleri ve dosyadaki karşılık gelen sütun adlarını belirler.
# Gösterim Adı (DB'ye kaydedilecek), Sütun Ön Eki (Dosyada)
DERS_BILGILERI = [
    ("Türkçe", "Turkce"),
    ("Matematik", "Matematik"),
    ("Fen Bilimleri", "Fen"), # Dosyada "Fen_Dogru" vb. olacak
    ("Sosyal Bilgiler", "Sosyal"), # Dosyada "Sosyal_Dogru" vb. olacak
    ("Yabancı Dil", "Ingilizce"), # Dosyada "Ingilizce_Dogru" vb. olacak
    ("Din Kültürü", "Din") # Dosyada "Din_Dogru" vb. olacak
]

# --- Ders, Ogrenci, Sinav Admin sınıfları aynı kalacak ---
class DersAdmin(admin.ModelAdmin):
    list_display = ('ad',)
    search_fields = ('ad',)

class OgrenciAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'kimlik_id')
    search_fields = ('ad_soyad', 'kimlik_id')

class SinavAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tarih')
    search_fields = ('ad',)
    list_filter = ('tarih',)

class SonucAdmin(admin.ModelAdmin):
    list_display = ('get_ogrenci_kimlik', 'get_ogrenci_ad_soyad', 'sinav', 'ders', 'dogru_sayisi', 'yanlis_sayisi', 'bos_sayisi', 'net_puan')
    list_filter = ('sinav', 'ders')
    search_fields = ('ogrenci__ad_soyad', 'ogrenci__kimlik_id', 'ders__ad', 'sinav__ad')
    list_select_related = ('ogrenci', 'sinav', 'ders')

    def get_ogrenci_ad_soyad(self, obj):
        return obj.ogrenci.ad_soyad
    get_ogrenci_ad_soyad.short_description = 'Öğrenci Adı Soyadı' # Admin panelindeki sütun başlığı
    get_ogrenci_ad_soyad.admin_order_field = 'ogrenci__ad_soyad' # Bu alana göre sıralama

    def get_ogrenci_kimlik(self, obj):
        return obj.ogrenci.kimlik_id
    get_ogrenci_kimlik.short_description = 'Öğrenci Kimlik ID' # Admin panelindeki sütun başlığı
    get_ogrenci_kimlik.admin_order_field = 'ogrenci__kimlik_id' # Bu alana göre sıralama

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('veri-yukle/', self.admin_site.admin_view(self.veri_yukle_view), name='sonuclar_sonuc_veri_yukle'),
        ]
        return custom_urls + urls

    def veri_yukle_view(self, request):
        if request.method == 'POST':
            form = VeriYuklemeFormu(request.POST, request.FILES)
            if form.is_valid():
                secilen_sinav = form.cleaned_data['sinav']
                yuklenen_dosya = form.cleaned_data['dosya']
                dosya_adi = yuklenen_dosya.name.lower()

                YANLIS_KATSAYISI = 4

                try:
                    df = None
                    if dosya_adi.endswith('.xlsx'):
                        df = pd.read_excel(yuklenen_dosya)
                    elif dosya_adi.endswith('.json'):
                        try:
                            data = json.load(yuklenen_dosya)
                            df = pd.DataFrame(data)
                        except json.JSONDecodeError:
                            self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR)
                            return redirect("..")
                        except Exception as e:
                            self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR)
                            return redirect("..")
                    else:
                        self.message_user(request, "Desteklenmeyen dosya formatı. Lütfen .xlsx veya .json uzantılı bir dosya yükleyin.", messages.ERROR)
                        return redirect("..")

                    if df is None or df.empty: # df.empty kontrolü eklendi
                         self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR)
                         return redirect("..")

                    # Gerekli temel sütunlar
                    temel_sutunlar = ['Ogrenci_Kimlik_ID', 'Ogrenci_Ad_Soyad']
                    gerekli_sutunlar = list(temel_sutunlar) # Kopyasını alarak başla

                    # Derslere ait sütunları da gerekli listeye ekle
                    for _, sutun_oneki in DERS_BILGILERI:
                        gerekli_sutunlar.extend([
                            f"{sutun_oneki}_Dogru",
                            f"{sutun_oneki}_Yanlis",
                            f"{sutun_oneki}_Bos"
                        ])
                    
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar if sutun not in df.columns]
                    if eksik_sutunlar:
                        self.message_user(request, f"Dosyada eksik sütunlar var: {', '.join(eksik_sutunlar)}. Lütfen dosya formatını kontrol edin.", messages.ERROR)
                        return redirect("..")
                    
                    kaydedilen_sayisi = 0
                    hatali_ogrenci_sayisi = 0
                    hata_mesajlari_liste = [] # Hata mesajlarını toplamak için liste

                    with transaction.atomic():
                        for index, row in df.iterrows(): # Her satır bir öğrenciyi temsil eder
                            try:
                                ogrenci_kimlik = str(row['Ogrenci_Kimlik_ID']).strip()
                                ogrenci_ad_soyad = str(row['Ogrenci_Ad_Soyad']).strip()

                                if not ogrenci_kimlik or not ogrenci_ad_soyad:
                                    hata_mesajlari_liste.append(f"{index+2}. satırdaki öğrencinin Kimlik ID veya Ad Soyad bilgisi eksik.")
                                    hatali_ogrenci_sayisi += 1
                                    continue
                                
                                ogrenci, created_ogrenci = Ogrenci.objects.get_or_create(
                                    kimlik_id=ogrenci_kimlik,
                                    defaults={'ad_soyad': ogrenci_ad_soyad}
                                )
                                if not created_ogrenci and ogrenci.ad_soyad != ogrenci_ad_soyad:
                                    ogrenci.ad_soyad = ogrenci_ad_soyad
                                    ogrenci.save()

                                # Her bir ders için sonuçları işle
                                for ders_gosterim_adi, ders_sutun_oneki in DERS_BILGILERI:
                                    try:
                                        dogru_sutun = f"{ders_sutun_oneki}_Dogru"
                                        yanlis_sutun = f"{ders_sutun_oneki}_Yanlis"
                                        bos_sutun = f"{ders_sutun_oneki}_Bos"

                                        # Sütunların varlığını tekrar kontrol et (her ders için)
                                        # Bu, bazı derslerin eksik olması durumunda hata vermesini engeller,
                                        # ancak o ders için kayıt oluşturulmaz.
                                        if not all(col in row for col in [dogru_sutun, yanlis_sutun, bos_sutun]):
                                            # İsteğe bağlı: Eksik ders bilgisi için uyarı eklenebilir
                                            # hata_mesajlari_liste.append(f"{ogrenci_kimlik} öğrencisi için {ders_gosterim_adi} dersine ait sütunlar eksik.")
                                            continue # Bu dersi atla, sonraki derse geç

                                        # NaN (Not a Number) değerlerini 0 olarak kabul et veya hata ver
                                        dogru_val = row.get(dogru_sutun)
                                        yanlis_val = row.get(yanlis_sutun)
                                        bos_val = row.get(bos_sutun)

                                        # Boş veya NaN ise 0 yap, aksi halde int'e çevir
                                        dogru = int(dogru_val) if pd.notna(dogru_val) else 0
                                        yanlis = int(yanlis_val) if pd.notna(yanlis_val) else 0
                                        bos = int(bos_val) if pd.notna(bos_val) else 0
                                        
                                        ders_obj, _ = Ders.objects.get_or_create(ad=ders_gosterim_adi)
                                        net_puan = dogru - (yanlis / YANLIS_KATSAYISI)

                                        Sonuc.objects.update_or_create(
                                            ogrenci=ogrenci,
                                            sinav=secilen_sinav,
                                            ders=ders_obj,
                                            defaults={
                                                'dogru_sayisi': dogru,
                                                'yanlis_sayisi': yanlis,
                                                'bos_sayisi': bos,
                                                'net_puan': net_puan
                                            }
                                        )
                                        kaydedilen_sayisi += 1 
                                    except ValueError:
                                        hata_mesajlari_liste.append(f"{ogrenci_kimlik} öğrencisi, {ders_gosterim_adi} dersi için sayısal olmayan değer (Doğru, Yanlış, Boş sayıları tam sayı olmalı).")
                                        # Bu ders için hata oluştu, öğrencinin diğer dersleri işlenmeye devam edebilir.
                                    except KeyError as ke: # Belirli bir dersin sütunu hiç yoksa
                                        hata_mesajlari_liste.append(f"{ogrenci_kimlik} öğrencisi, {ders_gosterim_adi} dersi için beklenen sütun bulunamadı: {ke}.")
                                    except Exception as e_ders:
                                        hata_mesajlari_liste.append(f"{ogrenci_kimlik} öğrencisi, {ders_gosterim_adi} dersi işlenirken genel hata: {e_ders}")
                            
                            except Exception as e_ogrenci:
                                hata_mesajlari_liste.append(f"{index+2}. satırdaki öğrenci işlenirken genel hata: {e_ogrenci}")
                                hatali_ogrenci_sayisi += 1
                    
                    if kaydedilen_sayisi > 0:
                        self.message_user(request, f"Toplam {kaydedilen_sayisi} adet ders sonucu başarıyla işlendi ve kaydedildi/güncellendi.", messages.SUCCESS)
                    if hatali_ogrenci_sayisi > 0 or len(hata_mesajlari_liste) > (kaydedilen_sayisi == 0 and hatali_ogrenci_sayisi > 0): # Sadece öğrenci bazlı olmayan hatalar varsa
                        # Eğer sadece ders bazlı hatalar varsa, hatali_ogrenci_sayisi 0 olabilir.
                        unique_error_messages = list(set(hata_mesajlari_liste)) # Tekrarlayan mesajları azalt
                        self.message_user(request, f"{len(unique_error_messages)} farklı hata mesajı oluştu (bazı öğrenciler veya dersler için). İlk 5 detay: {'; '.join(unique_error_messages[:5])}", messages.WARNING)
                    if kaydedilen_sayisi == 0 and hatali_ogrenci_sayisi == 0 and not hata_mesajlari_liste:
                         self.message_user(request, "Dosyada işlenecek geçerli veri bulunamadı veya tüm satırlar hatalıydı.", messages.INFO)
                    
                    return redirect("..")

                except pd.errors.EmptyDataError:
                    self.message_user(request, "Yüklenen dosya boş veya okunamıyor.", messages.ERROR)
                    return redirect("..")
                except Exception as e:
                    self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata oluştu: {e}", messages.ERROR)
                    return redirect("..")
            else:
                self.message_user(request, "Formda hatalar var. Lütfen kontrol edin.", messages.ERROR)
        else:
            form = VeriYuklemeFormu()

        context = {
            'title': 'Sınav Sonuç Verilerini Yükle (Geniş Format)',
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, None),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, None),
            'has_delete_permission': self.has_delete_permission(request, None),
            'has_editable_inline_admin_formsets': False,
        }
        return render(request, 'admin/sonuclar/sonuc/veri_yukleme_formu.html', context)

admin.site.register(Ders, DersAdmin)
admin.site.register(Ogrenci, OgrenciAdmin)
admin.site.register(Sinav, SinavAdmin)
admin.site.register(Sonuc, SonucAdmin)
