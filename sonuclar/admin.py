from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.db import transaction, IntegrityError # IntegrityError'u import et
from django.contrib.auth.models import User # User modelini import et
from .models import Ders, Ogrenci, Sinav, Sonuc
from .forms import VeriYuklemeFormu
import pandas as pd
import json

# Ders adları ve dosyadaki sütun ön ekleri (Türkçe karakter olmadan)
DERS_BILGILERI = [
    ("Türkçe", "Turkce"),
    ("Matematik", "Matematik"),
    ("Fen Bilimleri", "Fen"),
    ("Sosyal Bilgiler", "Sosyal"),
    ("Yabancı Dil", "Ingilizce"),
    ("Din Kültürü", "Din")
]

class DersAdmin(admin.ModelAdmin):
    list_display = ('ad',)
    search_fields = ('ad',)

class OgrenciAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'kimlik_id', 'get_kullanici_adi', 'get_kullanici_email') # Kullanıcı adını göster
    search_fields = ('ad_soyad', 'kimlik_id', 'user__username') # Kullanıcı adına göre de arama
    list_select_related = ('user',) # User bilgisini çekerken performansı artırır
    readonly_fields = ('user_link',) # Kullanıcı admin sayfasına link (isteğe bağlı)

    def get_kullanici_adi(self, obj):
        if obj.user:
            return obj.user.username
        return "Hesap Yok"
    get_kullanici_adi.short_description = "Kullanıcı Adı" # Sütun başlığı
    get_kullanici_adi.admin_order_field = 'user__username'

    def get_kullanici_email(self, obj):
        if obj.user:
            return obj.user.email
        return "-"
    get_kullanici_email.short_description = "E-posta"
    get_kullanici_email.admin_order_field = 'user__email'
    
    # İsteğe bağlı: Kullanıcı düzenleme sayfasına link
    # from django.utils.html import format_html
    # from django.urls import reverse
    # def user_link(self, obj):
    #     if obj.user:
    #         link = reverse("admin:auth_user_change", args=[obj.user.id])
    #         return format_html('<a href="{}">{}</a>', link, obj.user.username)
    #     return "N/A"
    # user_link.short_description = 'User Account'


class SinavAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tarih')
    search_fields = ('ad',)
    list_filter = ('tarih',)
    ordering = ['-tarih', 'ad']

