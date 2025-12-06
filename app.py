from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from db import get_connection
from utils.pdf_generator import PDFGenerator
import datetime

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"


# --- 1. ANA SAYFA (DASHBOARD) - GELİŞTİRİLMİŞ GRAFİKLER ---
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

        # D. Departman Dağılımı (Grafik için)
        sql_dept = """
            SELECT d.departman_adi, COUNT(p.personel_id) as sayi
            FROM Departman d
            LEFT JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = TRUE
            GROUP BY d.departman_id, d.departman_adi
            HAVING sayi > 0
        """
        cursor.execute(sql_dept)
        departman_data = cursor.fetchall()

        # E. Son 6 Ay Devamsızlık Trendi
        sql_devamsizlik = """
            SELECT 
                DATE_FORMAT(tarih, '%Y-%m') as ay,
                COUNT(*) as sayi
            FROM Devam
            WHERE durum = 'Devamsiz' 
            AND tarih >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(tarih, '%Y-%m')
            ORDER BY ay ASC
        """
        cursor.execute(sql_devamsizlik)
        devamsizlik_data = cursor.fetchall()

        # F. İzin Durumu İstatistikleri
        sql_izin_stats = """
            SELECT 
                onay_durumu,
                COUNT(*) as sayi
            FROM Izin_Kayit
            WHERE baslangic_tarihi >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            GROUP BY onay_durumu
        """
        cursor.execute(sql_izin_stats)
        izin_stats = cursor.fetchall()

        # G. Departmanlara Göre Ortalama Maaş
        sql_maas_dept = """
            SELECT 
                d.departman_adi,
                ROUND(AVG(poz.taban_maas), 2) as ort_maas
            FROM Departman d
            JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = TRUE
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = TRUE
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            GROUP BY d.departman_id, d.departman_adi
            HAVING ort_maas IS NOT NULL
        """
        cursor.execute(sql_maas_dept)
        maas_dept_data = cursor.fetchall()

    except Exception as e:
        print("İstatistik Hatası:", repr(e))
        departman_data = []
        devamsizlik_data = []
        izin_stats = []
        maas_dept_data = []

    finally:
        conn.close()

    stats = {
        "izinli": izinli_sayisi,
        "toplam": toplam_personel,
        "kalan_calisan": toplam_personel - izinli_sayisi,
        "bekleyen": bekleyen_isler
    }

    return render_template("home.html",
                           stats=stats,
                           departman_data=departman_data,
                           devamsizlik_data=devamsizlik_data,
                           izin_stats=izin_stats,
                           maas_dept_data=maas_dept_data)


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

        # Departman ve Pozisyon listelerini de gönder (Toplu işlem modalleri için)
        cursor.execute("SELECT * FROM Departman")
        departmanlar = cursor.fetchall()

        cursor.execute("SELECT * FROM Pozisyon")
        pozisyonlar = cursor.fetchall()
    except Exception as e:
        print(f"Liste Hatası: {e}")
        personeller = []
        departmanlar = []
        pozisyonlar = []

    conn.close()
    return render_template("personel_list.html",
                           personeller=personeller,
                           departmanlar=departmanlar,
                           pozisyonlar=pozisyonlar)


