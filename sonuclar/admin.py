from django.contrib import admin, messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from .models import Ders, Ogrenci, Sinav, Sonuc, Konu, OgrenciYanlisDetayi
from .forms import (
    VeriYuklemeFormu, YanlisDetayYuklemeFormu, 
    KonuKazanımYuklemeFormu, GenelYanlisDetayYuklemeFormu # Yeni formu import et
)
import pandas as pd
import json

DERS_BILGILERI = [
    ("Türkçe", "Turkce"),("Matematik", "Matematik"), ("Fen Bilimleri", "Fen"),
    ("Sosyal Bilgiler", "Sosyal"), ("Yabancı Dil", "Ingilizce"), ("Din Kültürü", "Din")
]

class DersAdmin(admin.ModelAdmin):
    list_display = ('ad',); search_fields = ('ad',); ordering = ['ad']

class OgrenciAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'kimlik_id', 'get_kullanici_adi')
    search_fields = ('ad_soyad', 'kimlik_id', 'user__username')
    list_select_related = ('user',); ordering = ['ad_soyad']
    def get_kullanici_adi(self, obj):
        return obj.user.username if obj.user else "Hesap Yok"
    get_kullanici_adi.short_description = "Kullanıcı Adı"
    get_kullanici_adi.admin_order_field = 'user__username'

