from django import forms
from .models import Sinav, Ogrenci # Ogrenci modelini import ettik
from django.forms.widgets import DateInput # HTML5 tarih widget'ı için

class VeriYuklemeFormu(forms.Form):
    """
    Admin panelinde Excel veya JSON dosyasından toplu sınav sonucu yüklemek için kullanılan form.
    """
    sinav = forms.ModelChoiceField(
        queryset=Sinav.objects.all().order_by('-tarih', 'ad'), # Sınavları tarihe göre (en yeni önce) sırala
        label="Verileri Yüklenecek Sınav",
        help_text="Lütfen sonuçları hangi sınav için yüklediğinizi seçin.",
        empty_label="--- Sınav Seçiniz ---"
    )
    dosya = forms.FileField(
        label="Sonuç Dosyası (Excel veya JSON)",
        help_text="Lütfen .xlsx veya .json formatında bir dosya yükleyin."
    )

class OgrenciAnalizFormu(forms.Form): # YENİ EKLENEN FORM
    """
    Öğrenci bazlı, tarih aralığına göre sınav sonuç analizi için kullanılan form.
    """
    ogrenci = forms.ModelChoiceField(
        queryset=Ogrenci.objects.all().order_by('ad_soyad'), # Öğrencileri ada göre sırala
        label="Öğrenci Seçiniz",
        empty_label="--- Öğrenci Seçiniz ---", # Bir öğrenci seçmek zorunlu
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}) # Bootstrap uyumlu class eklenebilir
    )
    baslangic_tarihi = forms.DateField(
        label="Başlangıç Tarihi",
        widget=DateInput(
            attrs={
                'type': 'date', # HTML5 tarih seçici
                'class': 'form-control' # Bootstrap uyumlu class
            }
        ),
        required=True
    )
    bitis_tarihi = forms.DateField(
        label="Bitiş Tarihi",
        widget=DateInput(
            attrs={
                'type': 'date', # HTML5 tarih seçici
                'class': 'form-control' # Bootstrap uyumlu class
            }
        ),
        required=True
    )

    def clean(self):
        """
        Form verilerini temizlerken ek doğrulama yapar.
        Başlangıç tarihinin bitiş tarihinden sonra olmamasını kontrol eder.
        """
        cleaned_data = super().clean()
        baslangic = cleaned_data.get("baslangic_tarihi")
        bitis = cleaned_data.get("bitis_tarihi")

        if baslangic and bitis:
            if baslangic > bitis:
                raise forms.ValidationError(
                    "Başlangıç tarihi, bitiş tarihinden sonra olamaz. Lütfen tarih aralığını kontrol edin."
                )
        return cleaned_data
