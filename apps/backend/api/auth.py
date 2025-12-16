from flask import Blueprint, jsonify, session, request
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from utils.db import get_connection
from datetime import datetime, timedelta
import jwt
from flask import current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

        token = auth_header.split(' ')[1]
        user_data = decode_token(token)

        if not user_data:
            return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

        token = auth_header.split(' ')[1]
        user_data = decode_token(token)

        if not user_data:
            return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

        if user_data.get('role') != 'admin':
            return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route("/auth/me", methods=["GET"])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'authenticated': False}), 200

    token = auth_header.split(' ')[1]
    user_data = decode_token(token)

    if not user_data:
        return jsonify({'authenticated': False}), 200
    user = {
        'kullanici_id': user_data.get('user_id'),
        'kullanici_adi': user_data.get('username'),
        'email': user_data.get('email'),
        'rol': user_data.get('role'),
        'personel_id': user_data.get('personel_id'),
        'ilk_giris': user_data.get('ilk_giris')
    }

    return jsonify({
        'authenticated': True,
        'user': user
    })


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gereklidir'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT kullanici_id, kullanici_adi, sifre_hash, rol, personel_id, ilk_giris, aktif_mi, email
            FROM Kullanici WHERE kullanici_adi = %s
        """, (username,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre'}), 401
        
        user = dict(row)
        
        if not user['aktif_mi']:
            return jsonify({'error': 'Bu hesap devre dışı bırakılmış'}), 401
        
        if not check_password_hash(user['sifre_hash'], password):
            return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre'}), 401
        
        cursor.execute("UPDATE Kullanici SET son_giris = %s WHERE kullanici_id = %s",
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['kullanici_id']))
        conn.commit()
        
        token = jwt.encode({
            'user_id': user['kullanici_id'],
            'username': user['kullanici_adi'],
            'role': user['rol'],
            'personel_id': user['personel_id'],
            'ilk_giris': user['ilk_giris'],
            'exp': datetime.utcnow() + timedelta(hours=2) 
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Giriş başarılı',
            'token': token,
            'user': {
                'kullanici_id': user['kullanici_id'],
                'kullanici_adi': user['kullanici_adi'],
                'email': user['email'],
                'rol': user['rol'],
                'personel_id': user['personel_id'],
                'ilk_giris': user['ilk_giris']
            }
        })
        
    finally:
        conn.close()


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    return jsonify({'message': 'Çıkış yapıldı'})


@auth_bp.route("/auth/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Mevcut ve yeni şifre gereklidir'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Yeni şifre en az 6 karakter olmalıdır'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()

    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

        user_id = payload.get('user_id')

        cursor.execute("SELECT sifre_hash FROM Kullanici WHERE kullanici_id = %s", (user_id,))
        row = cursor.fetchone()

        if not row or not check_password_hash(row['sifre_hash'], current_password):
            return jsonify({'error': 'Mevcut şifre yanlış'}), 401

        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE Kullanici SET sifre_hash = %s, ilk_giris = 0 WHERE kullanici_id = %s",
                      (new_hash, user_id))
        conn.commit()
        cursor.execute("SELECT kullanici_id, kullanici_adi, rol, personel_id, email, ilk_giris FROM Kullanici WHERE kullanici_id = %s", (user_id,))
        updated = cursor.fetchone()
        if updated:
            u = dict(updated)
            new_token = jwt.encode({
                'user_id': u['kullanici_id'],
                'username': u['kullanici_adi'],
                'role': u['rol'],
                'personel_id': u['personel_id'],
                'ilk_giris': u['ilk_giris'],
                'exp': datetime.utcnow() + timedelta(hours=2)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'message': 'Şifre başarıyla değiştirildi',
                'token': new_token,
                'user': {
                    'kullanici_id': u['kullanici_id'],
                    'kullanici_adi': u['kullanici_adi'],
                    'email': u['email'],
                    'rol': u['rol'],
                    'personel_id': u['personel_id'],
                    'ilk_giris': u['ilk_giris']
                }
            })

        return jsonify({'message': 'Şifre başarıyla değiştirildi'})
    finally:
        conn.close()


@auth_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    """
    Tüm personelleri ve varsa ilişkili kullanıcı hesaplarını döner.
    Kullanici kaydı olmayan personeller de listelenir (kullanici_id NULL).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    only_personnel = request.args.get('only_personnel', '0')
    try:
        sql = """
            SELECT 
                p.personel_id,
                p.ad,
                p.soyad,
                p.email AS personel_email,
                p.telefon AS personel_telefon,
                d.departman_adi,
                k.kullanici_id,
                k.kullanici_adi,
                k.email,
                k.rol,
                k.aktif_mi,
                k.son_giris
            FROM Personel p
            LEFT JOIN Kullanici k ON k.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
        """
        params = []
        # only_personnel param'ı korunuyor; kullanıcı dışı kayıtları hariç tutmak istersen ileride kullanılır.
        if str(only_personnel) in ['1', 'true', 'True']:
            sql += " WHERE p.personel_id IS NOT NULL"
        sql += " ORDER BY p.personel_id DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        users = [{
            'personel_id': row['personel_id'],
            'ad': row['ad'],
            'soyad': row['soyad'],
            'personel_email': row.get('personel_email'),
            'personel_telefon': row.get('personel_telefon'),
            'departman_adi': row.get('departman_adi'),
            'kullanici_id': row.get('kullanici_id'),
            'kullanici_adi': row.get('kullanici_adi'),
            'email': row.get('email'),
            'rol': row.get('rol'),
            'aktif_mi': row.get('aktif_mi'),
            'son_giris': row.get('son_giris'),
        } for row in rows]
        
        return jsonify(users)
    finally:
        conn.close()


