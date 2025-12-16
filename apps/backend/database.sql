	-- =========================
	-- TEMİZ BAŞLANGIÇ
	-- =========================
	SET FOREIGN_KEY_CHECKS = 0;
	
	DROP TABLE IF EXISTS Maas_Detay_Archive;
	DROP TABLE IF EXISTS Maas_Hesap_Archive;
	DROP TABLE IF EXISTS Devam_Archive;
	DROP TABLE IF EXISTS Izin_Kayit_Archive;
	DROP TABLE IF EXISTS Personel_Archive;
	
	DROP TABLE IF EXISTS Maas_Detay;
	DROP TABLE IF EXISTS Maas_Hesap;
	DROP TABLE IF EXISTS Maas_Bileseni;
	DROP TABLE IF EXISTS Izin_Kayit;
	DROP TABLE IF EXISTS Izin_Turu;
	DROP TABLE IF EXISTS Devam;
	DROP TABLE IF EXISTS Personel_Pozisyon;
	DROP TABLE IF EXISTS Adaylar;
	DROP TABLE IF EXISTS Duyuru;
	DROP TABLE IF EXISTS Pozisyon;
	DROP TABLE IF EXISTS Kullanici;
	DROP TABLE IF EXISTS Personel;
	DROP TABLE IF EXISTS Departman;
	DROP TABLE IF EXISTS Devam_Durumu;
	DROP TABLE IF EXISTS Izin_Onay_Durumu;
	
	SET FOREIGN_KEY_CHECKS = 1;
	
	-- =========================
	-- ANA TABLOLAR
	-- =========================
	
	CREATE TABLE Departman (
	  departman_id INT AUTO_INCREMENT PRIMARY KEY,
	  departman_adi VARCHAR(255) NOT NULL,
	  aciklama TEXT,
	  olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Personel (
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
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Kullanici (
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
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Duyuru (
	  duyuru_id INT AUTO_INCREMENT PRIMARY KEY,
	  baslik VARCHAR(255) NOT NULL,
	  icerik TEXT NOT NULL,
	  olusturan_kullanici_id INT NOT NULL,
	  yayin_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  bitis_tarihi DATETIME NULL,
	  oncelik VARCHAR(20) DEFAULT 'Normal',
	  aktif_mi TINYINT DEFAULT 1,
	  FOREIGN KEY (olusturan_kullanici_id) REFERENCES Kullanici(kullanici_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Pozisyon (
	  pozisyon_id INT AUTO_INCREMENT PRIMARY KEY,
	  pozisyon_adi VARCHAR(255) NOT NULL,
	  taban_maas DECIMAL(12,2) NOT NULL,
	  departman_id INT,
	  FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Adaylar (
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
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Personel_Pozisyon (
	  personel_pozisyon_id INT AUTO_INCREMENT PRIMARY KEY,
	  personel_id INT NOT NULL,
	  pozisyon_id INT NOT NULL,
	  baslangic_tarihi DATE NOT NULL,
	  bitis_tarihi DATE NULL,
  guncel_mi TINYINT DEFAULT 1,
  kidem_seviyesi INT DEFAULT 3,
	  FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
	  FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
CREATE TABLE Devam (
  devam_id INT AUTO_INCREMENT PRIMARY KEY,
  personel_id INT NOT NULL,
  tarih DATE NOT NULL,
  giris_saati TIME NULL,
  cikis_saati TIME NULL,
  durum VARCHAR(50) DEFAULT 'Normal',
  ek_mesai_saat DECIMAL(8, 2) DEFAULT 0,
  aciklama TEXT,
  FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
  UNIQUE KEY unique_personel_tarih (personel_id, tarih)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Izin_Turu (
	  izin_turu_id INT AUTO_INCREMENT PRIMARY KEY,
	  izin_adi VARCHAR(255) NOT NULL,
	  yillik_hak_gun INT DEFAULT 0,
	  ucretli_mi TINYINT DEFAULT 1
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Izin_Kayit (
	  izin_kayit_id INT AUTO_INCREMENT PRIMARY KEY,
	  personel_id INT NOT NULL,
	  izin_turu_id INT NOT NULL,
	  baslangic_tarihi DATE NOT NULL,
	  bitis_tarihi DATE NOT NULL,
	  gun_sayisi INT NOT NULL,
	  onay_durumu VARCHAR(50) DEFAULT 'Beklemede',
	  FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
	  FOREIGN KEY (izin_turu_id) REFERENCES Izin_Turu(izin_turu_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Maas_Bileseni (
	  bilesen_id INT AUTO_INCREMENT PRIMARY KEY,
	  bilesen_adi VARCHAR(255) NOT NULL,
	  bilesen_tipi VARCHAR(100) NOT NULL,
	  sabit_mi TINYINT DEFAULT 0,
	  varsayilan_tutar DECIMAL(12,2) DEFAULT 0
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Maas_Hesap (
	  maas_hesap_id INT AUTO_INCREMENT PRIMARY KEY,
	  personel_id INT NOT NULL,
	  donem_yil INT NOT NULL,
	  donem_ay INT NOT NULL,
	  brut_maas DECIMAL(12,2) NOT NULL,
	  toplam_ekleme DECIMAL(12,2) DEFAULT 0,
	  toplam_kesinti DECIMAL(12,2) DEFAULT 0,
	  net_maas DECIMAL(12,2) NOT NULL,
	  odeme_tarihi DATE NULL,
	  odendi_mi TINYINT DEFAULT 0,
	  FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
	  UNIQUE KEY unique_personel_donem (personel_id, donem_yil, donem_ay)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Maas_Detay (
	  maas_detay_id INT AUTO_INCREMENT PRIMARY KEY,
	  maas_hesap_id INT NOT NULL,
	  bilesen_id INT NOT NULL,
	  tutar DECIMAL(12,2) NOT NULL,
	  FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id),
	  FOREIGN KEY (bilesen_id) REFERENCES Maas_Bileseni(bilesen_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	-- =========================
	-- ARŞİV TABLOLARI
	-- =========================
	
	CREATE TABLE Personel_Archive (
	  archive_id INT AUTO_INCREMENT PRIMARY KEY,
	  personel_id INT NOT NULL,
	  tc_kimlik_no VARCHAR(20),
	  ad VARCHAR(100),
	  soyad VARCHAR(100),
	  dogum_tarihi DATE,
	  telefon VARCHAR(20),
	  email VARCHAR(255),
	  adres TEXT,
	  ise_giris_tarihi DATE,
	  cikis_tarihi DATE,
	  departman_id INT,
	  aktif_mi TINYINT,
	  arsiv_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  arsiv_sebebi VARCHAR(255),
	  FOREIGN KEY (personel_id) REFERENCES Personel(personel_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Maas_Hesap_Archive (
	  archive_id INT AUTO_INCREMENT PRIMARY KEY,
	  maas_hesap_id INT NOT NULL,
	  personel_id INT NOT NULL,
	  donem_yil INT NOT NULL,
	  donem_ay INT NOT NULL,
	  brut_maas DECIMAL(12,2) NOT NULL,
	  toplam_ekleme DECIMAL(12,2) DEFAULT 0,
	  toplam_kesinti DECIMAL(12,2) DEFAULT 0,
	  net_maas DECIMAL(12,2) NOT NULL,
	  odeme_tarihi DATE,
	  odendi_mi TINYINT,
	  arsiv_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  arsiv_sebebi VARCHAR(255),
	  FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Maas_Detay_Archive (
	  archive_id INT AUTO_INCREMENT PRIMARY KEY,
	  maas_detay_id INT NOT NULL,
	  maas_hesap_id INT NOT NULL,
	  bilesen_id INT NOT NULL,
	  tutar DECIMAL(12,2) NOT NULL,
	  arsiv_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  FOREIGN KEY (maas_detay_id) REFERENCES Maas_Detay(maas_detay_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Izin_Kayit_Archive (
	  archive_id INT AUTO_INCREMENT PRIMARY KEY,
	  izin_kayit_id INT NOT NULL,
	  personel_id INT NOT NULL,
	  izin_turu_id INT NOT NULL,
	  baslangic_tarihi DATE NOT NULL,
	  bitis_tarihi DATE NOT NULL,
	  gun_sayisi INT NOT NULL,
	  onay_durumu VARCHAR(50),
	  arsiv_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  arsiv_sebebi VARCHAR(255),
	  FOREIGN KEY (izin_kayit_id) REFERENCES Izin_Kayit(izin_kayit_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	CREATE TABLE Devam_Archive (
	  archive_id INT AUTO_INCREMENT PRIMARY KEY,
	  devam_id INT NOT NULL,
	  personel_id INT NOT NULL,
	  tarih DATE NOT NULL,
	  giris_saati TIME,
	  cikis_saati TIME,
	  durum VARCHAR(50),
	  aciklama TEXT,
	  arsiv_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
	  arsiv_sebebi VARCHAR(255),
	  FOREIGN KEY (devam_id) REFERENCES Devam(devam_id)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	
	-- =========================
	-- ÖRNEK VERİLER
	-- =========================
	
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
	
	INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, adres, ise_giris_tarihi, departman_id, aktif_mi) VALUES
	('12345678901', 'Ahmet', 'Yılmaz', '1990-05-15', '05551234567', 'ahmet@firma.com', 'İstanbul', '2020-01-10', 1, 1),
	('98765432109', 'Ayşe', 'Demir',  '1988-08-20', '05559876543', 'ayse@firma.com',  'Ankara',  '2019-03-15', 2, 1);
	
INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi, kidem_seviyesi) VALUES
(1, 1, '2020-01-10', 1, 3),
(2, 2, '2019-03-15', 1, 3);