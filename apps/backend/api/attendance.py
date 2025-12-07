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
        LEFT JOIN Devam dv ON p.personel_id = dv.personel_id AND dv.tarih = ?
        WHERE p.aktif_mi = 1
        ORDER BY p.ad, p.soyad
    """
    cursor.execute(sql, (secilen_tarih,))
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
            
            if not personel_id or not durum:
                continue

            cursor.execute("DELETE FROM Devam WHERE personel_id = ? AND tarih = ?", (personel_id, secilen_tarih))
            cursor.execute("INSERT INTO Devam (personel_id, tarih, durum) VALUES (?, ?, ?)", 
                          (personel_id, secilen_tarih, durum))

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
            FROM Devam WHERE tarih = ?
        """, (bugun,))
        row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM Personel WHERE aktif_mi = 1")
        toplam = cursor.fetchone()[0]
        
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
