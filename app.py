from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_connection
import datetime

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"

# ==========================================
# 1. ANA SAYFA (DASHBOARD)
# ==========================================
@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor()
    
    bugun = datetime.date.today()
    
    # İstatistik Değişkenleri
    izinli_sayisi = 0
    toplam_personel = 0
    bekleyen_isler = 0
    toplam_maas = 0
    duyurular = []

    try:
        # A. Bugün İzinli Olanları Say
        sql_izinli = "SELECT COUNT(*) FROM Devam WHERE tarih = %s AND durum = 'Izinli'"
        cursor.execute(sql_izinli, (bugun,))
        row_izinli = cursor.fetchone()
        if row_izinli:
            izinli_sayisi = row_izinli[0]

        # B. Toplam Personel Sayısı (Filtresiz - Kesin Sonuç İçin)
        cursor.execute("SELECT COUNT(*) FROM Personel")
        row_toplam = cursor.fetchone()
        if row_toplam:
            toplam_personel = row_toplam[0]

        # C. Bekleyen İzin Talepleri
        cursor.execute("SELECT COUNT(*) FROM Izin_Kayit WHERE onay_durumu = 'Beklemede'")
        row_bekleyen = cursor.fetchone()
        if row_bekleyen:
            bekleyen_isler = row_bekleyen[0]

        # D. Toplam Maaş Yükü (Güncel Pozisyonlardan)
        sql_maas = """
            SELECT SUM(poz.taban_maas) 
            FROM Personel_Pozisyon pp
            JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE pp.guncel_mi = TRUE
        """
        cursor.execute(sql_maas)
        row_maas = cursor.fetchone()
        if row_maas and row_maas[0]:
            toplam_maas = row_maas[0]

        # E. Son Duyurular (Son 3 tanesi)
        try:
            cursor.execute("SELECT * FROM Duyuru ORDER BY tarih DESC LIMIT 3")
            duyurular = cursor.fetchall()
        except Exception as e_duyuru:
            print(f"Duyuru tablosu henüz yok veya hata: {e_duyuru}")
            duyurular = []

    except Exception as e:
        print(f"Genel İstatistik Hatası: {e}")
        
    conn.close()

    # Maaş formatlama (Örn: 145000 -> 145.000)
    maas_formatli = "{:,.0f}".format(toplam_maas).replace(",", ".")

    stats = {
        "izinli": izinli_sayisi,
        "toplam": toplam_personel,
        "kalan_calisan": toplam_personel - izinli_sayisi,
        "bekleyen": bekleyen_isler,
        "maas_toplam": maas_formatli
    }

    return render_template("home.html", stats=stats, duyurular=duyurular)


# ==========================================
# 2. PERSONEL İŞLEMLERİ
# ==========================================
@app.route("/personel")
def personel_list():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tüm personeli getirir (Aktif/Pasif ayrımı yapmaksızın görünmesi için)
    sql = """
        SELECT 
            p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, p.email,
            p.ise_giris_tarihi, 
            d.departman_adi,
            poz.pozisyon_adi,
            poz.taban_maas
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = TRUE
        LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
        ORDER BY p.personel_id DESC
    """
    try:
        cursor.execute(sql)
        personeller = cursor.fetchall()
    except Exception as e:
        print(f"Liste Hatası: {e}")
        personeller = []
        
    conn.close()
    return render_template("personel_list.html", personeller=personeller)