class SonucAdmin(admin.ModelAdmin):
    list_display = ('get_ogrenci_kimlik', 'get_ogrenci_ad_soyad', 'sinav', 'ders', 'dogru_sayisi', 'yanlis_sayisi', 'bos_sayisi', 'net_puan')
    list_filter = ('sinav', 'ders', 'ogrenci__user__is_active') # Aktif kullanıcılara göre filtreleme eklenebilir
    search_fields = ('ogrenci__ad_soyad', 'ogrenci__kimlik_id', 'ogrenci__user__username', 'ders__ad', 'sinav__ad')
    list_select_related = ('ogrenci', 'sinav', 'ders', 'ogrenci__user')
    ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad']


    def get_ogrenci_ad_soyad(self, obj):
        return obj.ogrenci.ad_soyad
    get_ogrenci_ad_soyad.short_description = 'Öğrenci Adı Soyadı'
    get_ogrenci_ad_soyad.admin_order_field = 'ogrenci__ad_soyad'

    def get_ogrenci_kimlik(self, obj):
        return obj.ogrenci.kimlik_id
    get_ogrenci_kimlik.short_description = 'Öğrenci Kimlik ID'
    get_ogrenci_kimlik.admin_order_field = 'ogrenci__kimlik_id'

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

                df = None
                try:
                    if dosya_adi.endswith('.xlsx'):
                        df = pd.read_excel(yuklenen_dosya, dtype=str) # Tüm sütunları string olarak oku, sonra dönüştür
                    elif dosya_adi.endswith('.json'):
                        try:
                            data = json.load(yuklenen_dosya)
                            df = pd.DataFrame(data, dtype=str) # Tüm sütunları string olarak oku
                        except json.JSONDecodeError:
                            self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR)
                            return redirect("..")
                        except Exception as e:
                            self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR)
                            return redirect("..")
                    else:
                        self.message_user(request, "Desteklenmeyen dosya formatı. Lütfen .xlsx veya .json uzantılı bir dosya yükleyin.", messages.ERROR)
                        return redirect("..")

                    if df is None or df.empty:
                         self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR)
                         return redirect("..")

                    temel_sutunlar = ['Ogrenci_Kimlik_ID', 'Ogrenci_Ad_Soyad']
                    gerekli_sutunlar = list(temel_sutunlar)
                    for _, sutun_oneki in DERS_BILGILERI:
                        gerekli_sutunlar.extend([
                            f"{sutun_oneki}_Dogru", f"{sutun_oneki}_Yanlis", f"{sutun_oneki}_Bos"
                        ])
                    
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar if sutun not in df.columns]
                    if eksik_sutunlar:
                        self.message_user(request, f"Dosyada eksik sütunlar var: {', '.join(eksik_sutunlar)}. Lütfen dosya formatını kontrol edin.", messages.ERROR)
                        return redirect("..")
                    
                    kaydedilen_sonuc_sayisi = 0
                    olusturulan_kullanici_sayisi = 0
                    hatali_satir_bilgileri = []

                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                ogrenci_kimlik = str(row.get('Ogrenci_Kimlik_ID', '')).strip()
                                ogrenci_ad_soyad = str(row.get('Ogrenci_Ad_Soyad', '')).strip()

                                if not ogrenci_kimlik or not ogrenci_ad_soyad:
                                    hatali_satir_bilgileri.append(f"{index+2}. satır: Öğrenci Kimlik ID veya Ad Soyad boş.")
                                    continue
                                
                                # Öğrenciyi al veya oluştur
                                ogrenci, created_ogrenci = Ogrenci.objects.get_or_create(
                                    kimlik_id=ogrenci_kimlik,
                                    defaults={'ad_soyad': ogrenci_ad_soyad}
                                )
                                if not created_ogrenci and ogrenci.ad_soyad != ogrenci_ad_soyad:
                                    ogrenci.ad_soyad = ogrenci_ad_soyad
                                    ogrenci.save(update_fields=['ad_soyad'])

                                # --- User Hesabı Oluşturma/Bağlama Başlangıcı ---
                                if not ogrenci.user:
                                    try:
                                        # Önce bu kimlik_id ile bir User var mı diye bak (farklı bir senaryoda oluşmuş olabilir)
                                        existing_user = User.objects.filter(username=ogrenci_kimlik).first()
                                        if existing_user:
                                            ogrenci.user = existing_user
                                        else:
                                            # UYARI: Şifre olarak kimlik_id kullanılıyor. Bu GÜVENLİ DEĞİLDİR!
                                            # Gerçek bir uygulamada daha güvenli bir yöntem kullanılmalıdır.
                                            # Örneğin, rastgele şifre üretip e-posta ile gönderme veya ilk girişte şifre belirletme.
                                            user_password = ogrenci_kimlik # Basitlik adına
                                            new_user = User.objects.create_user(username=ogrenci_kimlik, password=user_password)
                                            ogrenci.user = new_user
                                            olusturulan_kullanici_sayisi += 1
                                        ogrenci.save(update_fields=['user'])
                                    except IntegrityError: # Kullanıcı adı zaten varsa (çok nadir bir durum olmalı)
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}): Kullanıcı hesabı oluşturulurken/bağlanırken bir sorun oluştu (IntegrityError).")
                                        continue # Bu öğrencinin sonuçlarını işlemeyi atla
                                    except Exception as e_user:
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}): Kullanıcı hesabı hatası: {e_user}")
                                        continue
                                # --- User Hesabı Oluşturma/Bağlama Sonu ---

                                for ders_gosterim_adi, ders_sutun_oneki in DERS_BILGILERI:
                                    try:
                                        dogru_sutun = f"{ders_sutun_oneki}_Dogru"
                                        yanlis_sutun = f"{ders_sutun_oneki}_Yanlis"
                                        bos_sutun = f"{ders_sutun_oneki}_Bos"

                                        # pd.to_numeric ile sayıya çevir, hatalıysa NaN olur
                                        dogru_val = pd.to_numeric(row.get(dogru_sutun), errors='coerce')
                                        yanlis_val = pd.to_numeric(row.get(yanlis_sutun), errors='coerce')
                                        bos_val = pd.to_numeric(row.get(bos_sutun), errors='coerce')

                                        # NaN (Not a Number) değerlerini 0 olarak kabul et
                                        dogru = int(dogru_val) if pd.notna(dogru_val) else 0
                                        yanlis = int(yanlis_val) if pd.notna(yanlis_val) else 0
                                        bos = int(bos_val) if pd.notna(bos_val) else 0
                                        
                                        ders_obj, _ = Ders.objects.get_or_create(ad=ders_gosterim_adi)
                                        net_puan = dogru - (yanlis / YANLIS_KATSAYISI)

                                        Sonuc.objects.update_or_create(
                                            ogrenci=ogrenci, sinav=secilen_sinav, ders=ders_obj,
                                            defaults={
                                                'dogru_sayisi': dogru, 'yanlis_sayisi': yanlis,
                                                'bos_sayisi': bos, 'net_puan': net_puan
                                            }
                                        )
                                        kaydedilen_sonuc_sayisi += 1
                                    except Exception as e_ders: # Ders bazlı hatalar
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}), {ders_gosterim_adi} dersi: {e_ders}")
                            
                            except Exception as e_ogrenci: # Öğrenci bazlı genel hatalar
                                hatali_satir_bilgileri.append(f"{index+2}. satır işlenirken genel hata: {e_ogrenci}")
                    
                    if kaydedilen_sonuc_sayisi > 0:
                        self.message_user(request, f"Toplam {kaydedilen_sonuc_sayisi} adet ders sonucu başarıyla işlendi.", messages.SUCCESS)
                    if olusturulan_kullanici_sayisi > 0:
                        self.message_user(request, f"{olusturulan_kullanici_sayisi} yeni öğrenci için kullanıcı hesabı oluşturuldu. (Şifreleri kimlik ID'leri ile aynıdır, GÜVENLİ DEĞİLDİR!)", messages.INFO)
                    if hatali_satir_bilgileri:
                        hata_ozeti = f"{len(hatali_satir_bilgileri)} satırda/derste hata oluştu. İlk 5 hata: " + "; ".join(hatali_satir_bilgileri[:5])
                        self.message_user(request, hata_ozeti, messages.WARNING)
                    if kaydedilen_sonuc_sayisi == 0 and not hatali_satir_bilgileri:
                         self.message_user(request, "Dosyada işlenecek geçerli veri bulunamadı.", messages.INFO)
                    
                    return redirect("..")

                except pd.errors.EmptyDataError:
                    self.message_user(request, "Yüklenen dosya boş veya okunamıyor.", messages.ERROR)
                except Exception as e:
                    self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata oluştu: {e}", messages.ERROR)
                return redirect("..") # Hata durumunda da formu gösteren sayfaya dön
            else: # Form geçerli değilse
                self.message_user(request, "Formda hatalar var. Lütfen kontrol edin.", messages.ERROR)
        else: # GET isteği ise
            form = VeriYuklemeFormu()

        context = {
            'title': 'Sınav Sonuç Verilerini Yükle (Geniş Format)', 'form': form,
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
