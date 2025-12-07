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
        cursor.execute("SELECT COUNT(*) FROM Devam WHERE tarih = ? AND durum = 'Izinli'", (bugun,))
        row = cursor.fetchone()
        if row:
            izinli_sayisi = row[0]

        cursor.execute("SELECT COUNT(*) FROM Personel WHERE aktif_mi = 1")
        row = cursor.fetchone()
        if row:
            toplam_personel = row[0]

        cursor.execute("SELECT COUNT(*) FROM Izin_Kayit WHERE onay_durumu = 'Beklemede'")
        row = cursor.fetchone()
        if row:
            bekleyen_isler = row[0]

        cursor.execute("""
            SELECT d.departman_adi, COUNT(p.personel_id) as sayi
            FROM Departman d
            LEFT JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = 1
            GROUP BY d.departman_id, d.departman_adi
            HAVING sayi > 0
        """)
        departman_data = [{'departman_adi': row[0], 'sayi': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT strftime('%Y-%m', tarih) as ay, COUNT(*) as sayi
            FROM Devam
            WHERE durum = 'Devamsiz' 
            AND tarih >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', tarih)
            ORDER BY ay ASC
        """)
        devamsizlik_data = [{'ay': row[0], 'sayi': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT onay_durumu, COUNT(*) as sayi
            FROM Izin_Kayit
            WHERE baslangic_tarihi >= date('now', '-3 months')
            GROUP BY onay_durumu
        """)
        izin_stats = [{'onay_durumu': row[0], 'sayi': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT d.departman_adi, ROUND(AVG(poz.taban_maas), 2) as ort_maas
            FROM Departman d
            JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = 1
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            GROUP BY d.departman_id, d.departman_adi
            HAVING ort_maas IS NOT NULL
        """)
        maas_dept_data = [{'departman_adi': row[0], 'ort_maas': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT 'izin' as tip, p.ad || ' ' || p.soyad as personel, 
                   'İzin talebi oluşturdu' as aksiyon, k.baslangic_tarihi as tarih
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            ORDER BY k.izin_kayit_id DESC
            LIMIT 5
        """)
        son_aktiviteler = [{'tip': row[0], 'personel': row[1], 'aksiyon': row[2], 'tarih': row[3]} for row in cursor.fetchall()]

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
