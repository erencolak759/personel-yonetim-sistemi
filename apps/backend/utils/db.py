import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Departman (
            departman_id INTEGER PRIMARY KEY AUTOINCREMENT,
            departman_adi TEXT NOT NULL,
            aciklama TEXT,
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Personel (
            personel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tc_kimlik_no TEXT UNIQUE NOT NULL,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            dogum_tarihi DATE NOT NULL,
            telefon TEXT,
            email TEXT,
            adres TEXT,
            ise_giris_tarihi DATE NOT NULL,
            departman_id INTEGER,
            aktif_mi INTEGER DEFAULT 1,
            FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
        );

        CREATE TABLE IF NOT EXISTS Kullanici (
            kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT UNIQUE NOT NULL,
            sifre_hash TEXT NOT NULL,
            email TEXT,
            rol TEXT NOT NULL DEFAULT 'employee',
            personel_id INTEGER,
            ilk_giris INTEGER DEFAULT 1,
            aktif_mi INTEGER DEFAULT 1,
            olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_giris DATETIME,
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id)
        );

        CREATE TABLE IF NOT EXISTS Pozisyon (
            pozisyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pozisyon_adi TEXT NOT NULL,
            taban_maas REAL NOT NULL,
            departman_id INTEGER,
            FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
        );

        CREATE TABLE IF NOT EXISTS Personel_Pozisyon (
            personel_pozisyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            pozisyon_id INTEGER NOT NULL,
            baslangic_tarihi DATE NOT NULL,
            bitis_tarihi DATE,
            guncel_mi INTEGER DEFAULT 1,
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
            FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
        );

        CREATE TABLE IF NOT EXISTS Devam (
            devam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            tarih DATE NOT NULL,
            giris_saati TIME,
            cikis_saati TIME,
            durum TEXT DEFAULT 'Normal',
            aciklama TEXT,
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
            UNIQUE(personel_id, tarih)
        );

        CREATE TABLE IF NOT EXISTS Izin_Turu (
            izin_turu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            izin_adi TEXT NOT NULL,
            yillik_hak_gun INTEGER DEFAULT 0,
            ucretli_mi INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS Izin_Kayit (
            izin_kayit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            izin_turu_id INTEGER NOT NULL,
            baslangic_tarihi DATE NOT NULL,
            bitis_tarihi DATE NOT NULL,
            gun_sayisi INTEGER NOT NULL,
            onay_durumu TEXT DEFAULT 'Beklemede',
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
            FOREIGN KEY (izin_turu_id) REFERENCES Izin_Turu(izin_turu_id)
        );

        CREATE TABLE IF NOT EXISTS Maas_Bileseni (
            bilesen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bilesen_adi TEXT NOT NULL,
            bilesen_tipi TEXT NOT NULL,
            sabit_mi INTEGER DEFAULT 0,
            varsayilan_tutar REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS Maas_Hesap (
            maas_hesap_id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_id INTEGER NOT NULL,
            donem_yil INTEGER NOT NULL,
            donem_ay INTEGER NOT NULL,
            brut_maas REAL NOT NULL,
            toplam_ekleme REAL DEFAULT 0,
            toplam_kesinti REAL DEFAULT 0,
            net_maas REAL NOT NULL,
            odeme_tarihi DATE,
            odendi_mi INTEGER DEFAULT 0,
            FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
            UNIQUE(personel_id, donem_yil, donem_ay)
        );

        CREATE TABLE IF NOT EXISTS Maas_Detay (
            maas_detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
            maas_hesap_id INTEGER NOT NULL,
            bilesen_id INTEGER NOT NULL,
            tutar REAL NOT NULL,
            FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id),
            FOREIGN KEY (bilesen_id) REFERENCES Maas_Bileseni(bilesen_id)
        );
    ''')
    
    conn.commit()
    conn.close()


def seed_db():
    from werkzeug.security import generate_password_hash
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Departman")
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO Departman (departman_adi, aciklama) VALUES
            ('Bilgi İşlem', 'Yazılım ve donanım destek'),
            ('İnsan Kaynakları', 'Personel yönetimi'),
            ('Muhasebe', 'Mali işler');

            INSERT INTO Pozisyon (pozisyon_adi, taban_maas, departman_id) VALUES 
            ('Yazılım Geliştirici', 25000.00, 1),
            ('İK Uzmanı', 20000.00, 2),
            ('Muhasebe Müdürü', 30000.00, 3);

            INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun, ucretli_mi) VALUES
            ('Yıllık İzin', 14, 1),
            ('Hastalık İzni', 10, 1),
            ('Mazeret İzni', 5, 1),
            ('Ücretsiz İzin', 0, 0);
        ''')
        conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM Kullanici WHERE kullanici_adi = ?", ('admin',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO Kullanici (kullanici_adi, sifre_hash, email, rol, ilk_giris, aktif_mi)
            VALUES (?, ?, ?, ?, 0, 1)
        ''', ('admin', password_hash, 'admin@sistem.com', 'admin'))
        conn.commit()
    
    conn.close()


if __name__ == '__main__':
    init_db()
    seed_db()
    print("Veritabanı başarıyla oluşturuldu!")
