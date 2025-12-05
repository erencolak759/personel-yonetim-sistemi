USE railway;
SET FOREIGN_KEY_CHECKS = 0;

-- TEMİZLİK
DROP TABLE IF EXISTS Maas_Detay;
DROP TABLE IF EXISTS Maas_Hesap;
DROP TABLE IF EXISTS Maas_Bileseni;
DROP TABLE IF EXISTS Izin_Kayit;
DROP TABLE IF EXISTS Izin_Turu;
DROP TABLE IF EXISTS Devam;
DROP TABLE IF EXISTS Personel_Pozisyon;
DROP TABLE IF EXISTS Pozisyon;
DROP TABLE IF EXISTS Personel;
DROP TABLE IF EXISTS Departman;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Departman
CREATE TABLE Departman (
    departman_id INT PRIMARY KEY AUTO_INCREMENT,
    departman_adi VARCHAR(100) NOT NULL,
    aciklama TEXT,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Personel
CREATE TABLE Personel (
    personel_id INT PRIMARY KEY AUTO_INCREMENT,
    tc_kimlik_no CHAR(11) UNIQUE NOT NULL,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    dogum_tarihi DATE NOT NULL,
    telefon VARCHAR(15),
    email VARCHAR(100),
    adres TEXT,
    ise_giris_tarihi DATE NOT NULL,
    departman_id INT,
    aktif_mi BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
);

-- 3. Pozisyon
CREATE TABLE Pozisyon (
    pozisyon_id INT PRIMARY KEY AUTO_INCREMENT,
    pozisyon_adi VARCHAR(100) NOT NULL,
    taban_maas DECIMAL(10,2) NOT NULL,
    departman_id INT,
    FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
);

-- 4. Personel-Pozisyon İlişkisi
CREATE TABLE Personel_Pozisyon (
    personel_pozisyon_id INT PRIMARY KEY AUTO_INCREMENT,
    personel_id INT NOT NULL,
    pozisyon_id INT NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    guncel_mi BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
);

-- 5. Devam (Yoklama)
CREATE TABLE Devam (
    devam_id INT PRIMARY KEY AUTO_INCREMENT,
    personel_id INT NOT NULL,
    tarih DATE NOT NULL,
    giris_saati TIME,
    cikis_saati TIME,
    durum ENUM('Normal', 'Izinli', 'Raporlu', 'Mazeret', 'Devamsiz') DEFAULT 'Normal',
    aciklama TEXT,
    FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    UNIQUE KEY unique_personel_tarih (personel_id, tarih)
);

-- 6. İzin Türleri
CREATE TABLE Izin_Turu (
    izin_turu_id INT PRIMARY KEY AUTO_INCREMENT,
    izin_adi VARCHAR(50) NOT NULL,
    yillik_hak_gun INT DEFAULT 0,
    ucretli_mi BOOLEAN DEFAULT TRUE
);

-- 7. İzin Kayıtları
CREATE TABLE Izin_Kayit (
    izin_kayit_id INT PRIMARY KEY AUTO_INCREMENT,
    personel_id INT NOT NULL,
    izin_turu_id INT NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    gun_sayisi INT NOT NULL,
    onay_durumu ENUM('Beklemede', 'Onaylandi', 'Reddedildi') DEFAULT 'Beklemede',
    FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    FOREIGN KEY (izin_turu_id) REFERENCES Izin_Turu(izin_turu_id)
);

-- 8. Maaş Bileşenleri
CREATE TABLE Maas_Bileseni (
    bilesen_id INT PRIMARY KEY AUTO_INCREMENT,
    bilesen_adi VARCHAR(100) NOT NULL,
    bilesen_tipi ENUM('Ekleme', 'Kesinti') NOT NULL,
    sabit_mi BOOLEAN DEFAULT FALSE,
    varsayilan_tutar DECIMAL(10,2) DEFAULT 0
);

-- 9. Maaş Hesap
CREATE TABLE Maas_Hesap (
    maas_hesap_id INT PRIMARY KEY AUTO_INCREMENT,
    personel_id INT NOT NULL,
    donem_yil INT NOT NULL,
    donem_ay INT NOT NULL,
    brut_maas DECIMAL(10,2) NOT NULL,
    toplam_ekleme DECIMAL(10,2) DEFAULT 0,
    toplam_kesinti DECIMAL(10,2) DEFAULT 0,
    net_maas DECIMAL(10,2) NOT NULL,
    odeme_tarihi DATE,
    odendi_mi BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    UNIQUE KEY unique_personel_donem (personel_id, donem_yil, donem_ay)
);

-- 10. Maaş Detay
CREATE TABLE Maas_Detay (
    maas_detay_id INT PRIMARY KEY AUTO_INCREMENT,
    maas_hesap_id INT NOT NULL,
    bilesen_id INT NOT NULL,
    tutar DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id),
    FOREIGN KEY (bilesen_id) REFERENCES Maas_Bileseni(bilesen_id)
);

-- ÖRNEK VERİ GİRİŞİ --
INSERT INTO Departman (departman_adi, aciklama) VALUES
('Bilgi İşlem', 'Yazılım ve donanım'),
('İnsan Kaynakları', 'Personel yönetimi'),
('Muhasebe', 'Finansal işlemler');

INSERT INTO Pozisyon (pozisyon_adi, taban_maas, departman_id) VALUES 
('Yazılım Geliştirici', 25000.00, 1),
('İK Uzmanı', 20000.00, 2),
('Muhasebe Müdürü', 30000.00, 3);

INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun) VALUES 
('Yıllık İzin', 14), ('Rapor', 0), ('Mazeret İzni', 3);

INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, ise_giris_tarihi, departman_id, aktif_mi) VALUES
('12345678901', 'Ahmet', 'Yılmaz', '1990-05-15', '05551112233', 'ahmet@mail.com', '2020-01-10', 1, TRUE),
('98765432109', 'Ayşe', 'Demir', '1988-08-20', '05554445566', 'ayse@mail.com', '2019-03-15', 2, TRUE);

INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi) VALUES
(1, 1, '2020-01-10', TRUE),
(2, 2, '2019-03-15', TRUE);