import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "railway"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_connection():
    connection = pymysql.connect(**DB_CONFIG)
    return connection


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Departman (
                departman_id INT AUTO_INCREMENT PRIMARY KEY,
                departman_adi VARCHAR(255) NOT NULL,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Personel (
                personel_id INT AUTO_INCREMENT PRIMARY KEY,
                tc_kimlik_no VARCHAR(20) UNIQUE NOT NULL,
                ad VARCHAR(100) NOT NULL,
                soyad VARCHAR(100) NOT NULL,
                dogum_tarihi DATE NOT NULL,
                telefon VARCHAR(20),
                email VARCHAR(255),
                adres TEXT,
                ise_giris_tarihi DATE NOT NULL,
                departman_id INT,
                aktif_mi TINYINT DEFAULT 1,
                FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Kullanici (
                kullanici_id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(100) UNIQUE NOT NULL,
                sifre_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                rol VARCHAR(50) NOT NULL DEFAULT 'employee',
                personel_id INT,
                ilk_giris TINYINT DEFAULT 1,
                aktif_mi TINYINT DEFAULT 1,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                son_giris DATETIME,
                FOREIGN KEY (personel_id) REFERENCES Personel(personel_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Pozisyon (
                pozisyon_id INT AUTO_INCREMENT PRIMARY KEY,
                pozisyon_adi VARCHAR(255) NOT NULL,
                taban_maas DECIMAL(12, 2) NOT NULL,
                departman_id INT,
                FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Personel_Pozisyon (
                personel_pozisyon_id INT AUTO_INCREMENT PRIMARY KEY,
                personel_id INT NOT NULL,
                pozisyon_id INT NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE,
                guncel_mi TINYINT DEFAULT 1,
                FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
                FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Devam (
                devam_id INT AUTO_INCREMENT PRIMARY KEY,
                personel_id INT NOT NULL,
                tarih DATE NOT NULL,
                giris_saati TIME,
                cikis_saati TIME,
                durum VARCHAR(50) DEFAULT 'Normal',
                ek_mesai_saat DECIMAL(5,2) DEFAULT 0,
                aciklama TEXT,
                FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
                UNIQUE KEY unique_personel_tarih (personel_id, tarih)
            )
        ''')
        try:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM information_schema.columns WHERE table_schema=%s AND table_name='Devam' AND column_name='ek_mesai_saat'",
                (DB_CONFIG.get('database'),)
            )
            col_row = cursor.fetchone()
            if not col_row or int(col_row.get('cnt', 0)) == 0:
                try:
                    cursor.execute("ALTER TABLE Devam ADD COLUMN ek_mesai_saat DECIMAL(5,2) DEFAULT 0")
                except Exception:
                    pass
        except Exception:
            pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Izin_Turu (
                izin_turu_id INT AUTO_INCREMENT PRIMARY KEY,
                izin_adi VARCHAR(255) NOT NULL,
                yillik_hak_gun INT DEFAULT 0,
                ucretli_mi TINYINT DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Izin_Kayit (
                izin_kayit_id INT AUTO_INCREMENT PRIMARY KEY,
                personel_id INT NOT NULL,
                izin_turu_id INT NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE NOT NULL,
                gun_sayisi INT NOT NULL,
                onay_durumu VARCHAR(50) DEFAULT 'Beklemede',
                FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
                FOREIGN KEY (izin_turu_id) REFERENCES Izin_Turu(izin_turu_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Maas_Bileseni (
                bilesen_id INT AUTO_INCREMENT PRIMARY KEY,
                bilesen_adi VARCHAR(255) NOT NULL,
                bilesen_tipi VARCHAR(100) NOT NULL,
                sabit_mi TINYINT DEFAULT 0,
                varsayilan_tutar DECIMAL(12, 2) DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Maas_Hesap (
                maas_hesap_id INT AUTO_INCREMENT PRIMARY KEY,
                personel_id INT NOT NULL,
                donem_yil INT NOT NULL,
                donem_ay INT NOT NULL,
                brut_maas DECIMAL(12, 2) NOT NULL,
                toplam_ekleme DECIMAL(12, 2) DEFAULT 0,
                toplam_kesinti DECIMAL(12, 2) DEFAULT 0,
                net_maas DECIMAL(12, 2) NOT NULL,
                odeme_tarihi DATE,
                odendi_mi TINYINT DEFAULT 0,
                FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
                UNIQUE KEY unique_personel_donem (personel_id, donem_yil, donem_ay)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Maas_Detay (
                maas_detay_id INT AUTO_INCREMENT PRIMARY KEY,
                maas_hesap_id INT NOT NULL,
                bilesen_id INT NOT NULL,
                tutar DECIMAL(12, 2) NOT NULL,
                FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id),
                FOREIGN KEY (bilesen_id) REFERENCES Maas_Bileseni(bilesen_id)
            )
        ''')
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS Personel_Archive LIKE Personel")
            cursor.execute("CREATE TABLE IF NOT EXISTS Devam_Archive LIKE Devam")
            cursor.execute("CREATE TABLE IF NOT EXISTS Izin_Kayit_Archive LIKE Izin_Kayit")
            cursor.execute("CREATE TABLE IF NOT EXISTS Maas_Hesap_Archive LIKE Maas_Hesap")
            cursor.execute("CREATE TABLE IF NOT EXISTS Maas_Detay_Archive LIKE Maas_Detay")
        except Exception:
            pass

        conn.commit()
    except KeyboardInterrupt:
        try:
            conn.rollback()
        except Exception:
            pass
        print("init_db: İşlem kullanıcı tarafından kesildi (Ctrl+C). Bağlantı kapatılıyor.")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def seed_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM Departman")
    if cursor.fetchone()['cnt'] == 0:
        cursor.execute('''
            INSERT INTO Departman (departman_adi, aciklama) VALUES
            ('Bilgi İşlem', 'Yazılım ve donanım destek'),
            ('İnsan Kaynakları', 'Personel yönetimi'),
            ('Muhasebe', 'Mali işler')
        ''')

        cursor.execute('''
            INSERT INTO Pozisyon (pozisyon_adi, taban_maas, departman_id) VALUES
            ('Yazılım Geliştirici', 80000.00, 1),
            ('İK Uzmanı', 70000.00, 2),
            ('Muhasebe Müdürü', 85000.00, 3)
        ''')

        cursor.execute('''
            INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun, ucretli_mi) VALUES
            ('Yıllık İzin', 14, 1),
            ('Hastalık İzni', 10, 1),
            ('Mazeret İzni', 5, 1),
            ('Ücretsiz İzin', 0, 0)
        ''')
        conn.commit()

    cursor.execute("SELECT COUNT(*) AS cnt FROM Kullanici WHERE kullanici_adi = %s", ('admin',))
    if cursor.fetchone()['cnt'] == 0:
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO Kullanici (kullanici_adi, sifre_hash, email, rol, ilk_giris, aktif_mi)
            VALUES (%s, %s, %s, %s, 0, 1)
        ''', ('admin', password_hash, 'admin@sistem.com', 'admin'))
        conn.commit()
    conn.close()

def check_schema_exists(table_name: str = 'Departman') -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        dbname = DB_CONFIG.get('database')
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
            (dbname, table_name)
        )
        row = cursor.fetchone()
        cnt = int(row.get('cnt', 0)) if row else 0
        return cnt > 0
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    init_db()
    seed_db()
    print("Veritabanı başarıyla oluşturuldu!")