from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required

salary_bp = Blueprint('salary', __name__, url_prefix='/api')


@salary_bp.route("/salary", methods=["GET"])
@login_required
def salary_list():
    conn = get_connection()
    cursor = conn.cursor()
    
    yil = request.args.get('yil')
    ay = request.args.get('ay')
    
    try:
        sql = """
            SELECT mh.maas_hesap_id, mh.personel_id, mh.donem_yil, mh.donem_ay,
                   mh.brut_maas, mh.toplam_ekleme, mh.toplam_kesinti, mh.net_maas,
                   mh.odeme_tarihi, mh.odendi_mi,
                   p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE 1=1
        """
        params = []
        
        if yil:
            sql += " AND mh.donem_yil = ?"
            params.append(yil)
        
        if ay:
            sql += " AND mh.donem_ay = ?"
            params.append(ay)
        
        sql += " ORDER BY mh.donem_yil DESC, mh.donem_ay DESC, p.ad"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        maaslar = [{
            'maas_hesap_id': row['maas_hesap_id'],
            'personel_id': row['personel_id'],
            'donem_yil': row['donem_yil'],
            'donem_ay': row['donem_ay'],
            'brut_maas': row['brut_maas'],
            'toplam_ekleme': row['toplam_ekleme'],
            'toplam_kesinti': row['toplam_kesinti'],
            'net_maas': row['net_maas'],
            'odeme_tarihi': row['odeme_tarihi'],
            'odendi_mi': bool(row['odendi_mi']),
            'ad': row['ad'],
            'soyad': row['soyad'],
            'departman_adi': row['departman_adi']
        } for row in rows]
        
        return jsonify(maaslar)
    except Exception as e:
        print(f"Maaş listesi hatası: {e}")
        return jsonify([])
    finally:
        conn.close()


@salary_bp.route("/salary/<int:maas_id>", methods=["GET"])
@login_required
def salary_detail(maas_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT mh.*, p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE mh.maas_hesap_id = ?
        """, (maas_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Maaş kaydı bulunamadı'}), 404
        
        cursor.execute("""
            SELECT md.*, mb.bilesen_adi, mb.tip
            FROM Maas_Detay md
            JOIN Maas_Bileseni mb ON md.bilesen_id = mb.bilesen_id
            WHERE md.maas_hesap_id = ?
        """, (maas_id,))
        detaylar = [{
            'bilesen_adi': d['bilesen_adi'],
            'tip': d['tip'],
            'tutar': d['tutar']
        } for d in cursor.fetchall()]
        
        return jsonify({
            'maas': {
                'maas_hesap_id': row['maas_hesap_id'],
                'personel_id': row['personel_id'],
                'donem_yil': row['donem_yil'],
                'donem_ay': row['donem_ay'],
                'brut_maas': row['brut_maas'],
                'toplam_ekleme': row['toplam_ekleme'],
                'toplam_kesinti': row['toplam_kesinti'],
                'net_maas': row['net_maas'],
                'odeme_tarihi': row['odeme_tarihi'],
                'odendi_mi': bool(row['odendi_mi']),
                'ad': row['ad'],
                'soyad': row['soyad'],
                'departman_adi': row['departman_adi']
            },
            'detaylar': detaylar
        })
    finally:
        conn.close()


@salary_bp.route("/salary", methods=["POST"])
@admin_required
def salary_create():
    data = request.get_json()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Maas_Hesap (personel_id, donem_yil, donem_ay, brut_maas, toplam_ekleme, toplam_kesinti, net_maas, odendi_mi)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data.get('personel_id'),
            data.get('donem_yil'),
            data.get('donem_ay'),
            data.get('brut_maas'),
            data.get('toplam_ekleme', 0),
            data.get('toplam_kesinti', 0),
            data.get('net_maas')
        ))
        conn.commit()
        return jsonify({'message': 'Maaş kaydı oluşturuldu', 'id': cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@salary_bp.route("/salary/<int:maas_id>/pay", methods=["POST"])
@admin_required
def salary_pay(maas_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Maas_Hesap SET odendi_mi = 1, odeme_tarihi = date('now')
            WHERE maas_hesap_id = ?
        """, (maas_id,))
        conn.commit()
        return jsonify({'message': 'Maaş ödendi olarak işaretlendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
