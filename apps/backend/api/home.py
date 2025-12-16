from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, decode_token
import datetime

home_bp = Blueprint('home', __name__, url_prefix='/api')


@home_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    bugun = datetime.date.today().strftime('%Y-%m-%d')

    # Kullanıcı rolü ve personel bilgisi
    auth_header = request.headers.get('Authorization')
    user_role = None
    current_personel_id = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        if payload:
            user_role = payload.get('role')
            current_personel_id = payload.get('personel_id')

    izinli_sayisi = 0
    toplam_personel = 0
    bekleyen_isler = 0
    odenen_maas = 0.0
    maas_butce_oran = 0.0
    personel_artis_oran = 0.0

    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM Devam WHERE tarih = %s AND durum = 'Izinli'", (bugun,))
        row = cursor.fetchone()
        if row:
            izinli_sayisi = row['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM Personel WHERE aktif_mi = 1")
        row = cursor.fetchone()
        if row:
            toplam_personel = row['cnt']

        # Bekleyen işler: admin için tüm sistem, çalışan için sadece kendisi
        if user_role == 'admin' or not current_personel_id:
            cursor.execute("SELECT COUNT(*) as cnt FROM Izin_Kayit WHERE onay_durumu = 'Beklemede'")
        else:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM Izin_Kayit WHERE onay_durumu = 'Beklemede' AND personel_id = %s",
                (current_personel_id,),
            )
        row = cursor.fetchone()
        if row:
            bekleyen_isler = row['cnt']

        # Aktif personeller için güncel net maaş toplamı
        # - Her personel için en güncel Maas_Hesap kaydının net_maas'ı
        # - Eğer hiç bordro yoksa ilgili pozisyonun taban_maas'ı kullanılır
        cursor.execute(
            """
            WITH latest_payroll AS (
                SELECT mh.personel_id,
                       mh.net_maas,
                       ROW_NUMBER() OVER (
                         PARTITION BY mh.personel_id
                         ORDER BY mh.donem_yil DESC, mh.donem_ay DESC, mh.maas_hesap_id DESC
                       ) AS rn
                FROM Maas_Hesap mh
            )
            SELECT COALESCE(SUM(COALESCE(lp.net_maas, poz.taban_maas, 0)), 0) AS toplam_net
            FROM Personel p
            LEFT JOIN latest_payroll lp
              ON lp.personel_id = p.personel_id AND lp.rn = 1
            LEFT JOIN Personel_Pozisyon pp
              ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz
              ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.aktif_mi = 1
            """
        )
        row = cursor.fetchone()
        odenen_maas = float(row.get("toplam_net", 0) or 0) if row else 0.0

        # Aktif personel için teorik maaş bütçesi (taban maaşların toplamı)
        cursor.execute(
            """
            SELECT COALESCE(SUM(poz.taban_maas), 0) AS butce
            FROM Personel p
            LEFT JOIN Personel_Pozisyon pp
                ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz
                ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.aktif_mi = 1
            """
        )
        row = cursor.fetchone()
        butce = float(row.get("butce", 0) or 0) if row else 0.0
        if butce > 0:
            maas_butce_oran = round((odenen_maas / butce) * 100, 1)

        # Son 30 güne göre personel artış oranı
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM Personel
            WHERE aktif_mi = 1
              AND ise_giris_tarihi <= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """
        )
        row = cursor.fetchone()
        onceki_personel = int(row.get("cnt", 0) or 0) if row else 0
        if onceki_personel > 0:
            personel_artis_oran = round(
                ((toplam_personel - onceki_personel) / onceki_personel) * 100, 1
            )

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

        # İzin istatistikleri: admin için tüm sistem, çalışan için sadece kendisi
        # Not: Önceden sadece son 3 aylık izinler hesaba katılıyordu.
        # Kullanıcıların dashboard'da tüm izin durumlarını görebilmesi için tarih filtresi kaldırıldı.
        if user_role == 'admin' or not current_personel_id:
            cursor.execute(
                """
                SELECT onay_durumu, COUNT(*) as sayi
                FROM Izin_Kayit
                GROUP BY onay_durumu
                """
            )
        else:
            cursor.execute(
                """
                SELECT onay_durumu, COUNT(*) as sayi
                FROM Izin_Kayit
                WHERE personel_id = %s
                GROUP BY onay_durumu
                """,
                (current_personel_id,),
            )
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

        cursor.execute("""
            SELECT d.duyuru_id,
                   d.baslik,
                   d.icerik,
                   d.yayin_tarihi,
                   d.oncelik
            FROM Duyuru d
            WHERE d.aktif_mi = 1
            ORDER BY d.yayin_tarihi DESC
            LIMIT 5
        """)
        duyurular = [{
            'duyuru_id': row['duyuru_id'],
            'baslik': row['baslik'],
            'icerik': row['icerik'],
            'yayin_tarihi': str(row['yayin_tarihi']) if row['yayin_tarihi'] else None,
            'oncelik': row['oncelik'],
        } for row in cursor.fetchall()]

        cursor.execute("""
            SELECT a.aday_id,
                   a.ad,
                   a.soyad,
                   a.basvuru_tarihi,
                   a.durum,
                   p.pozisyon_adi
            FROM Adaylar a
            JOIN Pozisyon p ON a.pozisyon_id = p.pozisyon_id
            ORDER BY a.basvuru_tarihi DESC, a.aday_id DESC
            LIMIT 5
        """)
        adaylar = [{
            'aday_id': row['aday_id'],
            'ad': row['ad'],
            'soyad': row['soyad'],
            'basvuru_tarihi': str(row['basvuru_tarihi']) if row['basvuru_tarihi'] else None,
            'durum': row['durum'],
            'pozisyon_adi': row['pozisyon_adi'],
        } for row in cursor.fetchall()]

    except Exception as e:
        print("Dashboard Hatası:", repr(e))
        departman_data = []
        devamsizlik_data = []
        izin_stats = []
        maas_dept_data = []
        son_aktiviteler = []
        duyurular = []
        adaylar = []

    finally:
        conn.close()

    return jsonify({
        'stats': {
            'izinli': izinli_sayisi,
            'toplam': toplam_personel,
            'kalan_calisan': toplam_personel - izinli_sayisi,
            'bekleyen': bekleyen_isler,
            'odenen_maas': odenen_maas,
            'maas_butce_oran': maas_butce_oran,
            'personel_artis_oran': personel_artis_oran
        },
        'departman_data': departman_data,
        'devamsizlik_data': devamsizlik_data,
        'izin_stats': izin_stats,
        'maas_dept_data': maas_dept_data,
        'son_aktiviteler': son_aktiviteler,
        'duyurular': duyurular,
        'adaylar': adaylar
    })
