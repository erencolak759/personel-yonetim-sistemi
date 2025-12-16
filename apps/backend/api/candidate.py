from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
from werkzeug.security import generate_password_hash
import datetime
import random
import string

candidate_bp = Blueprint('candidate', __name__, url_prefix='/api')


@candidate_bp.route("/candidates", methods=["GET"])
@login_required
def list_candidates():
    """Adayları listele."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT a.aday_id,
                   a.ad,
                   a.soyad,
                   a.telefon,
                   a.email,
                   a.pozisyon_id,
                   a.basvuru_tarihi,
                   a.gorusme_tarihi,
                   a.durum,
                   a.aciklama,
                   p.pozisyon_adi
            FROM Adaylar a
            JOIN Pozisyon p ON a.pozisyon_id = p.pozisyon_id
            ORDER BY a.basvuru_tarihi DESC, a.aday_id DESC
            """
        )
        rows = cursor.fetchall()
        adaylar = [
            {
                "aday_id": row["aday_id"],
                "ad": row["ad"],
                "soyad": row["soyad"],
                "telefon": row["telefon"],
                "email": row["email"],
                "pozisyon_id": row["pozisyon_id"],
                "pozisyon_adi": row["pozisyon_adi"],
                "basvuru_tarihi": row["basvuru_tarihi"].strftime("%Y-%m-%d")
                if row["basvuru_tarihi"]
                else None,
                "gorusme_tarihi": row["gorusme_tarihi"].strftime("%Y-%m-%d")
                if row["gorusme_tarihi"]
                else None,
                "durum": row["durum"],
                "aciklama": row["aciklama"],
            }
            for row in rows
        ]
        return jsonify(adaylar)
    finally:
        conn.close()


@candidate_bp.route("/candidates", methods=["POST"])
@admin_required
def create_candidate():
    """Yeni aday ekle."""
    data = request.get_json() or {}

    ad = data.get("ad")
    soyad = data.get("soyad")
    pozisyon_id = data.get("pozisyon_id")
    basvuru_tarihi = data.get("basvuru_tarihi")

    if not ad or not soyad or not pozisyon_id or not basvuru_tarihi:
        return jsonify({"error": "Ad, soyad, pozisyon ve başvuru tarihi zorunludur"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO Adaylar (ad, soyad, telefon, email, pozisyon_id, basvuru_tarihi, gorusme_tarihi, durum, aciklama)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ad,
                soyad,
                data.get("telefon"),
                data.get("email"),
                pozisyon_id,
                basvuru_tarihi,
                data.get("gorusme_tarihi"),
                data.get("durum", "Basvuru Alindi"),
                data.get("aciklama"),
            ),
        )
        conn.commit()
        return jsonify(
            {"message": "Aday kaydı oluşturuldu", "aday_id": cursor.lastrowid}
        ), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@candidate_bp.route("/candidates/positions", methods=["GET"])
