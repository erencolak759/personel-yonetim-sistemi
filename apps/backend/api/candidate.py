from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required

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


