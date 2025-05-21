from django.db import migrations
import os 
from django.contrib.auth.hashers import make_password 

def create_or_reset_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User') 
    db_alias = schema_editor.connection.alias
    
    SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'sozcelyk') 
    SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'sozcelyk@gmail.com') 
    SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Allalbin435..')

    if not SUPERUSER_PASSWORD:
        print("\nUYARI: DJANGO_SUPERUSER_PASSWORD ortam değişkeni ayarlanmamış. Superuser şifresi güncellenmeyecek/oluşturulmayacak.")
        return

    try:
        # User.objects yerine User._default_manager kullanarak doğru yöneticiyi alalım
        # veya doğrudan User.objects.using(db_alias) üzerinden işlem yapalım.
        # En temizi, User modelinin kendi yöneticisini kullanmaktır.
        user_manager = User.objects.db_manager(db_alias) # Doğru veritabanı için yöneticiyi al

        user = user_manager.get(username=SUPERUSER_USERNAME)
        user.set_password(SUPERUSER_PASSWORD) 
        user.is_staff = True
        user.is_superuser = True
        user.save(using=db_alias)
        print(f"\n'{SUPERUSER_USERNAME}' adlı superuser'ın şifresi başarıyla güncellendi.")
    except User.DoesNotExist:
        print(f"\nSuperuser '{SUPERUSER_USERNAME}' bulunamadı, yenisi oluşturuluyor...")
        # create_superuser metodunu doğru yönetici üzerinden çağır
        user_manager.create_superuser(
            username=SUPERUSER_USERNAME,
            email=SUPERUSER_EMAIL,
            password=SUPERUSER_PASSWORD
        )
        print(f"Superuser '{SUPERUSER_USERNAME}' başarıyla oluşturuldu.")
    except Exception as e:
        print(f"\nSuperuser oluşturulurken/güncellenirken bir hata oluştu: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('sonuclar', '0002_konu_ogrenciyanlisdetayi'), 
    ]

    operations = [
        migrations.RunPython(create_or_reset_superuser),
    ]
