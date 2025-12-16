-- Personnel Management System Database Schema (SQLite)
-- This file contains the database schema for the HR management system

-- Drop tables if they exist (for fresh installation)
DROP TABLE IF EXISTS Maas_Detay;
DROP TABLE IF EXISTS Maas_Hesap;
DROP TABLE IF EXISTS Maas_Bileseni;
DROP TABLE IF EXISTS Izin_Kayit;
DROP TABLE IF EXISTS Izin_Turu;
DROP TABLE IF EXISTS Devam;
DROP TABLE IF EXISTS Personel_Pozisyon;
DROP TABLE IF EXISTS Pozisyon;
DROP TABLE IF EXISTS Adaylar;
DROP TABLE IF EXISTS Duyuru;
DROP TABLE IF EXISTS Kullanici;
DROP TABLE IF EXISTS Personel;
DROP TABLE IF EXISTS Departman;

-- Department table
CREATE TABLE Departman (
    departman_id INTEGER PRIMARY KEY AUTOINCREMENT,
    departman_adi TEXT NOT NULL,
    aciklama TEXT,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Personnel table
CREATE TABLE Personel (
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

-- User table (for authentication)
CREATE TABLE Kullanici (
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

-- Announcement table
CREATE TABLE Duyuru (
    duyuru_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    baslik                 TEXT NOT NULL,
    icerik                 TEXT NOT NULL,
    olusturan_kullanici_id INTEGER NOT NULL,
    yayin_tarihi           DATETIME DEFAULT CURRENT_TIMESTAMP,
    bitis_tarihi           DATETIME,
    oncelik                TEXT DEFAULT 'Normal',   -- Dusuk / Normal / Yuksek
    aktif_mi               INTEGER DEFAULT 1,
    FOREIGN KEY (olusturan_kullanici_id) REFERENCES Kullanici(kullanici_id)
);

-- Position table
CREATE TABLE Pozisyon (
    pozisyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pozisyon_adi TEXT NOT NULL,
    taban_maas REAL NOT NULL,
    departman_id INTEGER,
    FOREIGN KEY (departman_id) REFERENCES Departman(departman_id)
);

-- Candidate (job applicant) table
CREATE TABLE Adaylar (
    aday_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ad             TEXT NOT NULL,
    soyad          TEXT NOT NULL,
    telefon        TEXT,
    email          TEXT,
    pozisyon_id    INTEGER NOT NULL,         -- basvurdugu pozisyon
    basvuru_tarihi DATE NOT NULL,
    gorusme_tarihi DATE,
    durum          TEXT DEFAULT 'Basvuru Alindi',  -- Basvuru Alindi / Mulakat / Red / Kabul
    aciklama       TEXT,
    FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
);

-- Personnel-Position mapping table
CREATE TABLE Personel_Pozisyon (
    personel_pozisyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    personel_id INTEGER NOT NULL,
    pozisyon_id INTEGER NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE,
    guncel_mi INTEGER DEFAULT 1,
    FOREIGN KEY (personel_id) REFERENCES Personel(personel_id),
    FOREIGN KEY (pozisyon_id) REFERENCES Pozisyon(pozisyon_id)
);

-- Attendance table
CREATE TABLE Devam (
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

-- Leave type table
CREATE TABLE Izin_Turu (
    izin_turu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    izin_adi TEXT NOT NULL,
    yillik_hak_gun INTEGER DEFAULT 0,
    ucretli_mi INTEGER DEFAULT 1
);

-- Leave record table
CREATE TABLE Izin_Kayit (
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

-- Salary component table
CREATE TABLE Maas_Bileseni (
    bilesen_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bilesen_adi TEXT NOT NULL,
    bilesen_tipi TEXT NOT NULL,
    sabit_mi INTEGER DEFAULT 0,
    varsayilan_tutar REAL DEFAULT 0
);

-- Salary calculation table
CREATE TABLE Maas_Hesap (
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

-- Salary detail table
CREATE TABLE Maas_Detay (
    maas_detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    maas_hesap_id INTEGER NOT NULL,
    bilesen_id INTEGER NOT NULL,
    tutar REAL NOT NULL,
    FOREIGN KEY (maas_hesap_id) REFERENCES Maas_Hesap(maas_hesap_id),
    FOREIGN KEY (bilesen_id) REFERENCES Maas_Bileseni(bilesen_id)
);

-- Seed data for departments
INSERT INTO Departman (departman_adi, aciklama) VALUES
('Bilgi Islem', 'Yazilim ve donanim destek'),
('Insan Kaynaklari', 'Personel yonetimi'),
('Muhasebe', 'Mali isler');

-- Seed data for positions
INSERT INTO Pozisyon (pozisyon_adi, taban_maas, departman_id) VALUES 
('Yazilim Gelistirici', 25000.00, 1),
('IK Uzmani', 20000.00, 2),
('Muhasebe Muduru', 30000.00, 3);

-- Seed data for leave types
INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun, ucretli_mi) VALUES
('Yillik Izin', 14, 1),
('Hastalik Izni', 10, 1),
('Mazeret Izni', 5, 1),
('Ucretsiz Izin', 0, 0);

-- Seed data for sample employees
INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, ise_giris_tarihi, departman_id) VALUES
('12345678901', 'Ahmet', 'Yilmaz', '1990-05-15', '05551234567', 'ahmet@firma.com', '2020-01-10', 1),
('98765432109', 'Ayse', 'Demir', '1988-08-20', '05559876543', 'ayse@firma.com', '2019-03-15', 2);

-- Seed data for employee positions
INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi) VALUES
(1, 1, '2020-01-10', 1),
(2, 2, '2019-03-15', 1);
