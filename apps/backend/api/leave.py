from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
from api.auth import decode_token
from datetime import datetime

leave_bp = Blueprint('leave', __name__, url_prefix='/api')


@leave_bp.route("/leaves", methods=["GET"])
@login_required
def leaves():
    conn = get_connection()
    cursor = conn.cursor()

    filtre = request.args.get('filtre', 'tumunu')

    try:
        if filtre == 'bekleyen':
            where_clause = "WHERE k.onay_durumu = 'Beklemede'"
        elif filtre == 'onaylanan':
            where_clause = "WHERE k.onay_durumu = 'Onaylandi'"
        elif filtre == 'reddedilen':
            where_clause = "WHERE k.onay_durumu = 'Reddedildi'"
        else:
            where_clause = ""

        sql_list = f"""
            SELECT k.izin_kayit_id, k.personel_id, k.izin_turu_id,
                   k.baslangic_tarihi, k.bitis_tarihi, k.gun_sayisi, k.onay_durumu,
                   p.ad, p.soyad, t.izin_adi 
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            JOIN Izin_Turu t ON k.izin_turu_id = t.izin_turu_id
            {where_clause}
            ORDER BY k.baslangic_tarihi DESC
        """
        cursor.execute(sql_list)
        rows = cursor.fetchall()

        izinler = [{
            'izin_kayit_id': row['izin_kayit_id'],
            'personel_id': row['personel_id'],
            'izin_turu_id': row['izin_turu_id'],
            'baslangic_tarihi': row['baslangic_tarihi'],
            'bitis_tarihi': row['bitis_tarihi'],
            'gun_sayisi': row['gun_sayisi'],
            'onay_durumu': row['onay_durumu'],
            'ad': row['ad'],
            'soyad': row['soyad'],
            'izin_adi': row['izin_adi']
        } for row in rows]

        return jsonify(izinler)
    except Exception as e:
        print(f"İzin listesi hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@leave_bp.route("/leaves", methods=["POST"])
@login_required
def create_leave():
    data = request.get_json()
    
    personel_id = data.get('personel_id')
    izin_turu_id = data.get('izin_turu_id')
    baslangic = data.get('baslangic_tarihi')
    bitis = data.get('bitis_tarihi')
    gun_sayisi = data.get('gun_sayisi')

    if not all([personel_id, izin_turu_id, baslangic, bitis]):
        return jsonify({'error': 'Gerekli alanlar eksik'}), 400

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

    if payload.get('role') != 'admin':
        caller_personel = payload.get('personel_id')
        if caller_personel is None or int(caller_personel) != int(personel_id):
            return jsonify({'error': 'Sadece kendi için izin talebi oluşturabilirsiniz'}), 403

    if gun_sayisi is None:
        try:
            dt_start = datetime.strptime(baslangic, '%Y-%m-%d')
            dt_end = datetime.strptime(bitis, '%Y-%m-%d')
            delta = (dt_end - dt_start).days + 1
            gun_sayisi = max(1, delta)
        except Exception as e:
            return jsonify({'error': 'Tarih formatı hatalı veya gun_sayisi eksik'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu)
            VALUES (%s, %s, %s, %s, %s, 'Beklemede')
        """, (personel_id, izin_turu_id, baslangic, bitis, gun_sayisi))
        conn.commit()
        return jsonify({'message': 'İzin talebi oluşturuldu', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@leave_bp.route("/leaves/<int:izin_id>/approve", methods=["POST"])
@admin_required
def leave_approve(izin_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE Izin_Kayit SET onay_durumu = 'Onaylandi' WHERE izin_kayit_id = %s", (izin_id,))
        conn.commit()
        return jsonify({'message': 'İzin talebi onaylandı'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@leave_bp.route("/leaves/<int:izin_id>/reject", methods=["POST"])
@admin_required
def leave_reject(izin_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE Izin_Kayit SET onay_durumu = 'Reddedildi' WHERE izin_kayit_id = %s", (izin_id,))
        conn.commit()
        return jsonify({'message': 'İzin talebi reddedildi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@leave_bp.route("/leave-types", methods=["GET"])
@login_required
def get_leave_types():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM Izin_Turu ORDER BY izin_adi")
        rows = cursor.fetchall()
        
        izin_turleri = [{
            'izin_turu_id': row['izin_turu_id'],
            'izin_adi': row['izin_adi'],
            'yillik_hak_gun': row['yillik_hak_gun'],
            'ucretli_mi': bool(row['ucretli_mi'])
        } for row in rows]
        
        return jsonify(izin_turleri)
    finally:
        conn.close()