@auth_bp.route("/users", methods=["POST"])
@admin_required
def create_user():
    data = request.get_json()
    
    kullanici_adi = data.get('kullanici_adi', '').strip()
    email = data.get('email', '').strip()
    sifre = data.get('sifre', '')
    rol = data.get('rol', 'employee')
    personel_id = data.get('personel_id')
    
    if not kullanici_adi or not sifre:
        return jsonify({'error': 'Kullanıcı adı ve şifre gereklidir'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT kullanici_id FROM Kullanici WHERE kullanici_adi = %s", (kullanici_adi,))
        if cursor.fetchone():
            return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
        
        sifre_hash = generate_password_hash(sifre)
        
        cursor.execute("""
            INSERT INTO Kullanici (kullanici_adi, email, sifre_hash, rol, personel_id, aktif_mi, ilk_giris)
            VALUES (%s, %s, %s, %s, %s, 1, 1)
        """, (kullanici_adi, email or None, sifre_hash, rol, personel_id))
        conn.commit()
        
        return jsonify({'message': 'Kullanıcı başarıyla oluşturuldu', 'id': cursor.lastrowid}), 201
    finally:
        conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.get_json()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'] or None)
        
        if 'rol' in data:
            updates.append("rol = %s")
            params.append(data['rol'])
        
        if 'aktif_mi' in data:
            updates.append("aktif_mi = %s")
            params.append(1 if data['aktif_mi'] else 0)
        
        plain_password = None
        if 'sifre' in data and data['sifre']:
            plain_password = data['sifre']
            updates.append("sifre_hash = %s")
            params.append(generate_password_hash(plain_password))
        
        if not updates:
            return jsonify({'error': 'Güncellenecek alan bulunamadı'}), 400
        
        params.append(user_id)
        sql = f"UPDATE Kullanici SET {', '.join(updates)} WHERE kullanici_id = %s"
        cursor.execute(sql, params)
        conn.commit()
        
        resp = {'message': 'Kullanıcı güncellendi'}
        if plain_password:
            resp['password'] = plain_password
        return jsonify(resp)
    finally:
        conn.close()


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Geçersiz veya süresi dolmuş token'}), 401

    current_user_id = payload.get('user_id')
    if user_id == current_user_id:
        return jsonify({'error': 'Kendi hesabınızı silemezsiniz'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE Kullanici SET aktif_mi = 0 WHERE kullanici_id = %s", (user_id,))
        conn.commit()
        return jsonify({'message': 'Kullanıcı devre dışı bırakıldı'})
    finally:
        conn.close()
