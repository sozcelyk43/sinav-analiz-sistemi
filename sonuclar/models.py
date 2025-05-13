from django.db import models
from django.contrib.auth.models import User

class Ders(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Ders Adı")

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"
        ordering = ['ad']

class Ogrenci(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="Kullanıcı Hesabı"
    )
    kimlik_id = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Öğrenci Kimlik ID",
        help_text="Öğrencinin benzersiz kimliği. Kullanıcı adı olarak da kullanılabilir."
    )
    ad_soyad = models.CharField(max_length=150, verbose_name="Adı Soyadı")

    def __str__(self):
        if self.user:
            return f"{self.ad_soyad} ({self.kimlik_id} - Kullanıcı: {self.user.username})"
        return f"{self.ad_soyad} ({self.kimlik_id})"

    class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"
        ordering = ['ad_soyad']

class Sinav(models.Model):
    ad = models.CharField(max_length=200, verbose_name="Sınav Adı")
    tarih = models.DateField(verbose_name="Sınav Tarihi", null=True, blank=True)

    def __str__(self):
        return f"{self.ad} ({self.tarih.strftime('%d-%m-%Y') if self.tarih else 'Tarih Belirtilmemiş'})"

    class Meta:
        verbose_name = "Sınav"
        verbose_name_plural = "Sınavlar"
        ordering = ['-tarih', 'ad']

class Sonuc(models.Model):
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, verbose_name="Öğrenci")
    sinav = models.ForeignKey(Sinav, on_delete=models.CASCADE, verbose_name="Sınav")
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    dogru_sayisi = models.PositiveIntegerField(verbose_name="Doğru Sayısı")
    yanlis_sayisi = models.PositiveIntegerField(verbose_name="Yanlış Sayısı")
    bos_sayisi = models.PositiveIntegerField(verbose_name="Boş Sayısı")
    net_puan = models.FloatField(verbose_name="Net Puan")

    def __str__(self):
        return f"{self.ogrenci.ad_soyad} - {self.sinav.ad} - {self.ders.ad}: {self.net_puan:.2f} Net"

    class Meta:
        verbose_name = "Sınav Sonucu"
        verbose_name_plural = "Sınav Sonuçları"
        unique_together = ('ogrenci', 'sinav', 'ders')
        ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad']

# --- YENİ EKLENEN MODELLER ---

class Konu(models.Model):
    """
    Derslere ait ünite ve konuları/kazanımları tanımlar.
    """
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    unite_adi = models.CharField(max_length=200, verbose_name="Ünite Adı")
    konu_adi = models.CharField(max_length=300, verbose_name="Konu/Kazanım Adı") # Daha uzun olabilir

    def __str__(self):
        return f"{self.ders.ad} - {self.unite_adi} - {self.konu_adi}"

    class Meta:
        verbose_name = "Konu/Kazanım"
        verbose_name_plural = "Konular/Kazanımlar"
        # Bir dersin aynı ünitesinde aynı konu adı tekrarlanmasın
        unique_together = ('ders', 'unite_adi', 'konu_adi') 
        ordering = ['ders__ad', 'unite_adi', 'konu_adi']

class OgrenciYanlisDetayi(models.Model):
    """
    Bir öğrencinin belirli bir sınavda, belirli bir derste, belirli bir konuda
    kaç yanlış yaptığını kaydeder.
    """
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, verbose_name="Öğrenci")
    sinav = models.ForeignKey(Sinav, on_delete=models.CASCADE, verbose_name="Sınav")
    # Ders bilgisi Konu modelinden dolaylı olarak alınabilir, ama direkt bağlantı sorguları kolaylaştırır.
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders") 
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE, verbose_name="Konu/Kazanım")
    yanlis_adedi = models.PositiveIntegerField(default=1, verbose_name="Bu Konudaki Yanlış Adedi")

    def __str__(self):
        return f"{self.ogrenci.ad_soyad} - {self.sinav.ad} - {self.konu}: {self.yanlis_adedi} yanlış"

    class Meta:
        verbose_name = "Öğrenci Yanlış Detayı"
        verbose_name_plural = "Öğrenci Yanlış Detayları"
        # Bir öğrencinin aynı sınavda aynı konuda birden fazla kaydı olmasın, varsa güncellensin.
        unique_together = ('ogrenci', 'sinav', 'konu')
        ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'konu__ders__ad', 'konu__unite_adi', 'konu__konu_adi']