class KonuAdmin(admin.ModelAdmin):
    list_display = ('ders', 'unite_adi', 'konu_adi'); list_filter = ('ders', 'unite_adi')
    search_fields = ('ders__ad', 'unite_adi', 'konu_adi'); ordering = ['ders__ad', 'unite_adi', 'konu_adi']
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path('toplu-konu-kazanim-yukle/', self.admin_site.admin_view(self.konu_kazanim_yukle_view), name='sonuclar_konu_toplu_yukle')]
        return custom_urls + urls
    def konu_kazanim_yukle_view(self, request):
        # ... (Bu fonksiyonun içeriği bir önceki adımdaki gibi kalır) ...
        if request.method == 'POST':
            form = KonuKazanımYuklemeFormu(request.POST, request.FILES)
            if form.is_valid():
                konu_dosyasi = form.cleaned_data['konu_dosyasi']; dosya_adi = konu_dosyasi.name.lower()
                df = None
                try:
                    if dosya_adi.endswith('.xlsx'): df = pd.read_excel(konu_dosyasi, dtype=str)
                    elif dosya_adi.endswith('.json'):
                        try: data = json.load(konu_dosyasi); df = pd.DataFrame(data, dtype=str)
                        except json.JSONDecodeError: self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
                        except Exception as e: self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
                    else: self.message_user(request, "Desteklenmeyen dosya formatı.", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
                    if df is None or df.empty: self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
                    gerekli_sutunlar_konu = ['Ders_Adi', 'Unite_Adi', 'Konu_Adi_Kazanım_Adi']
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar_konu if sutun not in df.columns]
                    if eksik_sutunlar: self.message_user(request, f"Konu/Kazanım dosyasında eksik sütunlar var: {', '.join(eksik_sutunlar)}.", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
                    kaydedilen_konu_sayisi = 0; olusturulan_ders_sayisi = 0; hatali_konu_satirlari = []
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                ders_adi = str(row.get('Ders_Adi', '')).strip(); unite_adi = str(row.get('Unite_Adi', '')).strip(); konu_kazanim_adi = str(row.get('Konu_Adi_Kazanım_Adi', '')).strip()
                                if not all([ders_adi, unite_adi, konu_kazanim_adi]): hatali_konu_satirlari.append(f"{index+2}. satır: Gerekli alanlardan (Ders, Ünite, Konu) biri boş."); continue
                                ders_obj, created_ders = Ders.objects.get_or_create(ad__iexact=ders_adi, defaults={'ad': ders_adi})
                                if created_ders: olusturulan_ders_sayisi += 1
                                konu_obj, created_konu = Konu.objects.get_or_create(ders=ders_obj, unite_adi=unite_adi, konu_adi=konu_kazanim_adi)
                                if created_konu: kaydedilen_konu_sayisi += 1
                            except Exception as e_konu: hatali_konu_satirlari.append(f"{index+2}. satır işlenirken hata: {e_konu}")
                    if kaydedilen_konu_sayisi > 0: self.message_user(request, f"{kaydedilen_konu_sayisi} yeni konu/kazanım başarıyla eklendi.", messages.SUCCESS)
                    if olusturulan_ders_sayisi > 0: self.message_user(request, f"{olusturulan_ders_sayisi} yeni ders otomatik olarak oluşturuldu.", messages.INFO)
                    if hatali_konu_satirlari: self.message_user(request, f"{len(hatali_konu_satirlari)} satırda hata oluştu. İlk 3 hata: {'; '.join(hatali_konu_satirlari[:3])}", messages.WARNING)
                    if kaydedilen_konu_sayisi == 0 and olusturulan_ders_sayisi == 0 and not hatali_konu_satirlari: self.message_user(request, "Dosyada işlenecek yeni konu/kazanım bulunamadı veya tümü zaten mevcuttu.", messages.INFO)
                    return redirect(reverse('admin:sonuclar_konu_changelist'))
                except Exception as e: self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata oluştu: {e}", messages.ERROR); return redirect(reverse('admin:sonuclar_konu_changelist'))
            else: self.message_user(request, "Formda hatalar var. Lütfen kontrol edin.", messages.ERROR)
        else: form = KonuKazanımYuklemeFormu()
        context = {'title': 'Toplu Konu/Kazanım Yükle', 'form': form, 'opts': Konu._meta, 'has_view_permission': self.has_view_permission(request, None), 'has_add_permission': self.has_add_permission(request), 'has_change_permission': self.has_change_permission(request, None), 'has_delete_permission': self.has_delete_permission(request, None)}
        return render(request, 'admin/sonuclar/konu/konu_kazanim_yukleme_formu.html', context)

class OgrenciYanlisDetayiAdmin(admin.ModelAdmin):
    list_display = ('get_ogrenci_ad_soyad', 'sinav', 'ders', 'get_konu_bilgisi', 'yanlis_adedi')
    list_filter = ('sinav', 'ders', 'konu__unite_adi', 'ogrenci')
    search_fields = ('ogrenci__ad_soyad', 'ogrenci__kimlik_id', 'sinav__ad', 'ders__ad', 'konu__konu_adi')
    list_select_related = ('ogrenci', 'sinav', 'ders', 'konu', 'konu__ders')
    ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad']

    def get_ogrenci_ad_soyad(self, obj): return obj.ogrenci.ad_soyad
    get_ogrenci_ad_soyad.short_description = 'Öğrenci'
    get_ogrenci_ad_soyad.admin_order_field = 'ogrenci__ad_soyad'

    def get_konu_bilgisi(self, obj): return f"{obj.konu.unite_adi} - {obj.konu.konu_adi}"
    get_konu_bilgisi.short_description = 'Konu/Kazanım'
    get_konu_bilgisi.admin_order_field = 'konu__konu_adi'

    # --- YENİ EKLENEN KISIMLAR (Genel Toplu Yanlış Detayı Yükleme) ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toplu-yanlis-detay-yukle/', 
                 self.admin_site.admin_view(self.toplu_yanlis_detay_yukle_view), 
                 name='sonuclar_ogrenciyanlisdetayi_toplu_yukle'), # URL adı güncellendi
        ]
        return custom_urls + urls

    def toplu_yanlis_detay_yukle_view(self, request):
        if request.method == 'POST':
            form = GenelYanlisDetayYuklemeFormu(request.POST, request.FILES)
            if form.is_valid():
                excel_dosyasi = form.cleaned_data['yanlis_detay_excel_dosyasi']
                dosya_adi = excel_dosyasi.name.lower()
                df = None
                try:
                    if dosya_adi.endswith('.xlsx'): df = pd.read_excel(excel_dosyasi, dtype=str)
                    elif dosya_adi.endswith('.json'):
                        try: data = json.load(excel_dosyasi); df = pd.DataFrame(data, dtype=str)
                        except json.JSONDecodeError: self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))
                        except Exception as e: self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))
                    else: self.message_user(request, "Desteklenmeyen dosya formatı.", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))
                    
                    if df is None or df.empty: self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))

                    # Sütun adları: Ogrenci_Kimlik_ID, Sinav_Adi, Ders_Adi, Unite_Adi, Konu_Adi_Kazanım_Adi, Yanlis_Adedi_Bu_Konuda
                    gerekli_sutunlar = ['Ogrenci_Kimlik_ID', 'Sinav_Adi', 'Ders_Adi', 'Unite_Adi', 'Konu_Adi_Kazanım_Adi', 'Yanlis_Adedi_Bu_Konuda']
                    df.rename(columns={'Konu_Adi/Kazanım_Adi': 'Konu_Adi_Kazanım_Adi'}, inplace=True) # Sütun adı düzeltmesi
                    
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar if sutun not in df.columns]
                    if eksik_sutunlar: self.message_user(request, f"Yanlış detayları Excel dosyasında eksik sütunlar var: {', '.join(eksik_sutunlar)}.", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))

                    kaydedilen_adet = 0; hatali_satirlar = []
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                ogrenci_kimlik = str(row.get('Ogrenci_Kimlik_ID', '')).strip()
                                sinav_adi = str(row.get('Sinav_Adi', '')).strip()
                                ders_adi_str = str(row.get('Ders_Adi', '')).strip()
                                unite_adi_str = str(row.get('Unite_Adi', '')).strip()
                                konu_adi_str = str(row.get('Konu_Adi_Kazanım_Adi', '')).strip()
                                yanlis_adedi_str = str(row.get('Yanlis_Adedi_Bu_Konuda', '')).strip()

                                if not all([ogrenci_kimlik, sinav_adi, ders_adi_str, unite_adi_str, konu_adi_str, yanlis_adedi_str]):
                                    hatali_satirlar.append(f"{index+2}. satır: Gerekli alanlardan biri boş."); continue
                                
                                if ogrenci_kimlik.isdigit(): ogrenci_kimlik_std = str(int(ogrenci_kimlik))
                                else: ogrenci_kimlik_std = ogrenci_kimlik

                                try: ogrenci = Ogrenci.objects.get(kimlik_id=ogrenci_kimlik_std)
                                except Ogrenci.DoesNotExist: hatali_satirlar.append(f"{index+2}. satır: Öğrenci ({ogrenci_kimlik_std}) bulunamadı."); continue
                                
                                try: sinav_obj = Sinav.objects.get(ad__iexact=sinav_adi)
                                except Sinav.DoesNotExist: sinav_obj = Sinav.objects.create(ad=sinav_adi); self.message_user(request, f"'{sinav_adi}' adlı yeni sınav oluşturuldu.", messages.INFO)
                                
                                try: ders_obj = Ders.objects.get(ad__iexact=ders_adi_str)
                                except Ders.DoesNotExist: ders_obj = Ders.objects.create(ad=ders_adi_str); self.message_user(request, f"'{ders_adi_str}' adlı yeni ders oluşturuldu.", messages.INFO)

                                konu_obj, _ = Konu.objects.get_or_create(ders=ders_obj, unite_adi=unite_adi_str, konu_adi=konu_adi_str)
                                yanlis_adedi = int(yanlis_adedi_str)

                                OgrenciYanlisDetayi.objects.update_or_create(
                                    ogrenci=ogrenci, sinav=sinav_obj, konu=konu_obj,
                                    defaults={'ders': ders_obj, 'yanlis_adedi': yanlis_adedi}
                                )
                                kaydedilen_adet += 1
                            except ValueError: hatali_satirlar.append(f"{index+2}. satır: 'Yanlis_Adedi_Bu_Konuda' sayısal olmalı.")
                            except Exception as e_islem: hatali_satirlar.append(f"{index+2}. satır işlenirken hata: {e_islem}")
                    
                    if kaydedilen_adet > 0: self.message_user(request, f"{kaydedilen_adet} adet öğrenci yanlış detayı başarıyla işlendi/güncellendi.", messages.SUCCESS)
                    if hatali_satirlar: self.message_user(request, f"{len(hatali_satirlar)} satırda hata oluştu. İlk 3 hata: {'; '.join(hatali_satirlar[:3])}", messages.WARNING)
                    return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))
                except Exception as e_dosya: self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata: {e_dosya}", messages.ERROR); return redirect(reverse('admin:sonuclar_ogrenciyanlisdetayi_changelist'))
            else: self.message_user(request, "Formda hatalar var.", messages.ERROR)
        else: form = GenelYanlisDetayYuklemeFormu()
        context = {'title': 'Toplu Öğrenci Yanlış Detayı Yükle', 'form': form, 'opts': OgrenciYanlisDetayi._meta}
        return render(request, 'admin/sonuclar/ogrenciyanlisdetayi/toplu_yanlis_detay_yukleme_formu.html', context)
    # --- YENİ EKLENEN KISIMLAR BİTTİ ---

