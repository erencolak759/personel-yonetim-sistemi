from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
from api.auth import decode_token
from datetime import datetime
from datetime import timedelta

leave_bp = Blueprint('leave', __name__, url_prefix='/api')


@leave_bp.route("/leaves", methods=["GET"])
@login_required
def leaves():
    conn = get_connection()
    cursor = conn.cursor()
    filtre = request.args.get('filtre', 'tumunu')
    archived = request.args.get('archived', '0')
    try:
        aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1
    except Exception:
        aktif_flag = 1

    # Kimlik bilgisi al
    auth_header = request.headers.get('Authorization')
    user_role = None
    current_personel_id = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        if payload:
            user_role = payload.get('role')
            current_personel_id = payload.get('personel_id')

    try:
        conditions = ["p.aktif_mi = %s"]
        params = [aktif_flag]

        # Rol bazlı filtre: admin tüm kayıtları, çalışan sadece kendini görür
        if user_role != 'admin':
            if not current_personel_id:
                return jsonify({'error': 'Personel bilgisi bulunamadı'}), 400
            conditions.append("k.personel_id = %s")
            params.append(current_personel_id)

        if filtre == 'bekleyen':
            conditions.append("k.onay_durumu = 'Beklemede'")
        elif filtre == 'onaylanan':
            conditions.append("k.onay_durumu = 'Onaylandi'")
        elif filtre == 'reddedilen':
            conditions.append("k.onay_durumu = 'Reddedildi'")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

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
        cursor.execute(sql_list, tuple(params))
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