@app.route("/personel_ekle", methods=["GET", "POST"])
def personel_ekle():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        # Form verilerini al
        tc = request.form.get("tc_kimlik_no")
        ad = request.form.get("ad")
        soyad = request.form.get("soyad")
        dogum = request.form.get("dogum_tarihi")
        tel = request.form.get("telefon")
        email = request.form.get("email")
        dept_id = request.form.get("departman_id")
        poz_id = request.form.get("pozisyon_id")
        ise_giris = request.form.get("ise_giris_tarihi")

        try:
            # 1. Personel Ekle (aktif_mi = 1 olarak zorluyoruz)
            sql_p = """
                INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, departman_id, ise_giris_tarihi, aktif_mi) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql_p, (tc, ad, soyad, dogum, tel, email, dept_id, ise_giris))
            yeni_id = cursor.lastrowid

            # 2. Pozisyon Ekle (Varsa)
            if poz_id:
                baslangic = ise_giris if ise_giris else datetime.date.today()
                sql_pp = """
                    INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                    VALUES (%s, %s, %s, TRUE)
                """
                cursor.execute(sql_pp, (yeni_id, poz_id, baslangic))

            conn.commit()
            flash("Personel başarıyla kaydedildi.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Kayıt Hatası: {str(e)}", "danger")
            print(f"SQL Hatası: {str(e)}")
        finally:
            conn.close()
        
        return redirect(url_for("personel_list"))

    # GET İsteği: Departman ve Pozisyonları listele
    cursor.execute("SELECT * FROM Departman")
    departmanlar = cursor.fetchall()
    cursor.execute("SELECT * FROM Pozisyon")
    pozisyonlar = cursor.fetchall()
    conn.close()

    return render_template("personel_ekle.html", departmanlar=departmanlar, pozisyonlar=pozisyonlar)


# ==========================================
# 3. DUYURU YÖNETİMİ (YENİ)
# ==========================================
@app.route("/duyurular")
def duyurular_sayfasi():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tüm duyuruları çek
    duyurular = []
    try:
        cursor.execute("SELECT * FROM Duyuru ORDER BY tarih DESC")
        duyurular = cursor.fetchall()
    except Exception as e:
        print(f"Tablo Hatası: {e}")
        flash("Duyuru tablosu bulunamadı. Lütfen veritabanını güncelleyin.", "warning")

    conn.close()
    return render_template("duyurular.html", duyurular=duyurular)


@app.route("/duyuru_ekle", methods=["POST"])
def duyuru_ekle():
    conn = get_connection()
    cursor = conn.cursor()
    
    baslik = request.form.get("baslik")
    icerik = request.form.get("icerik")
    oncelik = request.form.get("oncelik")
    tarih = datetime.date.today()
    
    try:
        sql = "INSERT INTO Duyuru (baslik, icerik, oncelik, tarih) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (baslik, icerik, oncelik, tarih))
        conn.commit()
        flash("Duyuru başarıyla yayınlandı.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()
        
    return redirect(url_for("duyurular_sayfasi"))


@app.route("/duyuru_sil/<int:id>")
def duyuru_sil(id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Duyuru WHERE duyuru_id = %s", (id,))
        conn.commit()
        flash("Duyuru silindi.", "warning")
    except Exception as e:
        conn.rollback()
        flash(f"Silme hatası: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("duyurular_sayfasi"))


# ==========================================
# 4. İZİN VE YOKLAMA İŞLEMLERİ
# ==========================================
@app.route("/izin", methods=["GET", "POST"])
def izin():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        personel_id = request.form.get("personel_id")
        izin_turu_id = request.form.get("izin_turu_id")
        baslangic = request.form.get("baslangic_tarihi")
        bitis = request.form.get("bitis_tarihi")
        gun_sayisi = request.form.get("gun_sayisi")

        try:
            sql_insert = """
                INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu)
                VALUES (%s, %s, %s, %s, %s, 'Beklemede')
            """
            cursor.execute(sql_insert, (personel_id, izin_turu_id, baslangic, bitis, gun_sayisi))
            conn.commit()
            flash("İzin talebi oluşturuldu.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Hata: {str(e)}", "danger")
            
        return redirect(url_for("izin"))

    try:
        sql_list = """
            SELECT k.*, p.ad, p.soyad, t.izin_adi 
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            JOIN Izin_Turu t ON k.izin_turu_id = t.izin_turu_id
            ORDER BY k.baslangic_tarihi DESC
        """
        cursor.execute(sql_list)
        izinler = cursor.fetchall()

        cursor.execute("SELECT personel_id, ad, soyad FROM Personel")
        personeller = cursor.fetchall()
        cursor.execute("SELECT * FROM Izin_Turu")
        izin_turleri = cursor.fetchall()
    except:
        izinler = []
        personeller = []
        izin_turleri = []
    
    conn.close()
    return render_template("izin.html", izinler=izinler, personeller=personeller, izin_turleri=izin_turleri)


@app.route("/devam")
def devam():
    conn = get_connection()
    cursor = conn.cursor()
    
    secilen_tarih = request.args.get('tarih')
    if not secilen_tarih:
        secilen_tarih = datetime.date.today().strftime("%Y-%m-%d")

    # Tüm personeli getirir (Aktif filtresi olmadan)
    sql = """
        SELECT 
            p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, 
            d.departman_adi,
            dv.durum as bugunku_durum
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        LEFT JOIN Devam dv ON p.personel_id = dv.personel_id AND dv.tarih = %s
    """
    cursor.execute(sql, (secilen_tarih,))
    personeller = cursor.fetchall()
    conn.close()
    
    return render_template("devam.html", personeller=personeller, bugun=secilen_tarih)


@app.route("/devam_kaydet", methods=["POST"])
def devam_kaydet():
    conn = get_connection()
    cursor = conn.cursor()
    
    secilen_tarih = request.form.get("tarih")
    if not secilen_tarih:
         secilen_tarih = datetime.date.today().strftime("%Y-%m-%d")

    try:
        for key, value in request.form.items():
            if key.startswith("durum_"):
                personel_id = key.split("_")[1]
                durum = value 
                
                # Önce eski kaydı sil (Tekrarlanan kayıt olmaması için)
                cursor.execute("DELETE FROM Devam WHERE personel_id = %s AND tarih = %s", (personel_id, secilen_tarih))
                
                # Yeni durumu ekle
                sql = "INSERT INTO Devam (personel_id, tarih, durum) VALUES (%s, %s, %s)"
                cursor.execute(sql, (personel_id, secilen_tarih, durum))
                
        conn.commit()
        flash(f"{secilen_tarih} tarihi için yoklama başarıyla kaydedildi.", "success")
        
    except Exception as e:
        conn.rollback()
        flash(f"Hata oluştu: {str(e)}", "danger")
        
    finally:
        conn.close()
        
    return redirect(url_for("devam", tarih=secilen_tarih))


# ==========================================
# 5. MAAŞ BORDROSU
# ==========================================
@app.route("/maas")
def maas():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT mh.*, p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
        """
        cursor.execute(sql)
        maaslar = cursor.fetchall()
    except:
        maaslar = []
        
    conn.close()
    return render_template("maas.html", maaslar=maaslar)


if __name__ == "__main__":
    app.run(debug=True)