# --- 2C. PERSONEL DÜZENLEME (YENİ!) ---
@app.route("/personel_duzenle", methods=["POST"])
def personel_duzenle():
    conn = get_connection()
    cursor = conn.cursor()

    personel_id = request.form.get("personel_id")
    ad = request.form.get("ad")
    soyad = request.form.get("soyad")
    tc = request.form.get("tc_kimlik_no")
    telefon = request.form.get("telefon")
    email = request.form.get("email")

    try:
        sql = """
            UPDATE Personel 
            SET ad = %s, soyad = %s, tc_kimlik_no = %s, telefon = %s, email = %s
            WHERE personel_id = %s
        """
        cursor.execute(sql, (ad, soyad, tc, telefon, email, personel_id))
        conn.commit()
        flash("Personel bilgileri başarıyla güncellendi!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Güncelleme hatası: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("personel_list"))


# --- 2D. PERSONEL SİLME (YENİ!) ---
@app.route("/personel_sil", methods=["POST"])
def personel_sil():
    conn = get_connection()
    cursor = conn.cursor()

    personel_id = request.form.get("personel_id")

    try:
        # Personeli pasif yap (silme yerine)
        sql = "UPDATE Personel SET aktif_mi = FALSE WHERE personel_id = %s"
        cursor.execute(sql, (personel_id,))
        conn.commit()
        flash("Personel başarıyla silindi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Silme hatası: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("personel_list"))


# --- 2E. TOPLU SİLME (YENİ!) ---
@app.route("/toplu_sil", methods=["POST"])
def toplu_sil():
    conn = get_connection()
    cursor = conn.cursor()

    personel_ids = request.form.get("personel_ids")

    if not personel_ids:
        flash("Hiç personel seçilmedi!", "warning")
        return redirect(url_for("personel_list"))

    ids = personel_ids.split(',')

    try:
        for pid in ids:
            sql = "UPDATE Personel SET aktif_mi = FALSE WHERE personel_id = %s"
            cursor.execute(sql, (pid,))

        conn.commit()
        flash(f"{len(ids)} personel başarıyla silindi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Toplu silme hatası: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("personel_list"))


# --- 2F. TOPLU DEPARTMAN DEĞİŞTİRME (YENİ!) ---
@app.route("/toplu_departman_degistir", methods=["POST"])
def toplu_departman_degistir():
    conn = get_connection()
    cursor = conn.cursor()

    personel_ids = request.form.get("personel_ids")
    departman_id = request.form.get("departman_id")

    if not personel_ids or not departman_id:
        flash("Gerekli bilgiler eksik!", "warning")
        return redirect(url_for("personel_list"))

    ids = personel_ids.split(',')

    try:
        for pid in ids:
            sql = "UPDATE Personel SET departman_id = %s WHERE personel_id = %s"
            cursor.execute(sql, (departman_id, pid))

        conn.commit()
        flash(f"{len(ids)} personelin departmanı başarıyla değiştirildi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Departman değiştirme hatası: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("personel_list"))


# --- 2G. TOPLU POZİSYON DEĞİŞTİRME (YENİ!) ---
@app.route("/toplu_pozisyon_degistir", methods=["POST"])
def toplu_pozisyon_degistir():
    conn = get_connection()
    cursor = conn.cursor()

    personel_ids = request.form.get("personel_ids")
    pozisyon_id = request.form.get("pozisyon_id")

    if not personel_ids or not pozisyon_id:
        flash("Gerekli bilgiler eksik!", "warning")
        return redirect(url_for("personel_list"))

    ids = personel_ids.split(',')

    try:
        for pid in ids:
            # Eski pozisyonu pasif yap
            sql_old = "UPDATE Personel_Pozisyon SET guncel_mi = FALSE WHERE personel_id = %s AND guncel_mi = TRUE"
            cursor.execute(sql_old, (pid,))

            # Yeni pozisyon ekle
            sql_new = """
                INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                VALUES (%s, %s, CURDATE(), TRUE)
            """
            cursor.execute(sql_new, (pid, pozisyon_id))

        conn.commit()
        flash(f"{len(ids)} personelin pozisyonu başarıyla değiştirildi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Pozisyon değiştirme hatası: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("personel_list"))


# --- 2H. TOPLU PDF İNDİRME (YENİ!) ---
@app.route("/personel_pdf")
def personel_pdf():
    ids = request.args.get('ids', '')

    if not ids:
        flash("Hiç personel seçilmedi!", "warning")
        return redirect(url_for("personel_list"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Seçili personelleri getir
        id_list = ids.split(',')
        placeholders = ','.join(['%s'] * len(id_list))

        sql = f"""
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
            WHERE p.personel_id IN ({placeholders}) AND p.aktif_mi = TRUE
        """
        cursor.execute(sql, id_list)
        personeller = cursor.fetchall()

        # PDF oluştur
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.personel_listesi_pdf(personeller)

        conn.close()

        # PDF'i indir
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'personel_listesi_{datetime.date.today()}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"PDF Hatası: {e}")
        flash(f"PDF oluşturma hatası: {str(e)}", "danger")
        conn.close()
        return redirect(url_for("personel_list"))


# --- 2I. TÜM PERSONEL LİSTESİ PDF ---
@app.route("/tum_personel_pdf")
def tum_personel_pdf():
    conn = get_connection()
    cursor = conn.cursor()

    try:
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
        cursor.execute(sql)
        personeller = cursor.fetchall()

        # PDF oluştur
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.personel_listesi_pdf(personeller)

        conn.close()

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'tum_personel_{datetime.date.today()}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"PDF Hatası: {e}")
        flash(f"PDF oluşturma hatası: {str(e)}", "danger")
        conn.close()
        return redirect(url_for("personel_list"))


# --- 2J. TEK PERSONEL DETAY PDF ---
@app.route("/personel/<int:personel_id>/pdf")
def personel_detay_pdf(personel_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Personel bilgileri
        sql_personel = """
            SELECT 
                p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, p.email,
                p.dogum_tarihi, p.ise_giris_tarihi, p.adres,
                d.departman_adi,
                poz.pozisyon_adi,
                poz.taban_maas
            FROM Personel p
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = TRUE
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.personel_id = %s AND p.aktif_mi = TRUE
        """
        cursor.execute(sql_personel, (personel_id,))
        personel = cursor.fetchone()

        if not personel:
            flash("Personel bulunamadı!", "danger")
            return redirect(url_for("personel_list"))

        # İzin geçmişi
        sql_izinler = """
            SELECT 
                ik.baslangic_tarihi, ik.bitis_tarihi, ik.gun_sayisi, 
                ik.onay_durumu, it.izin_adi
            FROM Izin_Kayit ik
            JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
            WHERE ik.personel_id = %s
            ORDER BY ik.baslangic_tarihi DESC
            LIMIT 10
        """
        cursor.execute(sql_izinler, (personel_id,))
        izinler = cursor.fetchall()

        # Devam özeti
        sql_devam = """
            SELECT 
                durum,
                COUNT(*) as adet
            FROM Devam
            WHERE personel_id = %s 
            AND tarih >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY durum
        """
        cursor.execute(sql_devam, (personel_id,))
        devam_ozet = cursor.fetchall()

        # Maaş bordroları
        sql_maas = """
            SELECT 
                donem_yil, donem_ay, brut_maas, 
                toplam_ekleme, toplam_kesinti, net_maas,
                odeme_tarihi, odendi_mi
            FROM Maas_Hesap
            WHERE personel_id = %s
            ORDER BY donem_yil DESC, donem_ay DESC
            LIMIT 6
        """
        cursor.execute(sql_maas, (personel_id,))
        maaslar = cursor.fetchall()

        # PDF oluştur
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.personel_detay_pdf(personel, izinler, devam_ozet, maaslar)

        conn.close()

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'personel_detay_{personel["ad"]}_{personel["soyad"]}_{datetime.date.today()}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"PDF Hatası: {e}")
        flash(f"PDF oluşturma hatası: {str(e)}", "danger")
        conn.close()
        return redirect(url_for("personel_list"))


# --- 2B. PERSONEL DETAY SAYFASI ---
@app.route("/personel/<int:personel_id>")
def personel_detay(personel_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Personel Bilgileri
        sql_personel = """
            SELECT 
                p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, p.email,
                p.dogum_tarihi, p.ise_giris_tarihi, p.adres,
                d.departman_adi,
                poz.pozisyon_adi,
                poz.taban_maas
            FROM Personel p
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = TRUE
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.personel_id = %s AND p.aktif_mi = TRUE
        """
        cursor.execute(sql_personel, (personel_id,))
        personel = cursor.fetchone()

        if not personel:
            flash("Personel bulunamadı!", "danger")
            return redirect(url_for("personel_list"))

        # İzin Geçmişi
        sql_izinler = """
            SELECT 
                ik.baslangic_tarihi, ik.bitis_tarihi, ik.gun_sayisi, 
                ik.onay_durumu, it.izin_adi
            FROM Izin_Kayit ik
            JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
            WHERE ik.personel_id = %s
            ORDER BY ik.baslangic_tarihi DESC
            LIMIT 10
        """
        cursor.execute(sql_izinler, (personel_id,))
        izinler = cursor.fetchall()

        # Devam Özeti (Son 30 gün)
        sql_devam = """
            SELECT 
                durum,
                COUNT(*) as adet
            FROM Devam
            WHERE personel_id = %s 
            AND tarih >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY durum
        """
        cursor.execute(sql_devam, (personel_id,))
        devam_ozet = cursor.fetchall()

        # Maaş Bordroları (Son 6 ay)
        sql_maas = """
            SELECT 
                donem_yil, donem_ay, brut_maas, 
                toplam_ekleme, toplam_kesinti, net_maas,
                odeme_tarihi, odendi_mi
            FROM Maas_Hesap
            WHERE personel_id = %s
            ORDER BY donem_yil DESC, donem_ay DESC
            LIMIT 6
        """
        cursor.execute(sql_maas, (personel_id,))
        maaslar = cursor.fetchall()

    except Exception as e:
        print(f"Detay Hatası: {e}")
        flash(f"Bir hata oluştu: {str(e)}", "danger")
        return redirect(url_for("personel_list"))
    finally:
        conn.close()

    return render_template("personel_detay.html",
                           personel=personel,
                           izinler=izinler,
                           devam_ozet=devam_ozet,
                           maaslar=maaslar)


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
            sql_p = """
                INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, departman_id, ise_giris_tarihi) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_p, (tc, ad, soyad, dogum, tel, email, dept_id, ise_giris))
            yeni_id = cursor.lastrowid

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

    # Filtre parametresi
    filtre = request.args.get('filtre', 'tumunu')

    try:
        # SQL sorgusu filtreye göre değişiyor
        if filtre == 'bekleyen':
            where_clause = "WHERE k.onay_durumu = 'Beklemede'"
        elif filtre == 'onaylanan':
            where_clause = "WHERE k.onay_durumu = 'Onaylandi'"
        elif filtre == 'reddedilen':
            where_clause = "WHERE k.onay_durumu = 'Reddedildi'"
        else:
            where_clause = ""

        sql_list = f"""
            SELECT k.*, p.ad, p.soyad, t.izin_adi 
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            JOIN Izin_Turu t ON k.izin_turu_id = t.izin_turu_id
            {where_clause}
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
    return render_template("izin.html", izinler=izinler, personeller=personeller, izin_turleri=izin_turleri,
                           filtre=filtre)


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

                cursor.execute("DELETE FROM Devam WHERE personel_id = %s AND tarih = %s", (personel_id, secilen_tarih))

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


# --- 7. İZİN ONAYLAMA/REDDETME (YENİ!) ---
@app.route("/izin_onayla/<int:izin_id>", methods=["POST"])
def izin_onayla(izin_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = "UPDATE Izin_Kayit SET onay_durumu = 'Onaylandi' WHERE izin_kayit_id = %s"
        cursor.execute(sql, (izin_id,))
        conn.commit()
        flash("İzin talebi onaylandı!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("izin"))


@app.route("/izin_reddet/<int:izin_id>", methods=["POST"])
def izin_reddet(izin_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = "UPDATE Izin_Kayit SET onay_durumu = 'Reddedildi' WHERE izin_kayit_id = %s"
        cursor.execute(sql, (izin_id,))
        conn.commit()
        flash("İzin talebi reddedildi.", "warning")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("izin"))


# --- 8. MAAŞ BORDROSU ---
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


# --- 9. RAPOR SAYFALARI (YENİ - PLACEHOLDER) ---
@app.route("/rapor/personel")
def rapor_personel():
    flash("Personel raporu sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


@app.route("/rapor/devam")
def rapor_devam():
    flash("Devam raporu sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


@app.route("/rapor/izin")
def rapor_izin():
    flash("İzin raporu sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


# --- 10. AYARLAR SAYFALARI (YENİ - PLACEHOLDER) ---
@app.route("/ayarlar/departmanlar")
def ayarlar_departmanlar():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Departmanları ve her birindeki personel sayısını getir
        sql = """
            SELECT 
                d.departman_id,
                d.departman_adi,
                COUNT(p.personel_id) as personel_sayisi
            FROM Departman d
            LEFT JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = TRUE
            GROUP BY d.departman_id, d.departman_adi
            ORDER BY d.departman_adi
        """
        cursor.execute(sql)
        departmanlar = cursor.fetchall()
    except Exception as e:
        print(f"Departman listesi hatası: {e}")
        departmanlar = []

    conn.close()
    return render_template("departmanlar.html", departmanlar=departmanlar)


@app.route("/ayarlar/departman_ekle", methods=["POST"])
def departman_ekle():
    conn = get_connection()
    cursor = conn.cursor()

    departman_adi = request.form.get("departman_adi")

    try:
        sql = "INSERT INTO Departman (departman_adi) VALUES (%s)"
        cursor.execute(sql, (departman_adi,))
        conn.commit()
        flash(f"{departman_adi} departmanı başarıyla eklendi!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("ayarlar_departmanlar"))


@app.route("/ayarlar/departman_duzenle", methods=["POST"])
def departman_duzenle():
    conn = get_connection()
    cursor = conn.cursor()

    departman_id = request.form.get("departman_id")
    departman_adi = request.form.get("departman_adi")

    try:
        sql = "UPDATE Departman SET departman_adi = %s WHERE departman_id = %s"
        cursor.execute(sql, (departman_adi, departman_id))
        conn.commit()
        flash("Departman başarıyla güncellendi!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("ayarlar_departmanlar"))


@app.route("/ayarlar/departman_sil", methods=["POST"])
def departman_sil():
    conn = get_connection()
    cursor = conn.cursor()

    departman_id = request.form.get("departman_id")

    try:
        # Önce bu departmanda personel var mı kontrol et
        cursor.execute("SELECT COUNT(*) as sayi FROM Personel WHERE departman_id = %s AND aktif_mi = TRUE",
                       (departman_id,))
        result = cursor.fetchone()

        if result and result['sayi'] > 0:
            flash("Bu departmanda personel bulunuyor! Önce personelleri başka departmana taşıyın.", "warning")
        else:
            sql = "DELETE FROM Departman WHERE departman_id = %s"
            cursor.execute(sql, (departman_id,))
            conn.commit()
            flash("Departman başarıyla silindi!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("ayarlar_departmanlar"))


@app.route("/ayarlar/pozisyonlar")
def ayarlar_pozisyonlar():
    flash("Pozisyon yönetimi sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


@app.route("/ayarlar/izin-turleri")
def ayarlar_izin_turleri():
    flash("İzin türleri yönetimi sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


@app.route("/ayarlar/duyurular")
def ayarlar_duyurular():
    flash("Duyuru yönetimi sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


# --- 11. PROFİL & ÇIKIŞ (YENİ - PLACEHOLDER) ---
@app.route("/profil")
def profil():
    flash("Profil ayarları sayfası yakında eklenecek!", "info")
    return redirect(url_for("home"))


@app.route("/cikis")
def cikis():
    flash("Çıkış yapıldı! (Login sistemi eklenince aktif olacak)", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)