class SinavAdmin(admin.ModelAdmin):
    # ... (Mevcut SinavAdmin içeriği - bir önceki adımdaki gibi) ...
    list_display = ('ad', 'tarih', 'yanlis_detay_yukleme_linki')
    search_fields = ('ad',); list_filter = ('tarih',); ordering = ['-tarih', 'ad']
    def get_urls(self):
        urls = super().get_urls(); custom_urls = [path('<int:sinav_id>/yanlis-detay-yukle/', self.admin_site.admin_view(self.yanlis_detay_yukle_view), name='sonuclar_sinav_yanlis_detay_yukle')]
        return custom_urls + urls
    def yanlis_detay_yukleme_linki(self, obj):
        url = reverse('admin:sonuclar_sinav_yanlis_detay_yukle', args=[obj.pk]); return format_html('<a href="{}">Yanlış Detay Yükle</a>', url)
    yanlis_detay_yukleme_linki.short_description = 'Yanlış Detayları'
    def yanlis_detay_yukle_view(self, request, sinav_id):
        # ... (Bu fonksiyonun içeriği bir önceki adımdaki gibi kalır) ...
        sinav = get_object_or_404(Sinav, pk=sinav_id)
        if request.method == 'POST':
            form = YanlisDetayYuklemeFormu(request.POST, request.FILES) 
            if form.is_valid():
                secilen_sinav = sinav 
                detay_dosyasi = form.cleaned_data['detay_dosyasi']
                dosya_adi = detay_dosyasi.name.lower(); df = None
                try:
                    if dosya_adi.endswith('.xlsx'): df = pd.read_excel(detay_dosyasi, dtype=str)
                    elif dosya_adi.endswith('.json'):
                        try: data = json.load(detay_dosyasi); df = pd.DataFrame(data, dtype=str)
                        except json.JSONDecodeError: self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
                        except Exception as e: self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
                    else: self.message_user(request, "Desteklenmeyen dosya formatı.", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
                    if df is None or df.empty: self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
                    gerekli_sutunlar_detay = ['Ogrenci_Kimlik_ID', 'Ders_Adi', 'Unite_Adi', 'Konu_Adi_Kazanım_Adi', 'Yanlis_Adedi_Bu_Konuda']
                    df.rename(columns={'Konu_Adi/Kazanım_Adi': 'Konu_Adi_Kazanım_Adi'}, inplace=True)
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar_detay if sutun not in df.columns]
                    if eksik_sutunlar: self.message_user(request, f"Yanlış detay dosyasında eksik sütunlar var: {', '.join(eksik_sutunlar)}.", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
                    kaydedilen_detay_sayisi = 0; hatali_detay_satirlari = []
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                ogrenci_kimlik_ham = str(row.get('Ogrenci_Kimlik_ID', '')).strip(); ders_adi_str = str(row.get('Ders_Adi', '')).strip(); unite_adi_str = str(row.get('Unite_Adi', '')).strip(); konu_kazanim_adi_str = str(row.get('Konu_Adi_Kazanım_Adi', '')).strip(); yanlis_adedi_str = str(row.get('Yanlis_Adedi_Bu_Konuda', '')).strip()
                                if not all([ogrenci_kimlik_ham, ders_adi_str, unite_adi_str, konu_kazanim_adi_str, yanlis_adedi_str]): hatali_detay_satirlari.append(f"{index+2}. satır: Gerekli alanlardan biri boş."); continue
                                if ogrenci_kimlik_ham.isdigit(): ogrenci_kimlik_standart = str(int(ogrenci_kimlik_ham))
                                else: ogrenci_kimlik_standart = ogrenci_kimlik_ham
                                try: ogrenci = Ogrenci.objects.get(kimlik_id=ogrenci_kimlik_standart)
                                except Ogrenci.DoesNotExist: hatali_detay_satirlari.append(f"{index+2}. satır: Öğrenci ({ogrenci_kimlik_standart}) bulunamadı."); continue
                                try: ders_obj = Ders.objects.get(ad__iexact=ders_adi_str)
                                except Ders.DoesNotExist: ders_obj = Ders.objects.create(ad=ders_adi_str); self.message_user(request, f"'{ders_adi_str}' adlı yeni ders oluşturuldu.", messages.INFO)
                                konu_obj, _ = Konu.objects.get_or_create(ders=ders_obj, unite_adi=unite_adi_str, konu_adi=konu_kazanim_adi_str)
                                yanlis_adedi = int(yanlis_adedi_str)
                                OgrenciYanlisDetayi.objects.update_or_create(ogrenci=ogrenci, sinav=secilen_sinav, konu=konu_obj, defaults={'ders': ders_obj, 'yanlis_adedi': yanlis_adedi})
                                kaydedilen_detay_sayisi += 1
                            except ValueError: hatali_detay_satirlari.append(f"{index+2}. satır: 'Yanlis_Adedi_Bu_Konuda' sayısal olmalı.")
                            except Exception as e_detay: hatali_detay_satirlari.append(f"{index+2}. satır işlenirken hata: {e_detay}")
                    if kaydedilen_detay_sayisi > 0: self.message_user(request, f"{secilen_sinav.ad} sınavı için {kaydedilen_detay_sayisi} adet yanlış detayı başarıyla işlendi.", messages.SUCCESS)
                    if hatali_detay_satirlari: self.message_user(request, f"{len(hatali_detay_satirlari)} satırda hata oluştu. İlk 3 hata: {'; '.join(hatali_detay_satirlari[:3])}", messages.WARNING)
                    return redirect(reverse('admin:sonuclar_sinav_changelist'))
                except Exception as e: self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata: {e}", messages.ERROR); return redirect(reverse('admin:sonuclar_sinav_changelist'))
            else: self.message_user(request, "Formda hatalar var.", messages.ERROR)
        else: form = YanlisDetayYuklemeFormu()
        context = {'title': f"'{sinav.ad}' Sınavı İçin Yanlış Detaylarını Yükle", 'form': form, 'opts': Sinav._meta, 'sinav': sinav, 'has_view_permission': self.has_view_permission(request, None), 'has_add_permission': self.has_add_permission(request), 'has_change_permission': self.has_change_permission(request, None), 'has_delete_permission': self.has_delete_permission(request, None)}
        return render(request, 'admin/sonuclar/sinav/yanlis_detay_yukleme_formu.html', context)

class SonucAdmin(admin.ModelAdmin):
    # ... (Mevcut SonucAdmin içeriği - bir önceki adımdaki gibi) ...
    list_display = ('get_ogrenci_ad_soyad', 'get_ogrenci_kimlik', 'sinav', 'ders', 'dogru_sayisi', 'yanlis_sayisi', 'bos_sayisi', 'net_puan')
    list_filter = ('sinav', 'ders', 'ogrenci__user__is_active')
    search_fields = ('ogrenci__ad_soyad', 'ogrenci__kimlik_id', 'ogrenci__user__username', 'ders__ad', 'sinav__ad')
    list_select_related = ('ogrenci', 'sinav', 'ders', 'ogrenci__user')
    ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad']
    def get_ogrenci_ad_soyad(self, obj): return obj.ogrenci.ad_soyad
    get_ogrenci_ad_soyad.short_description = 'Öğrenci Adı Soyadı'
    get_ogrenci_ad_soyad.admin_order_field = 'ogrenci__ad_soyad'
    def get_ogrenci_kimlik(self, obj): return obj.ogrenci.kimlik_id
    get_ogrenci_kimlik.short_description = 'Öğrenci Kimlik ID'
    get_ogrenci_kimlik.admin_order_field = 'ogrenci__kimlik_id'
    def get_urls(self): urls = super().get_urls(); custom_urls = [path('veri-yukle/', self.admin_site.admin_view(self.veri_yukle_view), name='sonuclar_sonuc_veri_yukle')]; return custom_urls + urls
    def veri_yukle_view(self, request):
        # ... (Mevcut veri_yukle_view içeriği - bir önceki adımdaki gibi) ...
        if request.method == 'POST':
            form = VeriYuklemeFormu(request.POST, request.FILES)
            if form.is_valid():
                secilen_sinav = form.cleaned_data['sinav']; yuklenen_dosya = form.cleaned_data['dosya']; dosya_adi = yuklenen_dosya.name.lower(); YANLIS_KATSAYISI = 4
                df = None
                try:
                    if dosya_adi.endswith('.xlsx'): df = pd.read_excel(yuklenen_dosya, dtype=str)
                    elif dosya_adi.endswith('.json'):
                        try: data = json.load(yuklenen_dosya); df = pd.DataFrame(data, dtype=str)
                        except json.JSONDecodeError: self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR); return redirect("..")
                        except Exception as e: self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR); return redirect("..")
                    else: self.message_user(request, "Desteklenmeyen dosya formatı.", messages.ERROR); return redirect("..")
                    if df is None or df.empty: self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR); return redirect("..")
                    temel_sutunlar = ['Ogrenci_Kimlik_ID', 'Ogrenci_Ad_Soyad']; gerekli_sutunlar_genel = list(temel_sutunlar) 
                    for _, sutun_oneki in DERS_BILGILERI: gerekli_sutunlar_genel.extend([f"{sutun_oneki}_Dogru", f"{sutun_oneki}_Yanlis", f"{sutun_oneki}_Bos"])
                    eksik_sutunlar = [sutun for sutun in gerekli_sutunlar_genel if sutun not in df.columns]
                    if eksik_sutunlar: self.message_user(request, f"Genel sonuç dosyasında eksik sütunlar var: {', '.join(eksik_sutunlar)}.", messages.ERROR); return redirect("..")
                    kaydedilen_sonuc_sayisi = 0; olusturulan_kullanici_sayisi = 0; guncellenen_ogrenci_adi_sayisi = 0; hatali_satir_bilgileri = []
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                ogrenci_kimlik_ham = str(row.get('Ogrenci_Kimlik_ID', '')).strip(); ogrenci_ad_soyad = str(row.get('Ogrenci_Ad_Soyad', '')).strip()
                                if ogrenci_kimlik_ham.isdigit(): ogrenci_kimlik_standart = str(int(ogrenci_kimlik_ham)) 
                                else: ogrenci_kimlik_standart = ogrenci_kimlik_ham
                                if not ogrenci_kimlik_standart or not ogrenci_ad_soyad: hatali_satir_bilgileri.append(f"{index+2}. satır: Öğrenci Kimlik ID veya Ad Soyad boş/geçersiz."); continue
                                ogrenci, created_ogrenci = Ogrenci.objects.get_or_create(kimlik_id=ogrenci_kimlik_standart, defaults={'ad_soyad': ogrenci_ad_soyad})
                                if not created_ogrenci and ogrenci.ad_soyad.strip().lower() != ogrenci_ad_soyad.strip().lower(): ogrenci.ad_soyad = ogrenci_ad_soyad; ogrenci.save(update_fields=['ad_soyad']); guncellenen_ogrenci_adi_sayisi +=1
                                if not ogrenci.user:
                                    try:
                                        user_username = ogrenci_kimlik_standart; existing_user = User.objects.filter(username=user_username).first()
                                        if existing_user: ogrenci.user = existing_user
                                        else: user_password = user_username; new_user = User.objects.create_user(username=user_username, password=user_password); ogrenci.user = new_user; olusturulan_kullanici_sayisi += 1
                                        ogrenci.save(update_fields=['user'])
                                    except IntegrityError: hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik_standart}): Kullanıcı adı zaten mevcut, hesap bağlanamadı."); continue
                                    except Exception as e_user: hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik_standart}): Kullanıcı hesabı hatası: {e_user}"); continue
                                for ders_gosterim_adi, ders_sutun_oneki in DERS_BILGILERI:
                                    try:
                                        dogru_sutun = f"{sutun_oneki}_Dogru"; yanlis_sutun = f"{sutun_oneki}_Yanlis"; bos_sutun = f"{sutun_oneki}_Bos"
                                        dogru_val = pd.to_numeric(row.get(dogru_sutun), errors='coerce'); yanlis_val = pd.to_numeric(row.get(yanlis_sutun), errors='coerce'); bos_val = pd.to_numeric(row.get(bos_sutun), errors='coerce')
                                        dogru = int(dogru_val) if pd.notna(dogru_val) else 0; yanlis = int(yanlis_val) if pd.notna(yanlis_val) else 0; bos = int(bos_val) if pd.notna(bos_val) else 0
                                        ders_obj_genel, _ = Ders.objects.get_or_create(ad=ders_gosterim_adi); net_puan = dogru - (yanlis / YANLIS_KATSAYISI)
                                        Sonuc.objects.update_or_create(ogrenci=ogrenci, sinav=secilen_sinav, ders=ders_obj_genel, defaults={'dogru_sayisi': dogru, 'yanlis_sayisi': yanlis, 'bos_sayisi': bos, 'net_puan': net_puan})
                                        kaydedilen_sonuc_sayisi += 1
                                    except Exception as e_ders: hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik_standart}), {ders_gosterim_adi} dersi: {e_ders}")
                            except Exception as e_ogrenci: hatali_satir_bilgileri.append(f"{index+2}. satır işlenirken genel hata: {e_ogrenci}")
                    if kaydedilen_sonuc_sayisi > 0: self.message_user(request, f"Toplam {kaydedilen_sonuc_sayisi} adet genel ders sonucu başarıyla işlendi.", messages.SUCCESS)
                    if olusturulan_kullanici_sayisi > 0: self.message_user(request, f"{olusturulan_kullanici_sayisi} yeni öğrenci için kullanıcı hesabı oluşturuldu.", messages.INFO)
                    if guncellenen_ogrenci_adi_sayisi > 0: self.message_user(request, f"{guncellenen_ogrenci_adi_sayisi} öğrencinin adı güncellendi.", messages.INFO)
                    if hatali_satir_bilgileri: self.message_user(request, f"{len(hatali_satir_bilgileri)} satırda/derste hata oluştu. İlk 5 hata: {'; '.join(hatali_satir_bilgileri[:5])}", messages.WARNING)
                    if kaydedilen_sonuc_sayisi == 0 and not hatali_satir_bilgileri: self.message_user(request, "Genel sonuç dosyasında işlenecek geçerli veri bulunamadı.", messages.INFO)
                    return redirect("..")
                except pd.errors.EmptyDataError: self.message_user(request, "Yüklenen genel sonuç dosyası boş veya okunamıyor.", messages.ERROR)
                except Exception as e: self.message_user(request, f"Genel sonuç dosyası okunurken veya işlenirken genel bir hata oluştu: {e}", messages.ERROR)
                return redirect("..")
            else: self.message_user(request, "Genel sonuç formu hatalı. Lütfen kontrol edin.", messages.ERROR)
        else: form = VeriYuklemeFormu()
        context = {'title': 'Genel Sınav Sonuçlarını Yükle (D/Y/B)', 'form': form, 'opts': Sonuc._meta, 'has_view_permission': self.has_view_permission(request, None), 'has_add_permission': self.has_add_permission(request), 'has_change_permission': self.has_change_permission(request, None), 'has_delete_permission': self.has_delete_permission(request, None), 'has_editable_inline_admin_formsets': False}
        return render(request, 'admin/sonuclar/sonuc/veri_yukleme_formu.html', context)

admin.site.register(Ders, DersAdmin)
admin.site.register(Ogrenci, OgrenciAdmin)
admin.site.register(Sinav, SinavAdmin)
admin.site.register(Sonuc, SonucAdmin)
admin.site.register(Konu, KonuAdmin)
admin.site.register(OgrenciYanlisDetayi, OgrenciYanlisDetayiAdmin) # Güncellenmiş OgrenciYanlisDetayiAdmin'i kaydet
