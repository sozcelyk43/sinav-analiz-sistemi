from django.db import models
# İleride öğrenciler için Django'nun kendi kullanıcı modelini kullanmayı düşünebiliriz,
# şimdilik ForeignKey ile User modeline bağlanmak yerine kendi Ogrenci modelimizi kullanacağız.
# from django.contrib.auth.models import User

class Ders(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Ders Adı")

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"

class Ogrenci(models.Model):
    # Adminin yükleyeceği dosyadaki öğrenciyi tanımlayan benzersiz bir kimlik
    # Örn: Öğrenci Numarası, TC Kimlik No (hash'lenmiş haliyle saklamak daha güvenli olabilir), veya benzersiz bir kod
    kimlik_id = models.CharField(max_length=50, unique=True, verbose_name="Öğrenci Kimlik ID")
    ad_soyad = models.CharField(max_length=150, verbose_name="Adı Soyadı")
    # İleride Django'nun User modeli ile ilişkilendirmek için:
    # user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.ad_soyad} ({self.kimlik_id})"

    class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"

class Sinav(models.Model):
    ad = models.CharField(max_length=200, verbose_name="Sınav Adı")
    tarih = models.DateField(verbose_name="Sınav Tarihi", null=True, blank=True) # İsteğe bağlı

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Sınav"
        verbose_name_plural = "Sınavlar"

class Sonuc(models.Model):
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, verbose_name="Öğrenci")
    sinav = models.ForeignKey(Sinav, on_delete=models.CASCADE, verbose_name="Sınav")
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    dogru_sayisi = models.PositiveIntegerField(verbose_name="Doğru Sayısı")
    yanlis_sayisi = models.PositiveIntegerField(verbose_name="Yanlış Sayısı")
    bos_sayisi = models.PositiveIntegerField(verbose_name="Boş Sayısı")
    net_puan = models.FloatField(verbose_name="Net Puan") # Bu puan, veri yüklenirken hesaplanıp buraya yazılabilir

    def __str__(self):
        return f"{self.ogrenci} - {self.sinav} - {self.ders}: {self.net_puan} Net"

    class Meta:
        verbose_name = "Sınav Sonucu"
        verbose_name_plural = "Sınav Sonuçları"
        # Bir öğrencinin aynı sınavda aynı dersten birden fazla sonucu olmaması için:
        unique_together = ('ogrenci', 'sinav', 'ders')