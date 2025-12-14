from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
import datetime

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api')


@attendance_bp.route("/attendance", methods=["GET"])
@login_required
def attendance():
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
        WHERE p.aktif_mi = %s
        ORDER BY p.ad, p.soyad
    """
    archived = request.args.get('archived', '0')
    aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1
    cursor.execute(sql, (secilen_tarih, aktif_flag))
    rows = cursor.fetchall()
    conn.close()

    personeller = [{
        'personel_id': row['personel_id'],
        'tc_kimlik_no': row['tc_kimlik_no'],
        'ad': row['ad'],
        'soyad': row['soyad'],
        'departman_adi': row['departman_adi'],
        'bugunku_durum': row['bugunku_durum']
    } for row in rows]

    return jsonify({
        'tarih': secilen_tarih,
        'personeller': personeller
    })


@attendance_bp.route("/attendance/pdf", methods=["GET"])
@login_required
def attendance_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({'error': 'start ve end tarihleri gerekli (YYYY-MM-DD)'}), 400
    archived = request.args.get('archived', '0')
    aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.tarih, p.ad, p.soyad, dep.departman_adi, d.durum
            FROM Devam d
            JOIN Personel p ON d.personel_id = p.personel_id
            LEFT JOIN Departman dep ON p.departman_id = dep.departman_id
            WHERE d.tarih BETWEEN %s AND %s AND p.aktif_mi = %s
            ORDER BY d.tarih, p.ad
        """, (start, end, aktif_flag))
        rows = cursor.fetchall()
        gen = PDFGenerator()
        buffer = gen.devam_raporu_pdf(rows, start, end)
        fname = f"devam_raporu_{start}_to_{end}.pdf"
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=fname)
    except Exception as e:
        print('Devam PDF hatası:', e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@attendance_bp.route("/attendance", methods=["POST"])
@admin_required
def attendance_save():
    data = request.get_json()
    
    secilen_tarih = data.get('tarih')
    kayitlar = data.get('kayitlar', [])
    
    if not secilen_tarih:
        secilen_tarih = datetime.date.today().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for kayit in kayitlar:
            personel_id = kayit.get('personel_id')
            durum = kayit.get('durum')
            ek_mesai = kayit.get('ek_mesai_saat', 0) or 0
            
            if not personel_id or not durum:
                continue

            cursor.execute("DELETE FROM Devam WHERE personel_id = %s AND tarih = %s", (personel_id, secilen_tarih))
            cursor.execute("INSERT INTO Devam (personel_id, tarih, durum, ek_mesai_saat) VALUES (%s, %s, %s, %s)", 
                          (personel_id, secilen_tarih, durum, ek_mesai))
            if durum == 'Izinli':
                cursor.execute("SELECT izin_turu_id, izin_adi, ucretli_mi, yillik_hak_gun FROM Izin_Turu WHERE izin_adi = %s LIMIT 1", ('Mazeret İzni',))
                tur = cursor.fetchone()
                if not tur:
                    cursor.execute("SELECT izin_turu_id FROM Izin_Turu WHERE izin_adi = %s LIMIT 1", ('Ücretsiz İzin',))
                    tur = cursor.fetchone()
                if not tur:
                    cursor.execute("SELECT izin_turu_id FROM Izin_Turu LIMIT 1")
                    tur = cursor.fetchone()

                izin_turu_id = tur['izin_turu_id'] if tur else None
                if izin_turu_id:
                    cursor.execute("SELECT COUNT(*) AS cnt FROM Izin_Kayit WHERE personel_id = %s AND baslangic_tarihi <= %s AND bitis_tarihi >= %s", (personel_id, secilen_tarih, secilen_tarih))
                    if cursor.fetchone().get('cnt', 0) == 0:
                        cursor.execute("INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu) VALUES (%s, %s, %s, %s, %s, 'Onaylandi')", (personel_id, izin_turu_id, secilen_tarih, secilen_tarih, 1))

        conn.commit()
        return jsonify({'message': f'{secilen_tarih} tarihi için yoklama kaydedildi'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@attendance_bp.route("/attendance/stats", methods=["GET"])
@login_required
def attendance_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        bugun = datetime.date.today().strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN durum = 'Normal' THEN 1 END) as geldi,
                COUNT(CASE WHEN durum = 'Izinli' THEN 1 END) as izinli,
                COUNT(CASE WHEN durum = 'Devamsiz' THEN 1 END) as devamsiz
            FROM Devam WHERE tarih = %s
        """, (bugun,))
        row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as cnt FROM Personel WHERE aktif_mi = 1")
        toplam = cursor.fetchone()['cnt']
        
        return jsonify({
            'tarih': bugun,
            'toplam': toplam,
            'geldi': row['geldi'] or 0,
            'izinli': row['izinli'] or 0,
            'devamsiz': row['devamsiz'] or 0,
            'belirsiz': toplam - ((row['geldi'] or 0) + (row['izinli'] or 0) + (row['devamsiz'] or 0))
        })
    finally:
        conn.close()
