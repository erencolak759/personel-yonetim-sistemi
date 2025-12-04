from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_connection
import datetime

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"

@app.route("/")
def home():
    return render_template("home.html")

# --- 1. PERSONEL LİSTELEME ---
@app.route("/personel")
def personel_list():
    conn = get_connection()
    cursor = conn.cursor()
    # PDF yapısına göre Personel, Departman ve Güncel Pozisyonu çekiyoruz
    sql = """
        SELECT 
            p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon,
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
    cursor.execute(sql)
    personeller = cursor.fetchall()
    conn.close()
    return render_template("personel_list.html", personeller=personeller)

# --- 2. PERSONEL EKLEME ---
@app.route("/personel_ekle", methods=["GET", "POST"])
def personel_ekle():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        # Formdan gelen veriler (PDF sütunlarıyla birebir aynı)
        tc = request.form.get("tc_kimlik_no")
        ad = request.form.get("ad")
        soyad = request.form.get("soyad")
        dogum = request.form.get("dogum_tarihi")
        tel = request.form.get("telefon")
        email = request.form.get("email")
        giris_tarihi = request.form.get("ise_giris_tarihi")
        dept_id = request.form.get("departman_id")
        poz_id = request.form.get("pozisyon_id")

        try:
            # Önce Personel tablosuna ekle
            sql_p = """
                INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, ise_giris_tarihi, departman_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_p, (tc, ad, soyad, dogum, tel, email, giris_tarihi, dept_id))
            yeni_id = cursor.lastrowid

            # Sonra Personel_Pozisyon tablosuna ekle (İlişki kur)
            if poz_id:
                sql_pp = """
                    INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                    VALUES (%s, %s, %s, TRUE)
                """
                cursor.execute(sql_pp, (yeni_id, poz_id, giris_tarihi))

            conn.commit()
            flash("Personel başarıyla kaydedildi.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Hata oluştu: {str(e)}", "danger")
        finally:
            conn.close()
        
        return redirect(url_for("personel_list"))

    # Select kutuları için verileri hazırla
    cursor.execute("SELECT * FROM Departman")
    departmanlar = cursor.fetchall()
    cursor.execute("SELECT * FROM Pozisyon")
    pozisyonlar = cursor.fetchall()
    conn.close()

    return render_template("personel_ekle.html", departmanlar=departmanlar, pozisyonlar=pozisyonlar)

# --- 3. İZİN YÖNETİMİ (YENİ - 10. Tablo) ---
@app.route("/izin", methods=["GET", "POST"])
def izin():
    conn = get_connection()
    cursor = conn.cursor()

    # Yeni İzin Talebi Varsa
    if request.method == "POST":
        personel_id = request.form.get("personel_id")
        izin_turu_id = request.form.get("izin_turu_id")
        baslangic = request.form.get("baslangic_tarihi")
        bitis = request.form.get("bitis_tarihi")
        gun_sayisi = request.form.get("gun_sayisi")

        # Izin_Kayit tablosuna ekle
        sql_insert = """
            INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu)
            VALUES (%s, %s, %s, %s, %s, 'Beklemede')
        """
        cursor.execute(sql_insert, (personel_id, izin_turu_id, baslangic, bitis, gun_sayisi))
        conn.commit()
        flash("İzin talebi oluşturuldu.", "success")
        return redirect(url_for("izin"))

    # İzin Listesini Getir
    sql_list = """
        SELECT k.*, p.ad, p.soyad, t.izin_adi 
        FROM Izin_Kayit k
        JOIN Personel p ON k.personel_id = p.personel_id
        JOIN Izin_Turu t ON k.izin_turu_id = t.izin_turu_id
        ORDER BY k.baslangic_tarihi DESC
    """
    cursor.execute(sql_list)
    izinler = cursor.fetchall()

    # Form için gerekli veriler
    cursor.execute("SELECT personel_id, ad, soyad FROM Personel WHERE aktif_mi = TRUE")
    personeller = cursor.fetchall()
    cursor.execute("SELECT * FROM Izin_Turu")
    izin_turleri = cursor.fetchall()
    
    conn.close()
    return render_template("izin.html", izinler=izinler, personeller=personeller, izin_turleri=izin_turleri)

# --- 4. DEVAM (YOKLAMA) ---
@app.route("/devam")
def devam():
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        SELECT p.personel_id, p.ad, p.soyad, d.departman_adi 
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        WHERE p.aktif_mi = TRUE
    """
    cursor.execute(sql)
    personeller = cursor.fetchall()
    conn.close()
    
    bugun = datetime.date.today().strftime("%Y-%m-%d")
    return render_template("devam.html", personeller=personeller, bugun=bugun)

# --- 5. MAAŞ BORDROSU ---
@app.route("/maas")
def maas():
    conn = get_connection()
    cursor = conn.cursor()
    # Maas_Hesap tablosundan verileri çek
    sql = """
        SELECT mh.*, p.ad, p.soyad, d.departman_adi 
        FROM Maas_Hesap mh
        JOIN Personel p ON mh.personel_id = p.personel_id
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
    """
    cursor.execute(sql)
    maaslar = cursor.fetchall()
    conn.close()
    return render_template("maas.html", maaslar=maaslar)

if __name__ == "__main__":
    app.run(debug=True)