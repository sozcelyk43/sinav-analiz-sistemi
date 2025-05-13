import pandas as pd

def olustur_ornek_yanlis_detay_excel(dosya_adi="ornek_sinav_yanlis_detaylari.xlsx"):
    """
    Öğrenci yanlış detaylarını içeren örnek bir Excel dosyası oluşturur.
    """
    veri = {
        'Ogrenci_Kimlik_ID': ['60', '60', '60', '69', '79', '98', '98', '66', '60', '79'],
        'Ders_Adi': [
            'Türkçe', 'Türkçe', 'Matematik', 'Türkçe', 'Fen Bilimleri', 
            'Matematik', 'Matematik', 'Sosyal Bilgiler', 'Fen Bilimleri', 'Matematik'
        ],
        'Unite_Adi': [
            'Sözcükte Anlam', 'Cümlede Anlam', 'Doğal Sayılar', 'Sözcükte Anlam', 'Vücudumuzun Bilmecesini Çözelim', 
            'Kesirler', 'Kesirler', 'Birey ve Toplum', 'Kuvvetin Ölçülmesi ve Sürtünme', 'Geometrik Cisimler'
        ],
        'Konu_Adi_Kazanım_Adi': [
            'Eş Anlamlı Kelimeler', 'Neden-Sonuç Cümleleri', 'Üslü İfadeler', 'Zıt Anlamlı Kelimeler', 'Besinler ve Özellikleri', 
            'Birim Kesirler', 'Kesirleri Karşılaştırma', 'Hak ve Sorumluluklarım', 'Sürtünme Kuvveti', 'Açılar'
        ],
        'Yanlis_Adedi_Bu_Konuda': [2, 1, 3, 1, 1, 2, 1, 1, 1, 2]
    }

    df = pd.DataFrame(veri)

    try:
        # DataFrame'i Excel dosyasına yaz
        # index=False: DataFrame index'ini Excel'e yazmaz
        df.to_excel(dosya_adi, index=False)
        print(f"'{dosya_adi}' başarıyla oluşturuldu!")
        print("Bu dosyayı açıp kendi verilerinizle güncelleyebilirsiniz.")
        print("Sütun başlıklarının ve veri formatının aynı kaldığından emin olun.")
    except Exception as e:
        print(f"Excel dosyası oluşturulurken bir hata oluştu: {e}")
        print("Lütfen 'openpyxl' kütüphanesinin kurulu olduğundan emin olun: pip install openpyxl")

if __name__ == "__main__":
    olustur_ornek_yanlis_detay_excel()
