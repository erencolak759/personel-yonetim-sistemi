-- Veritabanı oluştur (eğer yoksa)
CREATE DATABASE IF NOT EXISTS maas_takip
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE maas_takip;

-- DEPARTMAN TABLOSU
DROP TABLE IF EXISTS maas;
DROP TABLE IF EXISTS devam;
DROP TABLE IF EXISTS personel;
DROP TABLE IF EXISTS departman;

CREATE TABLE departman (
    departman_id INT AUTO_INCREMENT PRIMARY KEY,
    departman_adi VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- PERSONEL TABLOSU
CREATE TABLE personel (
    personel_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    departman_id INT,
    maas DECIMAL(10,2),
    aktif_mi TINYINT(1) DEFAULT 1,
    CONSTRAINT fk_personel_departman
        FOREIGN KEY (departman_id) REFERENCES departman(departman_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- DEVAM TABLOSU (yoklama)
CREATE TABLE devam (
    devam_id INT AUTO_INCREMENT PRIMARY KEY,
    personel_id INT NOT NULL,
    tarih DATE NOT NULL,
    durum ENUM('NORMAL', 'GEÇ', 'İZİNLİ', 'DEVAMSIZ') DEFAULT 'NORMAL',
    aciklama VARCHAR(255),
    CONSTRAINT fk_devam_personel
        FOREIGN KEY (personel_id) REFERENCES personel(personel_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- MAAS TABLOSU (aylık maaş kaydı)
CREATE TABLE maas (
    maas_id INT AUTO_INCREMENT PRIMARY KEY,
    personel_id INT NOT NULL,
    yil INT NOT NULL,
    ay INT NOT NULL,
    net_maas DECIMAL(10,2) NOT NULL,
    odeme_tarihi DATE,
    CONSTRAINT fk_maas_personel
        FOREIGN KEY (personel_id) REFERENCES personel(personel_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ÖRNEK VERİLER (isteğe bağlı)
INSERT INTO departman (departman_adi) VALUES
('Yazılım'),
('İnsan Kaynakları'),
('Muhasebe');

INSERT INTO personel (ad, soyad, departman_id, maas)
VALUES
('Ali', 'Yılmaz', 1, 35000),
('Ayşe', 'Demir', 2, 28000),
('Mehmet', 'Kara', 3, 32000);
