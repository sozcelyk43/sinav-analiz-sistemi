from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.db import transaction, IntegrityError # Veritabanı işlemleri ve hatalar için
from django.contrib.auth.models import User # Django User modeli
from .models import Ders, Ogrenci, Sinav, Sonuc # Uygulama modelleri
from .forms import VeriYuklemeFormu # Veri yükleme formu
import pandas as pd # Veri okuma ve işleme için
import json # JSON dosyaları için

# İşlenecek derslerin adları ve dosyadaki sütun adları için kullanılacak ön ekler
# Önemli: Dosyanızdaki sütun adları buradaki ikinci elemanlarla (ön ek) eşleşmelidir.
# Örn: Fen Bilimleri için dosyadaki sütunlar "Fen_Dogru", "Fen_Yanlis", "Fen_Bos" olmalı.
DERS_BILGILERI = [
    ("Türkçe", "Turkce"),
    ("Matematik", "Matematik"),
    ("Fen Bilimleri", "Fen"),
    ("Sosyal Bilgiler", "Sosyal"),
    ("Yabancı Dil", "Ingilizce"), # Veya dosyanızdaki adlandırmaya göre "Yabanci_Dil" vb.
    ("Din Kültürü", "Din")      # Veya dosyanızdaki adlandırmaya göre "Din_Kulturu" vb.
]

# Ders modelinin admin panelindeki görünümü
class DersAdmin(admin.ModelAdmin):
    list_display = ('ad',)
    search_fields = ('ad',)

# Ogrenci modelinin admin panelindeki görünümü
class OgrenciAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'kimlik_id', 'get_kullanici_adi', 'get_kullanici_email') # Gösterilecek sütunlar
    search_fields = ('ad_soyad', 'kimlik_id', 'user__username') # Arama yapılacak alanlar
    list_select_related = ('user',) # İlişkili User bilgisini daha verimli çekmek için
    # readonly_fields = ('user_link',) # Hata veren satır yorumlandı veya silindi

    # İlişkili User modelinden kullanıcı adını getiren metod
    def get_kullanici_adi(self, obj):
        if obj.user:
            return obj.user.username
        return "Hesap Yok" # Eğer User bağlı değilse
    get_kullanici_adi.short_description = "Kullanıcı Adı" # Sütun başlığı
    get_kullanici_adi.admin_order_field = 'user__username' # Kullanıcı adına göre sıralama

    # İlişkili User modelinden e-posta adresini getiren metod
    def get_kullanici_email(self, obj):
        if obj.user:
            return obj.user.email
        return "-"
    get_kullanici_email.short_description = "E-posta" # Sütun başlığı
    get_kullanici_email.admin_order_field = 'user__email' # E-postaya göre sıralama

    # İsteğe bağlı: Kullanıcı admin sayfasına link (yorumlu bırakıldı)
    # from django.utils.html import format_html
    # from django.urls import reverse
    # def user_link(self, obj):
    #     if obj.user:
    #         link = reverse("admin:auth_user_change", args=[obj.user.id])
    #         return format_html('<a href="{}">{}</a>', link, obj.user.username)
    #     return "N/A"
    # user_link.short_description = 'User Account'

# Sinav modelinin admin panelindeki görünümü
class SinavAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tarih')
    search_fields = ('ad',)
    list_filter = ('tarih',)
    ordering = ['-tarih', 'ad'] # Varsayılan sıralama (en yeni sınav önce)

