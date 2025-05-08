from django import forms
from .models import Sinav # Ogrenci import'u kaldırıldı, artık formda kullanılmıyor.
from django.forms.widgets import DateInput

class VeriYuklemeFormu(forms.Form):
    """
    Admin panelinde Excel veya JSON dosyasından toplu sınav sonucu yüklemek için kullanılan form.
    """
    sinav = forms.ModelChoiceField(
        queryset=Sinav.objects.all().order_by('-tarih', 'ad'),
        label="Verileri Yüklenecek Sınav",
        help_text="Lütfen sonuçları hangi sınav için yüklediğinizi seçin.",
        empty_label="--- Sınav Seçiniz ---"
    )
    dosya = forms.FileField(
        label="Sonuç Dosyası (Excel veya JSON)",
        help_text="Lütfen .xlsx veya .json formatında bir dosya yükleyin."
    )

class OgrenciAnalizFormu(forms.Form):
    """
    Giriş yapmış öğrenci için, tarih aralığına göre sınav sonuç analizi için kullanılan form.
    Öğrenci seçme alanı kaldırıldı.
    """
    # ogrenci alanı kaldırıldı. View tarafında request.user'dan alınacak.
    baslangic_tarihi = forms.DateField(
        label="Başlangıç Tarihi",
        widget=DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        ),
        required=True
    )
    bitis_tarihi = forms.DateField(
        label="Bitiş Tarihi",
        widget=DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        ),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        baslangic = cleaned_data.get("baslangic_tarihi")
        bitis = cleaned_data.get("bitis_tarihi")

        if baslangic and bitis:
            if baslangic > bitis:
                raise forms.ValidationError(
                    "Başlangıç tarihi, bitiş tarihinden sonra olamaz. Lütfen tarih aralığını kontrol edin."
                )
        return cleaned_data
