    # -*- coding: utf-8 -*-
    from django.db import migrations
    import os # Ortam değişkenlerini okumak için
    from django.contrib.auth.hashers import make_password # Şifreyi hashlemek için

    # Superuser oluşturmak veya şifresini güncellemek için bir fonksiyon
    def create_or_reset_superuser(apps, schema_editor):
        User = apps.get_model('auth', 'User') # Django'nun User modelini alıyoruz
        db_alias = schema_editor.connection.alias

        # Ortam değişkenlerinden kullanıcı adı, e-posta ve şifreyi almayı deneyelim
        # Render'da bu ortam değişkenlerini ayarlamanız GÜVENLİK açısından en iyisidir.
        # Eğer ortam değişkenleri yoksa, aşağıdaki varsayılan değerler kullanılacak.
        # DİKKAT: Koda doğrudan şifre yazmak GÜVENLİ DEĞİLDİR!
        #          Bu sadece geçici bir çözüm veya acil durum için düşünülmelidir.
        #          En iyi pratik, Render'da bu değişkenleri "Secret" olarak ayarlamaktır.
        
        SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'sozcelyk') # Varsayılan: admin_render
        SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'sozcelyk@gmail.com') # Varsayılan e-posta
        SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Allalbin435..') # Varsayılan: YeniSifre123! (BUNU DEĞİŞTİRİN!)

        if not SUPERUSER_PASSWORD:
            print("\nUYARI: DJANGO_SUPERUSER_PASSWORD ortam değişkeni ayarlanmamış. Superuser şifresi güncellenmeyecek/oluşturulmayacak.")
            return

        try:
            # Kullanıcıyı kullanıcı adına göre bulmaya çalış
            user = User.objects.using(db_alias).get(username=SUPERUSER_USERNAME)
            # Eğer kullanıcı varsa, şifresini güncelle
            user.set_password(SUPERUSER_PASSWORD) # set_password şifreyi hashler
            user.is_staff = True
            user.is_superuser = True
            user.save(using=db_alias)
            print(f"\n'{SUPERUSER_USERNAME}' adlı superuser'ın şifresi başarıyla güncellendi.")
        except User.DoesNotExist:
            # Eğer kullanıcı yoksa, yeni bir superuser oluştur
            print(f"\nSuperuser '{SUPERUSER_USERNAME}' bulunamadı, yenisi oluşturuluyor...")
            User.objects.using(db_alias).create_superuser(
                username=SUPERUSER_USERNAME,
                email=SUPERUSER_EMAIL,
                password=SUPERUSER_PASSWORD
            )
            print(f"Superuser '{SUPERUSER_USERNAME}' başarıyla oluşturuldu.")
        except Exception as e:
            print(f"\nSuperuser oluşturulurken/güncellenirken bir hata oluştu: {e}")


    class Migration(migrations.Migration):

        dependencies = [
            # Bu migration'ın hangi migration'dan sonra çalışacağını belirtin.
            # Genellikle uygulamanızın bir önceki migration dosyası olur.
            # Veya User modelini oluşturan 'auth' uygulamasının son migration'ından sonra çalışmalı.
            ('sonuclar', '0002_konu_ogrenciyanlisdetayi'), # 'sonuclar' uygulamanızın bir önceki migration'ının adı
                                                 # (Eğer bu ilk migration değilse, bir önceki dosyanın adını buraya yazın)
                                                 # Veya emin değilseniz:
            # ('auth', '__latest__'), # auth uygulamasının son migration'ından sonra çalışmasını sağlar
        ]

        operations = [
            # Yukarıda tanımladığımız create_or_reset_superuser fonksiyonunu çalıştır
            migrations.RunPython(create_or_reset_superuser),
        ]
    