# Sonuc modelinin admin panelindeki görünümü ve veri yükleme fonksiyonu
class SonucAdmin(admin.ModelAdmin):
    list_display = ('get_ogrenci_kimlik', 'get_ogrenci_ad_soyad', 'sinav', 'ders', 'dogru_sayisi', 'yanlis_sayisi', 'bos_sayisi', 'net_puan')
    list_filter = ('sinav', 'ders', 'ogrenci__user__is_active') # Sınav, ders ve öğrencinin aktiflik durumuna göre filtreleme
    search_fields = ('ogrenci__ad_soyad', 'ogrenci__kimlik_id', 'ogrenci__user__username', 'ders__ad', 'sinav__ad') # Arama alanları
    list_select_related = ('ogrenci', 'sinav', 'ders', 'ogrenci__user') # İlişkili verileri verimli çekme
    ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad'] # Varsayılan sıralama

    # Ogrenci modelinden ad soyadı getiren yardımcı metod
    def get_ogrenci_ad_soyad(self, obj):
        return obj.ogrenci.ad_soyad
    get_ogrenci_ad_soyad.short_description = 'Öğrenci Adı Soyadı'
    get_ogrenci_ad_soyad.admin_order_field = 'ogrenci__ad_soyad'

    # Ogrenci modelinden kimlik ID'sini getiren yardımcı metod
    def get_ogrenci_kimlik(self, obj):
        return obj.ogrenci.kimlik_id
    get_ogrenci_kimlik.short_description = 'Öğrenci Kimlik ID'
    get_ogrenci_kimlik.admin_order_field = 'ogrenci__kimlik_id'

    # Admin paneline özel URL eklemek için
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # /admin/sonuclar/sonuc/veri-yukle/ URL'ini tanımlar
            path('veri-yukle/', self.admin_site.admin_view(self.veri_yukle_view), name='sonuclar_sonuc_veri_yukle'),
        ]
        # Özel URL'leri standart admin URL'lerinden önce kontrol et
        return custom_urls + urls

    # Veri yükleme sayfasını ve işlemini yöneten view fonksiyonu
    def veri_yukle_view(self, request):
        # Eğer form gönderildiyse (POST isteği)
        if request.method == 'POST':
            form = VeriYuklemeFormu(request.POST, request.FILES)
            # Form geçerliyse işlemlere başla
            if form.is_valid():
                secilen_sinav = form.cleaned_data['sinav']
                yuklenen_dosya = form.cleaned_data['dosya']
                dosya_adi = yuklenen_dosya.name.lower()
                YANLIS_KATSAYISI = 4 # Net hesaplama katsayısı

                df = None # DataFrame'i başta None yap
                try:
                    # Dosya uzantısına göre oku (tüm veriyi string olarak oku)
                    if dosya_adi.endswith('.xlsx'):
                        df = pd.read_excel(yuklenen_dosya, dtype=str)
                    elif dosya_adi.endswith('.json'):
                        try:
                            data = json.load(yuklenen_dosya)
                            df = pd.DataFrame(data, dtype=str)
                        except json.JSONDecodeError:
                            self.message_user(request, "JSON dosyası formatı bozuk.", messages.ERROR)
                            return redirect("..") # Sonuç listesine geri dön
                        except Exception as e:
                             self.message_user(request, f"JSON verisi DataFrame'e dönüştürülürken hata: {e}", messages.ERROR)
                             return redirect("..")
                    else:
                        self.message_user(request, "Desteklenmeyen dosya formatı. Lütfen .xlsx veya .json uzantılı bir dosya yükleyin.", messages.ERROR)
                        return redirect("..")

                    # Dosya boşsa veya okunamadıysa hata ver
                    if df is None or df.empty:
                         self.message_user(request, "Dosya okunamadı veya dosya boş.", messages.ERROR)
                         return redirect("..")

                    # Dosyada olması gereken sütunları kontrol et
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

                    # Sayaçları ve hata listesini başlat
                    kaydedilen_sonuc_sayisi = 0
                    olusturulan_kullanici_sayisi = 0
                    hatali_satir_bilgileri = []

                    # Tüm veritabanı işlemlerini tek bir atomik blokta yap
                    with transaction.atomic():
                        # DataFrame'deki her satırı (öğrenciyi) işle
                        for index, row in df.iterrows():
                            try:
                                # Öğrenci bilgilerini al ve temizle
                                ogrenci_kimlik = str(row.get('Ogrenci_Kimlik_ID', '')).strip()
                                ogrenci_ad_soyad = str(row.get('Ogrenci_Ad_Soyad', '')).strip()

                                # Gerekli öğrenci bilgileri boşsa bu satırı atla
                                if not ogrenci_kimlik or not ogrenci_ad_soyad:
                                    hatali_satir_bilgileri.append(f"{index+2}. satır: Öğrenci Kimlik ID veya Ad Soyad boş.")
                                    continue # Sonraki satıra geç

                                # Öğrenciyi veritabanından al veya yeni oluştur
                                ogrenci, created_ogrenci = Ogrenci.objects.get_or_create(
                                    kimlik_id=ogrenci_kimlik,
                                    defaults={'ad_soyad': ogrenci_ad_soyad} # Yoksa bu bilgilerle oluştur
                                )
                                # Eğer öğrenci zaten vardıysa ve adı dosyada farklıysa, güncelle
                                if not created_ogrenci and ogrenci.ad_soyad != ogrenci_ad_soyad:
                                    ogrenci.ad_soyad = ogrenci_ad_soyad
                                    ogrenci.save(update_fields=['ad_soyad'])

                                # Öğrencinin User hesabı yoksa oluştur/bağla
                                if not ogrenci.user:
                                    try:
                                        # Bu kimlik ID ile başka bir User var mı diye kontrol et (nadiren gerekir)
                                        existing_user = User.objects.filter(username=ogrenci_kimlik).first()
                                        if existing_user:
                                            ogrenci.user = existing_user # Varsa bağla
                                        else:
                                            # Yeni User oluştur (ŞİFRE GÜVENLİ DEĞİL!)
                                            user_password = ogrenci_kimlik # Geçici ve güvensiz şifre
                                            new_user = User.objects.create_user(username=ogrenci_kimlik, password=user_password)
                                            ogrenci.user = new_user
                                            olusturulan_kullanici_sayisi += 1
                                        # Ogrenci kaydını User ile güncelle
                                        ogrenci.save(update_fields=['user'])
                                    except IntegrityError: # Kullanıcı adı zaten varsa (unique constraint ihlali)
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}): Kullanıcı adı zaten mevcut, hesap bağlanamadı.")
                                        continue # Bu öğrencinin sonuçlarını işleme
                                    except Exception as e_user: # Diğer User oluşturma hataları
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}): Kullanıcı hesabı hatası: {e_user}")
                                        continue # Bu öğrencinin sonuçlarını işleme

                                # Tanımlı her ders için sonuçları işle
                                for ders_gosterim_adi, ders_sutun_oneki in DERS_BILGILERI:
                                    try:
                                        # İlgili sütun adlarını oluştur
                                        dogru_sutun = f"{ders_sutun_oneki}_Dogru"
                                        yanlis_sutun = f"{ders_sutun_oneki}_Yanlis"
                                        bos_sutun = f"{ders_sutun_oneki}_Bos"

                                        # Değerleri al ve sayıya çevirmeye çalış (hatalıysa NaN olur)
                                        dogru_val = pd.to_numeric(row.get(dogru_sutun), errors='coerce')
                                        yanlis_val = pd.to_numeric(row.get(yanlis_sutun), errors='coerce')
                                        bos_val = pd.to_numeric(row.get(bos_sutun), errors='coerce')

                                        # NaN (Not a Number) değerlerini 0 olarak kabul et
                                        dogru = int(dogru_val) if pd.notna(dogru_val) else 0
                                        yanlis = int(yanlis_val) if pd.notna(yanlis_val) else 0
                                        bos = int(bos_val) if pd.notna(bos_val) else 0
                                        
                                        # Dersi al veya oluştur
                                        ders_obj, _ = Ders.objects.get_or_create(ad=ders_gosterim_adi)
                                        # Net puanı hesapla
                                        net_puan = dogru - (yanlis / YANLIS_KATSAYISI)

                                        # Sonuç kaydını oluştur veya güncelle
                                        Sonuc.objects.update_or_create(
                                            ogrenci=ogrenci, sinav=secilen_sinav, ders=ders_obj,
                                            defaults={ # Eğer kayıt varsa bu değerlerle güncelle
                                                'dogru_sayisi': dogru, 'yanlis_sayisi': yanlis,
                                                'bos_sayisi': bos, 'net_puan': net_puan
                                            }
                                        )
                                        kaydedilen_sonuc_sayisi += 1 # Başarılı işlenen sonuç sayısını artır
                                    except Exception as e_ders: # Ders bazlı hataları yakala
                                        hatali_satir_bilgileri.append(f"{index+2}. satır ({ogrenci_kimlik}), {ders_gosterim_adi} dersi: {e_ders}")
                            
                            except Exception as e_ogrenci: # Öğrenci bazlı genel hataları yakala
                                hatali_satir_bilgileri.append(f"{index+2}. satır işlenirken genel hata: {e_ogrenci}")
                    
                    # İşlem sonrası kullanıcıya bilgi mesajları göster
                    if kaydedilen_sonuc_sayisi > 0:
                        self.message_user(request, f"Toplam {kaydedilen_sonuc_sayisi} adet ders sonucu başarıyla işlendi.", messages.SUCCESS)
                    if olusturulan_kullanici_sayisi > 0:
                        self.message_user(request, f"{olusturulan_kullanici_sayisi} yeni öğrenci için kullanıcı hesabı oluşturuldu. (Şifreleri kimlik ID'leri ile aynıdır, GÜVENLİ DEĞİLDİR!)", messages.INFO)
                    if hatali_satir_bilgileri:
                        # Çok fazla hata mesajı varsa sadece özetini ve ilk birkaçını göster
                        hata_ozeti = f"{len(hatali_satir_bilgileri)} satırda/derste hata oluştu. İlk 5 hata: " + "; ".join(hatali_satir_bilgileri[:5])
                        self.message_user(request, hata_ozeti, messages.WARNING)
                    if kaydedilen_sonuc_sayisi == 0 and not hatali_satir_bilgileri:
                         self.message_user(request, "Dosyada işlenecek geçerli veri bulunamadı.", messages.INFO)
                    
                    # Sonuç listesi sayfasına geri yönlendir
                    return redirect("..")

                # Dosya okuma veya genel işlem hatalarını yakala
                except pd.errors.EmptyDataError:
                    self.message_user(request, "Yüklenen dosya boş veya okunamıyor.", messages.ERROR)
                except Exception as e:
                    self.message_user(request, f"Dosya okunurken veya işlenirken genel bir hata oluştu: {e}", messages.ERROR)
                # Hata durumunda da sonuç listesine geri dön
                return redirect("..")
            else: # Form geçerli değilse (örn: dosya seçilmemiş)
                self.message_user(request, "Formda hatalar var. Lütfen kontrol edin.", messages.ERROR)
        # Eğer GET isteği ise (sayfa ilk açıldığında)
        else:
            form = VeriYuklemeFormu() # Boş formu oluştur

        # Şablona gönderilecek context verileri
        context = {
            'title': 'Sınav Sonuç Verilerini Yükle (Geniş Format)',
            'form': form,
            'opts': self.model._meta, # Admin şablonlarının ihtiyaç duyduğu model bilgisi
            # Admin izinlerini context'e ekle (şablonda kullanılabilir)
            'has_view_permission': self.has_view_permission(request, None),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, None),
            'has_delete_permission': self.has_delete_permission(request, None),
            'has_editable_inline_admin_formsets': False,
        }
        # Veri yükleme formunu gösteren şablonu render et
        return render(request, 'admin/sonuclar/sonuc/veri_yukleme_formu.html', context)

# Modelleri admin paneline kaydet
admin.site.register(Ders, DersAdmin)
admin.site.register(Ogrenci, OgrenciAdmin)
admin.site.register(Sinav, SinavAdmin)
admin.site.register(Sonuc, SonucAdmin) # Güncellenmiş SonucAdmin ile kaydet
