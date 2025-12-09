from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
import datetime
from api.auth import decode_token
from flask import request, jsonify
from werkzeug.security import generate_password_hash

employee_bp = Blueprint('employee', __name__, url_prefix='/api')


@employee_bp.route("/employees/form-data", methods=["GET"])
@login_required
def employee_form_data():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT departman_id, departman_adi FROM Departman ORDER BY departman_adi")
        departmanlar = [
            {"departman_id": row["departman_id"], "departman_adi": row["departman_adi"]}
            for row in cursor.fetchall()
        ]

        cursor.execute("SELECT pozisyon_id, pozisyon_adi, departman_id, taban_maas FROM Pozisyon ORDER BY pozisyon_adi")
        pozisyonlar = [
            {
                "pozisyon_id": row["pozisyon_id"],
                "pozisyon_adi": row["pozisyon_adi"],
                "departman_id": row.get("departman_id") if isinstance(row, dict) else row[2],
                "taban_maas": row.get("taban_maas") if isinstance(row, dict) else row[3],
            }
            for row in cursor.fetchall()
        ]

        return jsonify({"departmanlar": departmanlar, "pozisyonlar": pozisyonlar})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees", methods=["GET"])
@login_required
def employee_list():
    conn = get_connection()
    cursor = conn.cursor()

    search = request.args.get('search', '')
    department = request.args.get('department', '')

    sql = """
        SELECT 
            p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, p.email,
            p.ise_giris_tarihi, p.dogum_tarihi, p.adres, p.aktif_mi,
            d.departman_id, d.departman_adi,
            poz.pozisyon_id, poz.pozisyon_adi,
            poz.taban_maas
        FROM Personel p
        LEFT JOIN Departman d ON p.departman_id = d.departman_id
        LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
        LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
        WHERE p.aktif_mi = 1
    """
    params = []

    if search:
        sql += " AND (p.ad LIKE %s OR p.soyad LIKE %s OR p.tc_kimlik_no LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    if department:
        sql += " AND p.departman_id = %s"
        params.append(department)

    sql += " ORDER BY p.personel_id DESC"

    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        personeller = [{
            'personel_id': row['personel_id'],
            'tc_kimlik_no': row['tc_kimlik_no'],
            'ad': row['ad'],
            'soyad': row['soyad'],
            'telefon': row['telefon'],
            'email': row['email'],
            'ise_giris_tarihi': row['ise_giris_tarihi'],
            'dogum_tarihi': row['dogum_tarihi'],
            'adres': row['adres'],
            'aktif_mi': bool(row['aktif_mi']),
            'departman_id': row['departman_id'],
            'departman_adi': row['departman_adi'],
            'pozisyon_id': row['pozisyon_id'],
            'pozisyon_adi': row['pozisyon_adi'],
            'taban_maas': row['taban_maas']
        } for row in rows]

        return jsonify(personeller)
    except Exception as e:
        print(f"Liste Hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@employee_bp.route("/employees/<int:personel_id>", methods=["GET"])
@login_required
def employee_detail(personel_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                p.personel_id, p.tc_kimlik_no, p.ad, p.soyad, p.telefon, p.email,
                p.ise_giris_tarihi, p.dogum_tarihi, p.adres, p.aktif_mi,
                d.departman_id, d.departman_adi,
                poz.pozisyon_id, poz.pozisyon_adi,
                poz.taban_maas
            FROM Personel p
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.personel_id = %s
        """, (personel_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Personel bulunamadı'}), 404

        personel = {
            'personel_id': row['personel_id'],
            'tc_kimlik_no': row['tc_kimlik_no'],
            'ad': row['ad'],
            'soyad': row['soyad'],
            'telefon': row['telefon'],
            'email': row['email'],
            'ise_giris_tarihi': row['ise_giris_tarihi'],
            'dogum_tarihi': row['dogum_tarihi'],
            'adres': row['adres'],
            'aktif_mi': bool(row['aktif_mi']),
            'departman_id': row['departman_id'],
            'departman_adi': row['departman_adi'],
            'pozisyon_id': row['pozisyon_id'],
            'pozisyon_adi': row['pozisyon_adi'],
            'taban_maas': row['taban_maas']
        }

        cursor.execute("""
            SELECT pp.baslangic_tarihi, pp.bitis_tarihi, poz.pozisyon_adi
            FROM Personel_Pozisyon pp
            JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE pp.personel_id = %s
            ORDER BY pp.baslangic_tarihi DESC
        """, (personel_id,))
        pozisyon_gecmisi = [{
            'baslangic_tarihi': row['baslangic_tarihi'],
            'bitis_tarihi': row['bitis_tarihi'],
            'pozisyon_adi': row['pozisyon_adi']
        } for row in cursor.fetchall()]

        cursor.execute("""
            SELECT ik.baslangic_tarihi, ik.bitis_tarihi, ik.gun_sayisi, 
                   ik.onay_durumu, it.izin_adi
            FROM Izin_Kayit ik
            JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
            WHERE ik.personel_id = %s
            ORDER BY ik.baslangic_tarihi DESC
            LIMIT 10
        """, (personel_id,))
        izinler = [{
            'baslangic_tarihi': row['baslangic_tarihi'],
            'bitis_tarihi': row['bitis_tarihi'],
            'gun_sayisi': row['gun_sayisi'],
            'onay_durumu': row['onay_durumu'],
            'izin_adi': row['izin_adi']
        } for row in cursor.fetchall()]

        return jsonify({
            'personel': personel,
            'pozisyon_gecmisi': pozisyon_gecmisi,
            'izinler': izinler
        })
    except Exception as e:
        print(f"Detay Hatası: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees", methods=["POST"])
@admin_required
def employee_add():
    data = request.get_json()
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT personel_id FROM Personel WHERE tc_kimlik_no = %s", (data.get('tc_kimlik_no'),))
        if cursor.fetchone():
            return jsonify({'error': 'Bu TC kimlik numarası zaten kayıtlı'}), 400
        kullanici_adi = data.get('kullanici_adi')
        sifre = data.get('sifre')
        rol = data.get('rol') or 'employee'
        if not kullanici_adi or not sifre:
            return jsonify({'error': 'Kullanıcı adı ve şifre zorunludur'}), 400
        cursor.execute("SELECT kullanici_id FROM Kullanici WHERE kullanici_adi = %s", (kullanici_adi,))
        if cursor.fetchone():
            return jsonify({'error': 'Bu kullanıcı adı zaten alınmış'}), 400

        cursor.execute("""
            INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, adres, ise_giris_tarihi, departman_id, aktif_mi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (
            data.get('tc_kimlik_no'),
            data.get('ad'),
            data.get('soyad'),
            data.get('dogum_tarihi'),
            data.get('telefon'),
            data.get('email'),
            data.get('adres'),
            data.get('ise_giris_tarihi') or datetime.date.today().strftime('%Y-%m-%d'),
            data.get('departman_id')
        ))
        
        personel_id = cursor.lastrowid
        if data.get('pozisyon_id'):
            cursor.execute("""
                INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                VALUES (%s, %s, CURDATE(), 1)
            """, (personel_id, data.get('pozisyon_id')))

        password_hash = generate_password_hash(sifre)
        cursor.execute('''
            INSERT INTO Kullanici (kullanici_adi, sifre_hash, email, rol, personel_id, ilk_giris, aktif_mi)
            VALUES (%s, %s, %s, %s, %s, 1, 1)
        ''', (kullanici_adi, password_hash, data.get('email'), rol, personel_id))

        conn.commit()
        return jsonify({'message': 'Personel ve kullanıcı hesabı başarıyla eklendi', 'id': personel_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/<int:personel_id>", methods=["PUT"])
@admin_required
def employee_edit(personel_id):
    data = request.get_json()
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        allowed_fields = ['ad', 'soyad', 'tc_kimlik_no', 'telefon', 'email', 'adres', 'dogum_tarihi', 'departman_id']
        sql_parts = []
        params = []
        for field in allowed_fields:
            if field in data:
                sql_parts.append(f"{field} = %s")
                params.append(data.get(field))

        if sql_parts:
            params.append(personel_id)
            sql = f"UPDATE Personel SET {', '.join(sql_parts)} WHERE personel_id = %s"
            cursor.execute(sql, params)

        if data.get('pozisyon_id'):
            cursor.execute("""
                UPDATE Personel_Pozisyon SET guncel_mi = 0, bitis_tarihi = CURDATE() 
                WHERE personel_id = %s AND guncel_mi = 1
            """, (personel_id,))
            cursor.execute("""
                INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                VALUES (%s, %s, CURDATE(), 1)
            """, (personel_id, data.get('pozisyon_id')))

        conn.commit()
        return jsonify({'message': 'Personel bilgileri güncellendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/me", methods=["PUT"])
@login_required
def employee_update_me():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

    personel_id = payload.get('personel_id')
    if not personel_id:
        return jsonify({'error': 'Personel bilgisi bulunamadı'}), 400

    data = request.get_json() or {}

    allowed_fields = ['ad', 'soyad', 'telefon', 'email', 'adres', 'dogum_tarihi']
    updates = {k: data.get(k) for k in allowed_fields if k in data}

    if not updates:
        return jsonify({'error': 'Güncellenecek alan bulunamadı'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql_parts = []
        params = []
        for k, v in updates.items():
            sql_parts.append(f"{k} = %s")
            params.append(v)

        params.append(personel_id)
        sql = f"UPDATE Personel SET {', '.join(sql_parts)} WHERE personel_id = %s"
        cursor.execute(sql, params)
        conn.commit()
        return jsonify({'message': 'Kişisel bilgiler güncellendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/<int:personel_id>", methods=["DELETE"])
@admin_required
def employee_delete(personel_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE Personel SET aktif_mi = 0 WHERE personel_id = %s", (personel_id,))
        cursor.execute("DELETE FROM Kullanici WHERE personel_id = %s", (personel_id,))
        conn.commit()
        return jsonify({'message': 'Personel başarıyla silindi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/bulk-delete", methods=["POST"])
@admin_required
def employee_bulk_delete():
    data = request.get_json()
    personel_ids = data.get('personel_ids', [])

    if not personel_ids:
        return jsonify({'error': 'Hiç personel seçilmedi'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for pid in personel_ids:
            cursor.execute("UPDATE Personel SET aktif_mi = 0 WHERE personel_id = %s", (pid,))
            cursor.execute("DELETE FROM Kullanici WHERE personel_id = %s", (pid,))
        
        conn.commit()
        return jsonify({'message': f'{len(personel_ids)} personel başarıyla silindi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/bulk-department", methods=["POST"])
@admin_required
def employee_bulk_department():
    data = request.get_json()
    personel_ids = data.get('personel_ids', [])
    departman_id = data.get('departman_id')

    if not personel_ids or not departman_id:
        return jsonify({'error': 'Gerekli bilgiler eksik'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for pid in personel_ids:
            cursor.execute("UPDATE Personel SET departman_id = %s WHERE personel_id = %s", (departman_id, pid))
        
        conn.commit()
        return jsonify({'message': f'{len(personel_ids)} personelin departmanı değiştirildi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@employee_bp.route("/employees/bulk-position", methods=["POST"])
@admin_required
def employee_bulk_position():
    data = request.get_json()
    personel_ids = data.get('personel_ids', [])
    pozisyon_id = data.get('pozisyon_id')

    if not personel_ids or not pozisyon_id:
        return jsonify({'error': 'Gerekli bilgiler eksik'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for pid in personel_ids:
            cursor.execute("UPDATE Personel_Pozisyon SET guncel_mi = 0 WHERE personel_id = %s AND guncel_mi = 1", (pid,))
            cursor.execute("""
                INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                VALUES (%s, %s, CURDATE(), 1)
            """, (pid, pozisyon_id))
        
        conn.commit()
        return jsonify({'message': f'{len(personel_ids)} personelin pozisyonu değiştirildi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
