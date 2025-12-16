from flask import Blueprint, jsonify, request
from utils.db import get_connection
from api.auth import login_required, admin_required
import datetime

announcement_bp = Blueprint('announcement', __name__, url_prefix='/api')


@announcement_bp.route("/announcements", methods=["GET"])
@login_required
def list_announcements():
    """Aktif duyuruları listele."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT d.duyuru_id,
                   d.baslik,
                   d.icerik,
                   d.yayin_tarihi,
                   d.bitis_tarihi,
                   d.oncelik,
                   d.aktif_mi,
                   k.kullanici_adi AS olusturan
            FROM Duyuru d
            JOIN Kullanici k ON d.olusturan_kullanici_id = k.kullanici_id
            WHERE d.aktif_mi = 1
            ORDER BY d.yayin_tarihi DESC
            """
        )
        rows = cursor.fetchall()
        duyurular = [
            {
                "duyuru_id": row["duyuru_id"],
                "baslik": row["baslik"],
                "icerik": row["icerik"],
                "yayin_tarihi": row["yayin_tarihi"].strftime("%Y-%m-%d %H:%M")
                if row["yayin_tarihi"]
                else None,
                "bitis_tarihi": row["bitis_tarihi"].strftime("%Y-%m-%d %H:%M")
                if row["bitis_tarihi"]
                else None,
                "oncelik": row["oncelik"],
                "aktif_mi": bool(row["aktif_mi"]),
                "olusturan": row["olusturan"],
            }
            for row in rows
        ]
        return jsonify(duyurular)
    finally:
        conn.close()


@announcement_bp.route("/announcements", methods=["POST"])
@admin_required
def create_announcement():
    """Yeni duyuru oluştur."""
    data = request.get_json() or {}

    baslik = data.get("baslik")
    icerik = data.get("icerik")
    oncelik = data.get("oncelik", "Normal")
    bitis_tarihi = data.get("bitis_tarihi")
    olusturan_kullanici_id = data.get("olusturan_kullanici_id")

    if not baslik or not icerik or not olusturan_kullanici_id:
        return jsonify({"error": "Başlık, içerik ve oluşturan kullanıcı zorunludur"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO Duyuru (baslik, icerik, olusturan_kullanici_id, bitis_tarihi, oncelik)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (baslik, icerik, olusturan_kullanici_id, bitis_tarihi, oncelik),
        )
        conn.commit()
        return jsonify(
            {"message": "Duyuru oluşturuldu", "duyuru_id": cursor.lastrowid}
        ), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@announcement_bp.route("/announcements/<int:duyuru_id>", methods=["DELETE"])
@admin_required
def delete_announcement(duyuru_id: int):
    """Duyuruyu pasif hale getir (soft delete)."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE Duyuru SET aktif_mi = 0 WHERE duyuru_id = %s", (duyuru_id,)
        )
        conn.commit()
        return jsonify({"message": "Duyuru silindi"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


