from django.db import models
from django.contrib.auth.models import User # Django'nun User modelini import ediyoruz

class Ders(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Ders Adı")

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"

class Ogrenci(models.Model):
    # Django'nun User modeli ile birebir ilişki
    # Bir User silindiğinde ilişkili Ogrenci kaydı da silinir (CASCADE).
    # null=True, blank=True: Bir Ogrenci kaydının başlangıçta bir User'a bağlı olmaması durumuna izin verir
    # (örneğin, User hesabı daha sonra oluşturulacaksa). Ancak idealde her öğrencinin bir User'ı olmalı.
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Kullanıcı Hesabı")
    
    kimlik_id = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Öğrenci Kimlik ID",
        help_text="Öğrencinin benzersiz kimliği. Kullanıcı adı olarak da kullanılabilir."
    )
    ad_soyad = models.CharField(max_length=150, verbose_name="Adı Soyadı")
    # Sınıf bilgisi eklemek isterseniz buraya ekleyebilirsiniz:
    # sinif = models.CharField(max_length=20, verbose_name="Sınıfı", blank=True, null=True)


    def __str__(self):
        # Eğer bir kullanıcıya bağlıysa, kullanıcı adını da gösterelim
        if self.user:
            return f"{self.ad_soyad} ({self.kimlik_id} - User: {self.user.username})"
        return f"{self.ad_soyad} ({self.kimlik_id})"

    class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"

class Sinav(models.Model):
    ad = models.CharField(max_length=200, verbose_name="Sınav Adı")
    tarih = models.DateField(verbose_name="Sınav Tarihi", null=True, blank=True)

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Sınav"
        verbose_name_plural = "Sınavlar"
        ordering = ['-tarih', 'ad'] # Sınavları en yeni tarihe göre sırala

class Sonuc(models.Model):
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, verbose_name="Öğrenci")
    sinav = models.ForeignKey(Sinav, on_delete=models.CASCADE, verbose_name="Sınav")
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    dogru_sayisi = models.PositiveIntegerField(verbose_name="Doğru Sayısı")
    yanlis_sayisi = models.PositiveIntegerField(verbose_name="Yanlış Sayısı")
    bos_sayisi = models.PositiveIntegerField(verbose_name="Boş Sayısı")
    net_puan = models.FloatField(verbose_name="Net Puan")

    def __str__(self):
        return f"{self.ogrenci} - {self.sinav} - {self.ders}: {self.net_puan} Net"

    class Meta:
        verbose_name = "Sınav Sonucu"
        verbose_name_plural = "Sınav Sonuçları"
        unique_together = ('ogrenci', 'sinav', 'ders')
        ordering = ['-sinav__tarih', 'ogrenci__ad_soyad', 'ders__ad']
