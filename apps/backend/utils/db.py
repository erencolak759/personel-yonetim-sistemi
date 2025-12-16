import pymysql
import os
from dotenv import load_dotenv

# Load environment variables from .env file
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
    # With DictCursor, rows are already dicts
    if row is None:
        return None
    return dict(row)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables (MySQL syntax)
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
            ek_mesai_saat DECIMAL(8, 2) DEFAULT 0,
            aciklama TEXT,
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
            UNIQUE KEY unique_personel_tarih (personel_id, tarih)
        )
    ''')

    # Eski kurulu veritabanlarında ek_mesai_saat kolonu olmayabilir; eklemeyi dene.
    try:
        cursor.execute(
            "ALTER TABLE Devam ADD COLUMN ek_mesai_saat DECIMAL(8, 2) DEFAULT 0"
        )
    except Exception:
        # Kolon zaten varsa hata alırız, bunu sessizce yoksay.
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Duyuru (
            duyuru_id INT AUTO_INCREMENT PRIMARY KEY,
            baslik VARCHAR(255) NOT NULL,
            icerik TEXT NOT NULL,
            olusturan_kullanici_id INT NOT NULL,
            yayin_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            bitis_tarihi DATETIME NULL,
            oncelik VARCHAR(20) DEFAULT 'Normal',
            aktif_mi TINYINT DEFAULT 1,
            FOREIGN KEY (olusturan_kullanici_id) REFERENCES Kullanici(kullanici_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Adaylar (
            aday_id INT AUTO_INCREMENT PRIMARY KEY,
            ad VARCHAR(100) NOT NULL,
            soyad VARCHAR(100) NOT NULL,
            telefon VARCHAR(20),
            email VARCHAR(255),
            pozisyon_id INT NOT NULL,
            basvuru_tarihi DATE NOT NULL,
            gorusme_tarihi DATE NULL,
            durum VARCHAR(50) DEFAULT 'Basvuru Alindi',
            aciklama TEXT,
            FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
        )
    ''')

    conn.commit()
    conn.close()


def seed_db():
    from werkzeug.security import generate_password_hash

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
            ('Yazılım Geliştirici', 25000.00, 1),
            ('İK Uzmanı', 20000.00, 2),
            ('Muhasebe Müdürü', 30000.00, 3)
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


if __name__ == '__main__':
    init_db()
    seed_db()
    print("Veritabanı başarıyla oluşturuldu!")


def check_schema_exists(table_name: str = 'Departman') -> bool:
    """Check whether the given table exists in the configured MySQL database.

    Returns True if exists, False otherwise. Useful for setup scripts to avoid
    re-initializing an already provisioned remote database.
    """
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
