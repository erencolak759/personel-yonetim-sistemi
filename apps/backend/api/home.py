from flask import Blueprint, jsonify
from utils.db import get_connection
from api.auth import login_required
import datetime

home_bp = Blueprint('home', __name__, url_prefix='/api')


@home_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    bugun = datetime.date.today().strftime('%Y-%m-%d')

    izinli_sayisi = 0
    toplam_personel = 0
    bekleyen_isler = 0

    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM Devam WHERE tarih = %s AND durum = 'Izinli'", (bugun,))
        row = cursor.fetchone()
        if row:
            izinli_sayisi = row['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM Personel WHERE aktif_mi = 1")
        row = cursor.fetchone()
        if row:
            toplam_personel = row['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM Izin_Kayit WHERE onay_durumu = 'Beklemede'")
        row = cursor.fetchone()
        if row:
            bekleyen_isler = row['cnt']

        cursor.execute("""
            SELECT d.departman_adi, COUNT(p.personel_id) as sayi
            FROM Departman d
            LEFT JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = 1
            GROUP BY d.departman_id, d.departman_adi
            HAVING COUNT(p.personel_id) > 0
        """)
        departman_data = [{'departman_adi': row['departman_adi'], 'sayi': row['sayi']} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DATE_FORMAT(tarih, '%Y-%m') as ay, COUNT(*) as sayi
            FROM Devam
            WHERE durum = 'Devamsiz' 
            AND tarih >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(tarih, '%Y-%m')
            ORDER BY ay ASC
        """)
        devamsizlik_data = [{'ay': row['ay'], 'sayi': row['sayi']} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT onay_durumu, COUNT(*) as sayi
            FROM Izin_Kayit
            WHERE baslangic_tarihi >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            GROUP BY onay_durumu
        """)
        izin_stats = [{'onay_durumu': row['onay_durumu'], 'sayi': row['sayi']} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT d.departman_adi, ROUND(AVG(poz.taban_maas), 2) as ort_maas
            FROM Departman d
            JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = 1
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            GROUP BY d.departman_id, d.departman_adi
            HAVING AVG(poz.taban_maas) IS NOT NULL
        """)
        maas_dept_data = [{'departman_adi': row['departman_adi'], 'ort_maas': float(row['ort_maas'])} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT 'izin' as tip, CONCAT(p.ad, ' ', p.soyad) as personel, 
                   'İzin talebi oluşturdu' as aksiyon, k.baslangic_tarihi as tarih
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            ORDER BY k.izin_kayit_id DESC
            LIMIT 5
        """)
        son_aktiviteler = [{'tip': row['tip'], 'personel': row['personel'], 'aksiyon': row['aksiyon'], 'tarih': str(row['tarih'])} for row in cursor.fetchall()]

    except Exception as e:
        print("Dashboard Hatası:", repr(e))
        departman_data = []
        devamsizlik_data = []
        izin_stats = []
        maas_dept_data = []
        son_aktiviteler = []

    finally:
        conn.close()

    return jsonify({
        'stats': {
            'izinli': izinli_sayisi,
            'toplam': toplam_personel,
            'kalan_calisan': toplam_personel - izinli_sayisi,
            'bekleyen': bekleyen_isler
        },
        'departman_data': departman_data,
        'devamsizlik_data': devamsizlik_data,
        'izin_stats': izin_stats,
        'maas_dept_data': maas_dept_data,
        'son_aktiviteler': son_aktiviteler
    })