@leave_bp.route("/leaves/pdf", methods=["GET"])
@login_required
def leaves_pdf():
    filtre = request.args.get('filtre', 'tumunu')
    archived = request.args.get('archived', '0')
    aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1

    conn = get_connection()
    cursor = conn.cursor()

    # Kimlik bilgisi al
    auth_header = request.headers.get('Authorization')
    user_role = None
    current_personel_id = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        if payload:
            user_role = payload.get('role')
            current_personel_id = payload.get('personel_id')

    try:
        conditions = []
        if filtre == 'bekleyen':
            conditions.append("k.onay_durumu = 'Beklemede'")
        elif filtre == 'onaylanan':
            conditions.append("k.onay_durumu = 'Onaylandi'")
        elif filtre == 'reddedilen':
            conditions.append("k.onay_durumu = 'Reddedildi'")

        # Çalışanlar sadece kendi izinlerinin PDF'ini görebilsin
        params = [aktif_flag]
        base_condition = "p.aktif_mi = %s"
        if user_role != 'admin':
            if not current_personel_id:
                return jsonify({'error': 'Personel bilgisi bulunamadı'}), 400
            base_condition += " AND k.personel_id = %s"
            params.append(current_personel_id)

        where_clause = "WHERE " + base_condition
        if conditions:
            where_clause += " AND " + " AND ".join(conditions)

        sql = f"""
            SELECT k.baslangic_tarihi as bas, k.bitis_tarihi as bit, k.gun_sayisi, k.onay_durumu,
                   p.ad, p.soyad, t.izin_adi
            FROM Izin_Kayit k
            JOIN Personel p ON k.personel_id = p.personel_id
            JOIN Izin_Turu t ON k.izin_turu_id = t.izin_turu_id
            {where_clause}
            ORDER BY k.baslangic_tarihi DESC
        """
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        gen = PDFGenerator()
        buffer = gen.izin_raporu_pdf(rows, filtre=filtre)
        fname = f"izin_raporu_{filtre}.pdf"
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=fname)
    except Exception as e:
        print('İzin PDF hatası:', e)
        return jsonify({'error': str(e)}), 500
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
        cursor.execute("SELECT izin_adi, yillik_hak_gun, ucretli_mi FROM Izin_Turu WHERE izin_turu_id = %s", (izin_turu_id,))
        izin_turu = cursor.fetchone()
        max_gun = izin_turu.get('yillik_hak_gun') if izin_turu else None
        ucretli = bool(izin_turu.get('ucretli_mi')) if izin_turu else False
        def get_unpaid_type_id():
            cursor.execute("SELECT izin_turu_id FROM Izin_Turu WHERE ucretli_mi = 0 AND izin_adi LIKE %s LIMIT 1", ('%Ücretsiz%',))
            row = cursor.fetchone()
            if row:
                return row['izin_turu_id']
            cursor.execute("INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun, ucretli_mi) VALUES (%s, %s, %s)", ('Ücretsiz İzin', 0, 0))
            return cursor.lastrowid
        if ucretli and max_gun and int(max_gun) > 0:
            try:
                start_dt = datetime.strptime(baslangic, '%Y-%m-%d')
            except Exception:
                start_dt = datetime.strptime(baslangic, '%Y-%m-%d')
            year_start = datetime(start_dt.year, 1, 1).strftime('%Y-%m-%d')
            year_end = datetime(start_dt.year, 12, 31).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COALESCE(SUM(gun_sayisi),0) AS used
                FROM Izin_Kayit ik
                JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
                WHERE ik.personel_id = %s AND ik.izin_turu_id = %s
                  AND NOT (ik.bitis_tarihi < %s OR ik.baslangic_tarihi > %s)
                  AND ik.onay_durumu != 'Reddedildi'
            """, (personel_id, izin_turu_id, year_start, year_end))
            used_row = cursor.fetchone()
            used_days = int(used_row.get('used', 0) or 0)

            remaining_paid = int(max_gun) - used_days
            if remaining_paid <= 0:
                unpaid_days = int(gun_sayisi)
                paid_days = 0
            elif int(gun_sayisi) <= remaining_paid:
                paid_days = int(gun_sayisi)
                unpaid_days = 0
            else:
                paid_days = remaining_paid
                unpaid_days = int(gun_sayisi) - paid_days

            if paid_days > 0:
                paid_start = datetime.strptime(baslangic, '%Y-%m-%d')
                paid_end = (paid_start + timedelta(days=paid_days - 1)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu)
                    VALUES (%s, %s, %s, %s, %s, 'Beklemede')
                """, (personel_id, izin_turu_id, paid_start.strftime('%Y-%m-%d'), paid_end, paid_days))

            if unpaid_days > 0:
                unpaid_type_id = get_unpaid_type_id()
                if paid_days > 0:
                    unpaid_start_dt = datetime.strptime(paid_end, '%Y-%m-%d') + timedelta(days=1)
                else:
                    unpaid_start_dt = datetime.strptime(baslangic, '%Y-%m-%d')
                unpaid_start = unpaid_start_dt.strftime('%Y-%m-%d')
                unpaid_end_dt = datetime.strptime(bitis, '%Y-%m-%d')
                unpaid_end = unpaid_end_dt.strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO Izin_Kayit (personel_id, izin_turu_id, baslangic_tarihi, bitis_tarihi, gun_sayisi, onay_durumu)
                    VALUES (%s, %s, %s, %s, %s, 'Beklemede')
                """, (personel_id, unpaid_type_id, unpaid_start, unpaid_end, unpaid_days))
        else:
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


@leave_bp.route("/leaves/<int:izin_id>/cancel", methods=["POST"])
@login_required
def leave_cancel(izin_id):
    conn = get_connection()
    cursor = conn.cursor()

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

    try:
        cursor.execute("SELECT personel_id, onay_durumu FROM Izin_Kayit WHERE izin_kayit_id = %s", (izin_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'İzin kaydı bulunamadı'}), 404

        if row.get('onay_durumu') != 'Beklemede':
            return jsonify({'error': 'Sadece beklemedeki izinler iptal edilebilir'}), 400
        caller_role = payload.get('role')
        caller_personel = payload.get('personel_id')
        if caller_role != 'admin' and int(caller_personel) != int(row.get('personel_id')):
            return jsonify({'error': 'Bu izni iptal etme yetkiniz yok'}), 403

        cursor.execute("UPDATE Izin_Kayit SET onay_durumu = 'Iptal' WHERE izin_kayit_id = %s", (izin_id,))
        conn.commit()
        return jsonify({'message': 'İzin talebi iptal edildi'})
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
