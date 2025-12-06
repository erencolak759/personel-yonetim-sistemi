from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_connection
import datetime

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"

# --- 1. ANA SAYFA (DASHBOARD) ---
@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor()
    
    bugun = datetime.date.today()
    
    izinli_sayisi = 0
    toplam_personel = 0
    bekleyen_isler = 0

    try:
        # A. Bugün İzinli Olanlar
        sql_izinli = """
            SELECT COUNT(*) AS sayi
            FROM Devam
            WHERE tarih = %s AND durum = 'Izinli'
        """
        cursor.execute(sql_izinli, (bugun,))
        row_izinli = cursor.fetchone()
        if row_izinli:
            # dict geldiği için key ile erişiyoruz
            izinli_sayisi = row_izinli["sayi"]

        # B. Toplam Aktif Personel Sayısı
        sql_toplam = """
            SELECT COUNT(*) AS sayi
            FROM Personel
            WHERE aktif_mi = TRUE
        """
        cursor.execute(sql_toplam)
        row_toplam = cursor.fetchone()
        if row_toplam:
            toplam_personel = row_toplam["sayi"]

        # C. Bekleyen İzin Talepleri
        sql_bekleyen = """
            SELECT COUNT(*) AS sayi
            FROM Izin_Kayit
            WHERE onay_durumu = 'Beklemede'
        """
        cursor.execute(sql_bekleyen)
        row_bekleyen = cursor.fetchone()
        if row_bekleyen:
            bekleyen_isler = row_bekleyen["sayi"]

    except Exception as e:
        print("İstatistik Hatası:", repr(e))

    finally:
        conn.close()

    stats = {
        "izinli": izinli_sayisi,
        "toplam": toplam_personel,
        "kalan_calisan": toplam_personel - izinli_sayisi,
        "bekleyen": bekleyen_isler
    }


    return render_template("home.html", stats=stats)


# --- 2. PERSONEL LİSTELEME ---
@app.route("/personel")
def personel_list():
    conn = get_connection()
    cursor = conn.cursor()
    
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
        WHERE p.aktif_mi = TRUE
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

# --- 3. PERSONEL EKLEME (DÜZELTİLDİ) ---
@app.route("/personel_ekle", methods=["GET", "POST"])
def personel_ekle():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        tc = request.form.get("tc_kimlik_no")
        ad = request.form.get("ad")
        soyad = request.form.get("soyad")
        dogum = request.form.get("dogum_tarihi")
        tel = request.form.get("telefon")
        email = request.form.get("email")
        dept_id = request.form.get("departman_id")
        poz_id = request.form.get("pozisyon_id")
        ise_giris = request.form.get("ise_giris_tarihi") # Formdan tarihi al

        try:
            # Personel Ekle (DÜZELTME: ise_giris_tarihi sütununu ekledik)
            sql_p = """
                INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, departman_id, ise_giris_tarihi) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_p, (tc, ad, soyad, dogum, tel, email, dept_id, ise_giris))
            yeni_id = cursor.lastrowid

            # Pozisyon Ekle
            if poz_id:
                # Pozisyon başlangıç tarihi olarak işe giriş tarihini mi yoksa bugünü mü baz alalım?
                # Genelde işe giriş tarihi ile başlar.
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
            # Hata mesajını detaylı gösterelim
            flash(f"Kayıt Hatası: {str(e)}", "danger")
            print(f"SQL Hatası: {str(e)}") # Konsola da yazdıralım
        finally:
            conn.close()
        
        return redirect(url_for("personel_list"))

    # GET İsteği - Formu Göster
    cursor.execute("SELECT * FROM Departman")
    departmanlar = cursor.fetchall()
    cursor.execute("SELECT * FROM Pozisyon")
    pozisyonlar = cursor.fetchall()
    conn.close()

    return render_template("personel_ekle.html", departmanlar=departmanlar, pozisyonlar=pozisyonlar)

# --- 4. İZİN YÖNETİMİ ---
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

        cursor.execute("SELECT personel_id, ad, soyad FROM Personel WHERE aktif_mi = TRUE")
        personeller = cursor.fetchall()
        cursor.execute("SELECT * FROM Izin_Turu")
        izin_turleri = cursor.fetchall()
    except:
        izinler = []
        personeller = []
        izin_turleri = []
    
    conn.close()
    return render_template("izin.html", izinler=izinler, personeller=personeller, izin_turleri=izin_turleri)

# --- 5. DEVAM (YOKLAMA LİSTESİ) ---
@app.route("/devam")
def devam():
    conn = get_connection()
    cursor = conn.cursor()
    
    secilen_tarih = request.args.get('tarih')
    if not secilen_tarih:
        secilen_tarih = datetime.date.today().strftime("%Y-%m-%d")

    sql = """
        SELECT 
            p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, 
            d.departman_adi,
            dv.durum as bugunku_durum
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        LEFT JOIN Devam dv ON p.personel_id = dv.personel_id AND dv.tarih = %s
        WHERE p.aktif_mi = TRUE
    """
    cursor.execute(sql, (secilen_tarih,))
    personeller = cursor.fetchall()
    conn.close()
    
    return render_template("devam.html", personeller=personeller, bugun=secilen_tarih)

# --- 6. DEVAM KAYDET ---
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
                
                # Önce eski kaydı sil
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

# --- 7. MAAŞ BORDROSU ---
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