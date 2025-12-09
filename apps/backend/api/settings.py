from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import admin_required, login_required

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route("/departments", methods=["GET"])
@login_required
def departments_list():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                d.departman_id as id,
                d.departman_adi as ad,
                COUNT(p.personel_id) as personel_sayisi
            FROM Departman d
            LEFT JOIN Personel p ON d.departman_id = p.departman_id AND p.aktif_mi = 1
            GROUP BY d.departman_id, d.departman_adi
            ORDER BY d.departman_adi
        """)
        rows = cursor.fetchall()
        
        departmanlar = [{
            'id': row['id'],
            'ad': row['ad'],
            'personel_sayisi': row['personel_sayisi']
        } for row in rows]
        
        return jsonify(departmanlar)
    except Exception as e:
        print(f"Departman listesi hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@settings_bp.route("/departments", methods=["POST"])
@admin_required
def department_add():
    data = request.get_json()
    departman_adi = data.get('ad', '').strip()

    if not departman_adi:
        return jsonify({'error': 'Departman adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO Departman (departman_adi) VALUES (%s)", (departman_adi,))
        conn.commit()
        return jsonify({'message': 'Departman eklendi', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/departments/<int:dept_id>", methods=["PUT"])
@admin_required
def department_edit(dept_id):
    data = request.get_json()
    departman_adi = data.get('ad', '').strip()

    if not departman_adi:
        return jsonify({'error': 'Departman adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE Departman SET departman_adi = %s WHERE departman_id = %s", (departman_adi, dept_id))
        conn.commit()
        return jsonify({'message': 'Departman güncellendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
@admin_required
def department_delete(dept_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) as sayi FROM Personel WHERE departman_id = %s AND aktif_mi = 1", (dept_id,))
        result = cursor.fetchone()

        if result and result['sayi'] > 0:
            return jsonify({'error': 'Bu departmanda personel bulunuyor! Önce personelleri başka departmana taşıyın.'}), 400

        cursor.execute("DELETE FROM Departman WHERE departman_id = %s", (dept_id,))
        conn.commit()
        return jsonify({'message': 'Departman silindi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@settings_bp.route("/positions", methods=["GET"])
@login_required
def positions_list():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                p.pozisyon_id as id,
                p.pozisyon_adi as ad,
                p.taban_maas as min_maas,
                p.taban_maas as max_maas,
                d.departman_id,
                d.departman_adi
            FROM Pozisyon p
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            ORDER BY p.pozisyon_adi
        """)
        rows = cursor.fetchall()
        
        pozisyonlar = [{
            'id': row['id'],
            'ad': row['ad'],
            'min_maas': row['min_maas'],
            'max_maas': row['max_maas'],
            'departman_id': row['departman_id']
        } for row in rows]
        
        return jsonify(pozisyonlar)
    except Exception as e:
        print(f"Pozisyon listesi hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@settings_bp.route("/positions", methods=["POST"])
@admin_required
def position_add():
    data = request.get_json()
    
    pozisyon_adi = data.get('ad', '').strip()
    departman_id = data.get('departman_id')
    taban_maas = data.get('min_maas') or data.get('max_maas') or 0

    if not pozisyon_adi:
        return jsonify({'error': 'Pozisyon adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Pozisyon (pozisyon_adi, departman_id, taban_maas) 
            VALUES (%s, %s, %s)
        """, (pozisyon_adi, departman_id or None, taban_maas))
        conn.commit()
        return jsonify({'message': 'Pozisyon eklendi', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/positions/<int:pos_id>", methods=["PUT"])
@admin_required
def position_edit(pos_id):
    data = request.get_json()
    
    pozisyon_adi = data.get('ad', '').strip()
    departman_id = data.get('departman_id')
    taban_maas = data.get('min_maas') or data.get('max_maas') or 0

    if not pozisyon_adi:
        return jsonify({'error': 'Pozisyon adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE Pozisyon SET pozisyon_adi = %s, departman_id = %s, taban_maas = %s
            WHERE pozisyon_id = %s
        """, (pozisyon_adi, departman_id or None, taban_maas, pos_id))
        conn.commit()
        return jsonify({'message': 'Pozisyon güncellendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/positions/<int:pos_id>", methods=["DELETE"])
@admin_required
def position_delete(pos_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) as sayi FROM Personel_Pozisyon 
            WHERE pozisyon_id = %s AND guncel_mi = 1
        """, (pos_id,))
        result = cursor.fetchone()

        if result and result['sayi'] > 0:
            return jsonify({'error': 'Bu pozisyonda personel bulunuyor!'}), 400

        cursor.execute("DELETE FROM Pozisyon WHERE pozisyon_id = %s", (pos_id,))
        conn.commit()
        return jsonify({'message': 'Pozisyon silindi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/leave-types", methods=["GET"])
@login_required
def leave_types_list():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                izin_turu_id as id,
                izin_adi as ad,
                yillik_hak_gun as max_gun,
                ucretli_mi
            FROM Izin_Turu
            ORDER BY izin_adi
        """)
        rows = cursor.fetchall()
        
        izin_turleri = [{
            'id': row['id'],
            'ad': row['ad'],
            'max_gun': row['max_gun'],
            'aciklama': 'Ücretli' if row['ucretli_mi'] else 'Ücretsiz'
        } for row in rows]
        
        return jsonify(izin_turleri)
    except Exception as e:
        print(f"İzin türleri listesi hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@settings_bp.route("/leave-types", methods=["POST"])
@admin_required
def leave_type_add():
    data = request.get_json()
    
    izin_adi = data.get('ad', '').strip()
    max_gun = data.get('max_gun') or 0
    ucretli_mi = 1 if data.get('aciklama', '').lower() == 'ücretli' else 0

    if not izin_adi:
        return jsonify({'error': 'İzin türü adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Izin_Turu (izin_adi, yillik_hak_gun, ucretli_mi) 
            VALUES (%s, %s, %s)
        """, (izin_adi, max_gun, ucretli_mi))
        conn.commit()
        return jsonify({'message': 'İzin türü eklendi', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/leave-types/<int:type_id>", methods=["PUT"])
@admin_required
def leave_type_edit(type_id):
    data = request.get_json()
    
    izin_adi = data.get('ad', '').strip()
    max_gun = data.get('max_gun') or 0
    ucretli_mi = 1 if data.get('aciklama', '').lower() == 'ücretli' else 0

    if not izin_adi:
        return jsonify({'error': 'İzin türü adı gereklidir'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE Izin_Turu SET izin_adi = %s, yillik_hak_gun = %s, ucretli_mi = %s
            WHERE izin_turu_id = %s
        """, (izin_adi, max_gun, ucretli_mi, type_id))
        conn.commit()
        return jsonify({'message': 'İzin türü güncellendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@settings_bp.route("/leave-types/<int:type_id>", methods=["DELETE"])
@admin_required
def leave_type_delete(type_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) as sayi FROM Izin_Kayit WHERE izin_turu_id = %s", (type_id,))
        result = cursor.fetchone()

        if result and result['sayi'] > 0:
            return jsonify({'error': 'Bu izin türü kullanılıyor, silinemez!'}), 400

        cursor.execute("DELETE FROM Izin_Turu WHERE izin_turu_id = %s", (type_id,))
        conn.commit()
        return jsonify({'message': 'İzin türü silindi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
