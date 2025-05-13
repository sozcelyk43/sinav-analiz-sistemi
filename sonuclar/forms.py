from django import forms
from .models import Sinav
from django.forms.widgets import DateInput

class VeriYuklemeFormu(forms.Form):
    sinav = forms.ModelChoiceField(
        queryset=Sinav.objects.all().order_by('-tarih', 'ad'),
        label="Genel Sonuçları Yüklenecek Sınav",
        help_text="Lütfen genel sonuçları (D/Y/B) hangi sınav için yüklediğinizi seçin.",
        empty_label="--- Sınav Seçiniz ---",
        required=True
    )
    dosya = forms.FileField(
        label="Genel Sonuç Dosyası (Excel veya JSON)",
        help_text="Lütfen D/Y/B bilgilerini içeren .xlsx veya .json formatında bir dosya yükleyin.",
        required=True
    )

class OgrenciAnalizFormu(forms.Form):
    baslangic_tarihi = forms.DateField(
        label="Başlangıç Tarihi",
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        required=True
    )
    bitis_tarihi = forms.DateField(
        label="Bitiş Tarihi",
        widget=DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        baslangic = cleaned_data.get("baslangic_tarihi")
        bitis = cleaned_data.get("bitis_tarihi")
        if baslangic and bitis and baslangic > bitis:
            raise forms.ValidationError(
                "Başlangıç tarihi, bitiş tarihinden sonra olamaz. Lütfen tarih aralığını kontrol edin."
            )
        return cleaned_data

class KonuKazanımYuklemeFormu(forms.Form):
    konu_dosyasi = forms.FileField(
        label="Konu/Kazanım Dosyası (Excel veya JSON)",
        help_text="Lütfen Ders, Ünite ve Konu/Kazanım bilgilerini içeren .xlsx veya .json formatında bir dosya yükleyin.",
        required=True
    )

    def clean_konu_dosyasi(self):
        dosya = self.cleaned_data.get('konu_dosyasi')
        if dosya:
            dosya_adi = dosya.name.lower()
            if not (dosya_adi.endswith('.xlsx') or dosya_adi.endswith('.json')):
                raise forms.ValidationError(
                    "Desteklenmeyen dosya formatı. Lütfen .xlsx veya .json uzantılı bir dosya yükleyin."
                )
        return dosya

# --- DÜZELTİLMİŞ FORM ---
class YanlisDetayYuklemeFormu(forms.Form):
    """
    Admin panelinde Excel veya JSON dosyasından toplu olarak
    öğrenci yanlış detaylarını (ünite, konu bazlı) yüklemek için kullanılacak form.
    Sınav alanı kaldırıldı, çünkü sınav bilgisi URL'den alınıyor.
    """
    detay_dosyasi = forms.FileField(
        label="Yanlış Detay Dosyası (Excel veya JSON)",
        help_text="Lütfen ünite/konu bazlı yanlış adetlerini içeren .xlsx veya .json formatında bir dosya yükleyin.",
        required=True # Dosya yüklemek zorunlu
    )

    def clean_detay_dosyasi(self):
        """
        Yüklenen dosyanın uzantısını kontrol eder.
        """
        dosya = self.cleaned_data.get('detay_dosyasi')
        if dosya: # Dosya seçilmişse kontrol et
            dosya_adi = dosya.name.lower()
            if not (dosya_adi.endswith('.xlsx') or dosya_adi.endswith('.json')):
                raise forms.ValidationError(
                    "Desteklenmeyen dosya formatı. Lütfen .xlsx veya .json uzantılı bir dosya yükleyin."
                )
        # Eğer dosya zorunluysa ve seçilmemişse, Django zaten "Bu alan zorunludur" hatası verir.
        # Ama burada ek bir kontrol de yapılabilir:
        # elif not dosya and self.fields['detay_dosyasi'].required:
        #     raise forms.ValidationError("Lütfen bir dosya seçin.")
        return dosya