def public_positions():
    """Aday başvuru formu için pozisyon listesini herkese açık verir."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT pozisyon_id, pozisyon_adi FROM Pozisyon ORDER BY pozisyon_adi")
        rows = cursor.fetchall()
        return jsonify(rows)
    finally:
        conn.close()


@candidate_bp.route("/candidates/apply", methods=["POST"])
def public_apply():
    """Login gerektirmeyen aday başvurusu."""
    data = request.get_json() or {}
    ad = data.get("ad")
    soyad = data.get("soyad")
    pozisyon_id = data.get("pozisyon_id")
    telefon = data.get("telefon")
    email = data.get("email")

    if not ad or not soyad or not pozisyon_id:
        return jsonify({"error": "Ad, soyad ve pozisyon zorunlu"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Adaylar (ad, soyad, telefon, email, pozisyon_id, basvuru_tarihi, durum)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ad,
                soyad,
                telefon,
                email,
                pozisyon_id,
                datetime.date.today().strftime("%Y-%m-%d"),
                "Basvuru Alindi",
            ),
        )
        conn.commit()
        return jsonify({"message": "Başvurunuz alındı", "aday_id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


def _generate_username(ad: str, soyad: str, suffix: str = ""):
    base = f"{ad}.{soyad}".lower().replace(" ", "")
    return f"{base}{suffix}" if suffix else base


def _generate_password(length: int = 10):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


@candidate_bp.route("/candidates/<int:aday_id>/approve", methods=["POST"])
@admin_required
def approve_candidate(aday_id: int):
    """Adayı onaylar, durumunu 'Kabul' yapar ve kullanıcı hesabı oluşturur.

    Ek olarak:
    - Adayın seçtiği pozisyonun bağlı olduğu departmanı otomatik bulur
    - Oluşturulan personel kaydında `departman_id` alanını bu değer ile doldurur
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT ad, soyad, email, telefon, pozisyon_id, durum
            FROM Adaylar
            WHERE aday_id = %s
            """,
            (aday_id,),
        )
        aday = cursor.fetchone()
        if not aday:
            return jsonify({"error": "Aday bulunamadı"}), 404
        if aday.get("durum") == "Kabul":
            return jsonify({"error": "Bu aday zaten onaylanmış"}), 400

        # Adayın pozisyonuna bağlı departmanı bul
        pozisyon_id = aday.get("pozisyon_id")
        departman_id = None
        if pozisyon_id:
            cursor.execute(
                "SELECT departman_id FROM Pozisyon WHERE pozisyon_id = %s",
                (pozisyon_id,),
            )
            pozisyon_row = cursor.fetchone()
            if pozisyon_row:
                departman_id = pozisyon_row.get("departman_id")

        # Durumu güncelle
        cursor.execute(
            "UPDATE Adaylar SET durum = %s WHERE aday_id = %s", ("Kabul", aday_id)
        )

        # Personel oluştur (basit varsayılan alanlar ile)
        tc_kimlik_no = "".join(random.choices(string.digits, k=11))
        dogum_tarihi = "1990-01-01"
        ise_giris_tarihi = datetime.date.today().strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT INTO Personel (tc_kimlik_no, ad, soyad, dogum_tarihi, telefon, email, adres, ise_giris_tarihi, departman_id, aktif_mi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (
                tc_kimlik_no,
                aday["ad"],
                aday["soyad"],
                dogum_tarihi,
                aday.get("telefon"),
                aday.get("email"),
                None,
                ise_giris_tarihi,
                departman_id,
            ),
        )
        personel_id = cursor.lastrowid

        # Pozisyon eşlemesi
        if pozisyon_id:
            cursor.execute(
                """
                INSERT INTO Personel_Pozisyon (personel_id, pozisyon_id, baslangic_tarihi, guncel_mi)
                VALUES (%s, %s, %s, 1)
                """,
                (personel_id, pozisyon_id, ise_giris_tarihi),
            )

        # Kullanıcı adı üret
        base_username = _generate_username(aday["ad"], aday["soyad"])
        username = base_username
        tries = 0
        while True:
            cursor.execute(
                "SELECT 1 FROM Kullanici WHERE kullanici_adi = %s LIMIT 1", (username,)
            )
            if not cursor.fetchone():
                break
            tries += 1
            username = _generate_username(aday["ad"], aday["soyad"], str(tries))

        password = _generate_password(12)
        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO Kullanici (kullanici_adi, sifre_hash, email, rol, personel_id, ilk_giris, aktif_mi)
            VALUES (%s, %s, %s, %s, %s, 1, 1)
            """,
            (username, password_hash, aday.get("email"), "employee", personel_id),
        )

        conn.commit()
        return jsonify(
            {
                "message": "Aday onaylandı ve kullanıcı oluşturuldu",
                "username": username,
                "password": password,
                "personel_id": personel_id,
            }
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@candidate_bp.route("/candidates/<int:aday_id>/reject", methods=["POST"])
@admin_required
def reject_candidate(aday_id: int):
    """Adayı reddeder."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Adaylar SET durum = %s WHERE aday_id = %s", ("Red", aday_id)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Aday bulunamadı"}), 404
        conn.commit()
        return jsonify({"message": "Aday reddedildi"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
