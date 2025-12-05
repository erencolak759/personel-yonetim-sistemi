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
    stats = {"izinli": 0, "toplam": 0, "kalan_calisan": 0, "bekleyen": 0}

    try:
        # A. Bugün İzinli Olanlar
        sql_izinli = "SELECT COUNT(*) FROM Devam WHERE tarih = %s AND (durum = 'Izinli' OR durum = 'Raporlu')"
        cursor.execute(sql_izinli, (bugun,))
        row_izinli = cursor.fetchone()
        stats["izinli"] = row_izinli[0] if row_izinli else 0

        # B. Toplam Aktif Personel (Personel listesi ile AYNI mantık)
        cursor.execute("SELECT COUNT(*) FROM Personel WHERE aktif_mi = TRUE")
        row_toplam = cursor.fetchone()
        stats["toplam"] = row_toplam[0] if row_toplam else 0

        # C. Bekleyen İzinler
        cursor.execute("SELECT COUNT(*) FROM Izin_Kayit WHERE onay_durumu = 'Beklemede'")
        row_bekleyen = cursor.fetchone()
        stats["bekleyen"] = row_bekleyen[0] if row_bekleyen else 0

        stats["kalan_calisan"] = stats["toplam"] - stats["izinli"]

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

    return render_template("home.html", stats=stats)

# --- 2. PERSONEL LİSTELEME ---
@app.route("/personel")
def personel_list():
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
        SELECT p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, 
               d.departman_adi, poz.pozisyon_adi, poz.taban_maas
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

# --- 3. PERSONEL EKLEME ---
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
        ise_giris = request.form.get("ise_giris_tarihi")

        try:
            # ÖNEMLİ: aktif_mi = TRUE olarak ekleniyor
            sql_p = """
                INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, departman_id, ise_giris_tarihi, aktif_mi) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(sql_p, (tc, ad, soyad, dogum, tel, email, dept_id, ise_giris))
            yeni_id = cursor.lastrowid

            if poz_id:
                baslangic = ise_giris if ise_giris else datetime.date.today()
                sql_pp = "INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi) VALUES (%s, %s, %s, TRUE)"
                cursor.execute(sql_pp, (yeni_id, poz_id, baslangic))

            conn.commit()
            flash("Personel eklendi.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Hata: {str(e)}", "danger")
        finally:
            conn.close()
        return redirect(url_for("personel_list"))

    # Form için verileri çek
    cursor.execute("SELECT * FROM Departman")
    depts = cursor.fetchall()
    cursor.execute("SELECT * FROM Pozisyon")
    pozs = cursor.fetchall()
    conn.close()
    return render_template("personel_ekle.html", departmanlar=depts, pozisyonlar=pozs)

# --- 4. DEVAM/YOKLAMA ---
@app.route("/devam")
def devam():
    conn = get_connection()
    cursor = conn.cursor()
    tarih = request.args.get('tarih', datetime.date.today().strftime("%Y-%m-%d"))

    sql = """
        SELECT p.personel_id, p.ad, p.soyad, d.departman_adi, dv.durum 
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        LEFT JOIN Devam dv ON p.personel_id = dv.personel_id AND dv.tarih = %s
        WHERE p.aktif_mi = TRUE
    """
    cursor.execute(sql, (tarih,))
    personeller = cursor.fetchall()
    conn.close()
    return render_template("devam.html", personeller=personeller, bugun=tarih)

@app.route("/devam_kaydet", methods=["POST"])
def devam_kaydet():
    conn = get_connection()
    cursor = conn.cursor()
    tarih = request.form.get("tarih")

    try:
        for key, val in request.form.items():
            if key.startswith("durum_"):
                pid = key.split("_")[1]
                cursor.execute("DELETE FROM Devam WHERE personel_id=%s AND tarih=%s", (pid, tarih))
                cursor.execute("INSERT INTO Devam (personel_id, tarih, durum) VALUES (%s, %s, %s)", (pid, tarih, val))
        conn.commit()
        flash("Yoklama kaydedildi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("devam", tarih=tarih))

# --- 5. İZİN ---
@app.route("/izin", methods=["GET", "POST"])
def izin():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        pid = request.form.get("personel_id")
        tid = request.form.get("izin_turu_id")
        bas = request.form.get("baslangic_tarihi")
        bit = request.form.get("bitis_tarihi")
        gun = request.form.get("gun_sayisi")
        
        try:
            cursor.execute("INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi) VALUES (%s, %s, %s, %s, %s)", 
                          (pid, tid, bas, bit, gun))
            conn.commit()
            flash("İzin talebi oluşturuldu.", "success")
        except Exception as e:
            flash(f"Hata: {e}", "danger")
        return redirect(url_for("izin"))

    cursor.execute("SELECT k.*, p.ad, p.soyad, t.izin_adi FROM Izin_Kayit k JOIN Personel p ON k.personel_id=p.personel_id JOIN Izin_Turu t ON k.izin_turu_id=t.izin_turu_id")
    izinler = cursor.fetchall()
    cursor.execute("SELECT personel_id, ad, soyad FROM Personel WHERE aktif_mi=TRUE")
    personeller = cursor.fetchall()
    cursor.execute("SELECT * FROM Izin_Turu")
    turler = cursor.fetchall()
    conn.close()
    return render_template("izin.html", izinler=izinler, personeller=personeller, izin_turleri=turler)

# --- 6. MAAŞ ---
@app.route("/maas")
def maas():
    conn = get_connection()
    cursor = conn.cursor()
    # Basit bir listeleme, hesaplama mantığı eklenebilir
    cursor.execute("SELECT mh.*, p.ad, p.soyad FROM Maas_Hesap mh JOIN Personel p ON mh.personel_id=p.personel_id")
    maaslar = cursor.fetchall()
    conn.close()
    return render_template("maas.html", maaslar=maaslar)

if __name__ == "__main__":
    app.run(debug=True)