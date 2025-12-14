from flask import Blueprint, jsonify, request, send_file
from utils.db import get_connection
from api.auth import login_required, admin_required
from utils.pdf_generator import PDFGenerator
from io import BytesIO
import datetime

salary_bp = Blueprint('salary', __name__, url_prefix='/api')


def hesapla_maas(brut_maas, eklemeler=None, kesintiler=None):
    """
    Maaş hesaplama motoru
    brut_maas: Brüt maaş tutarı
    eklemeler: {'Prim': 1000, 'Yemek': 500} formatında dict
    kesintiler: Otomatik hesaplanır veya özel kesintiler eklenebilir
    """
    if eklemeler is None:
        eklemeler = {}

    # Brüt maaş + eklemeler
    toplam_brut = brut_maas
    toplam_ekleme = sum(eklemeler.values())

    # Kesintiler hesaplaması
    sgk_isci = brut_maas * 0.14
    sgk_isveren = brut_maas * 0.205
    issizlik_isci = brut_maas * 0.01
    issizlik_isveren = brut_maas * 0.02

    # Gelir vergisi matrah
    gelir_vergisi_matrahi = brut_maas - sgk_isci - issizlik_isci

    # Gelir vergisi (basitleştirilmiş - dilimli hesaplama)
    if gelir_vergisi_matrahi <= 70000:
        gelir_vergisi = gelir_vergisi_matrahi * 0.15
    elif gelir_vergisi_matrahi <= 150000:
        gelir_vergisi = 70000 * 0.15 + (gelir_vergisi_matrahi - 70000) * 0.20
    elif gelir_vergisi_matrahi <= 550000:
        gelir_vergisi = 70000 * 0.15 + 80000 * 0.20 + (gelir_vergisi_matrahi - 150000) * 0.27
    elif gelir_vergisi_matrahi <= 1900000:
        gelir_vergisi = 70000 * 0.15 + 80000 * 0.20 + 400000 * 0.27 + (gelir_vergisi_matrahi - 550000) * 0.35
    else:
        gelir_vergisi = 70000 * 0.15 + 80000 * 0.20 + 400000 * 0.27 + 1350000 * 0.35 + (
                    gelir_vergisi_matrahi - 1900000) * 0.40

    # Damga vergisi
    damga_vergisi = brut_maas * 0.00759

    # Toplam kesintiler
    toplam_kesinti = sgk_isci + issizlik_isci + gelir_vergisi + damga_vergisi

    # Net maaş
    net_maas = brut_maas + toplam_ekleme - toplam_kesinti

    return {
        'brut_maas': round(brut_maas, 2),
        'toplam_ekleme': round(toplam_ekleme, 2),
        'toplam_kesinti': round(toplam_kesinti, 2),
        'net_maas': round(net_maas, 2),
        'detaylar': {
            'sgk_isci': round(sgk_isci, 2),
            'sgk_isveren': round(sgk_isveren, 2),
            'issizlik_isci': round(issizlik_isci, 2),
            'issizlik_isveren': round(issizlik_isveren, 2),
            'gelir_vergisi': round(gelir_vergisi, 2),
            'damga_vergisi': round(damga_vergisi, 2)
        }
    }


@salary_bp.route("/salary/calculate", methods=["POST"])
@login_required
def calculate_salary():
    """Maaş hesaplama preview endpoint'i"""
    data = request.get_json()

    brut_maas = float(data.get('brut_maas', 0))
    eklemeler = data.get('eklemeler', {})

    hesaplama = hesapla_maas(brut_maas, eklemeler)

    return jsonify(hesaplama)


@salary_bp.route("/salary/components", methods=["GET"])
@login_required
def get_salary_components():
    """Maaş bileşenlerini getirir"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT bilesen_id, bilesen_adi, bilesen_tipi, sabit_mi, varsayilan_tutar
            FROM Maas_Bileseni
            ORDER BY bilesen_tipi, bilesen_adi
        """)

        components = [{
            'bilesen_id': row['bilesen_id'],
            'bilesen_adi': row['bilesen_adi'],
            'bilesen_tipi': row['bilesen_tipi'],
            'sabit_mi': bool(row['sabit_mi']),
            'varsayilan_tutar': row['varsayilan_tutar']
        } for row in cursor.fetchall()]

        return jsonify(components)
    finally:
        conn.close()


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
            sql += " AND mh.donem_yil = %s"
            params.append(yil)

        if ay:
            sql += " AND mh.donem_ay = %s"
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
            SELECT mh.*, p.ad, p.soyad, p.tc_kimlik_no, d.departman_adi,
                   pos.pozisyon_adi
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon pos ON pp.pozisyon_id = pos.pozisyon_id
            WHERE mh.maas_hesap_id = %s
        """, (maas_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Maaş kaydı bulunamadı'}), 404

        cursor.execute("""
            SELECT md.*, mb.bilesen_adi, mb.bilesen_tipi
            FROM Maas_Detay md
            JOIN Maas_Bileseni mb ON md.bilesen_id = mb.bilesen_id
            WHERE md.maas_hesap_id = %s
        """, (maas_id,))
        detaylar = [{
            'bilesen_adi': d['bilesen_adi'],
            'tip': d['bilesen_tipi'],
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
                'odeme_tarihi': str(row['odeme_tarihi']) if row['odeme_tarihi'] else None,
                'odendi_mi': bool(row['odendi_mi']),
                'ad': row['ad'],
                'soyad': row['soyad'],
                'departman_adi': row['departman_adi']
            },
            'personel': {
                'ad': row['ad'],
                'soyad': row['soyad'],
                'tc_kimlik_no': row.get('tc_kimlik_no'),
                'departman_adi': row.get('departman_adi'),
                'pozisyon_adi': row.get('pozisyon_adi')
            },
            'detaylar': detaylar
        })
    finally:
        conn.close()


@salary_bp.route("/salary", methods=["POST"])
@admin_required
def salary_create():
    """Yeni maaş kaydı oluşturur"""
    data = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Maaş hesaplama
        brut_maas = float(data.get('brut_maas'))
        eklemeler = data.get('eklemeler', {})
        hesaplama = hesapla_maas(brut_maas, eklemeler)

        # Ana maaş kaydını oluştur
        cursor.execute("""
            INSERT INTO Maas_Hesap (personel_id, donem_yil, donem_ay, brut_maas, 
                                     toplam_ekleme, toplam_kesinti, net_maas, odendi_mi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """, (
            data.get('personel_id'),
            data.get('donem_yil'),
            data.get('donem_ay'),
            hesaplama['brut_maas'],
            hesaplama['toplam_ekleme'],
            hesaplama['toplam_kesinti'],
            hesaplama['net_maas']
        ))

        maas_hesap_id = cursor.lastrowid

        # Detayları kaydet
        # Önce otomatik kesintileri ekle
        cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = 'SGK Isci Payi'")
        sgk_isci_id = cursor.fetchone()['bilesen_id']
        cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)",
                       (maas_hesap_id, sgk_isci_id, hesaplama['detaylar']['sgk_isci']))

        cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = 'Gelir Vergisi'")
        gelir_vergisi_id = cursor.fetchone()['bilesen_id']
        cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)",
                       (maas_hesap_id, gelir_vergisi_id, hesaplama['detaylar']['gelir_vergisi']))

        cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = 'Damga Vergisi'")
        damga_vergisi_id = cursor.fetchone()['bilesen_id']
        cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)",
                       (maas_hesap_id, damga_vergisi_id, hesaplama['detaylar']['damga_vergisi']))

        cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = 'Issizlik Sigortasi Isci'")
        issizlik_id = cursor.fetchone()['bilesen_id']
        cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)",
                       (maas_hesap_id, issizlik_id, hesaplama['detaylar']['issizlik_isci']))

        # Ekstra eklemeleri kaydet
        for bilesen_adi, tutar in eklemeler.items():
            if tutar > 0:
                cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = %s", (bilesen_adi,))
                bilesen = cursor.fetchone()
                if bilesen:
                    cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)",
                                   (maas_hesap_id, bilesen['bilesen_id'], tutar))

        conn.commit()
        return jsonify({'message': 'Maaş kaydı oluşturuldu', 'id': maas_hesap_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Maaş oluşturma hatası: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@salary_bp.route("/salary/<int:maas_id>/pay", methods=["POST"])
@admin_required
def salary_pay(maas_id):
    """Maaşı ödendi olarak işaretle"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE Maas_Hesap SET odendi_mi = 1, odeme_tarihi = CURRENT_DATE
            WHERE maas_hesap_id = %s
        """, (maas_id,))
        conn.commit()
        return jsonify({'message': 'Maaş ödendi olarak işaretlendi'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@salary_bp.route("/salary/pdf", methods=["GET"])
@login_required
def salary_pdf_all():
    """Tüm bordroların toplu PDF'i"""
    yil = request.args.get('yil')
    ay = request.args.get('ay')

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT mh.*, p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE 1=1
        """
        params = []

        if yil:
            sql += " AND mh.donem_yil = %s"
            params.append(yil)
        if ay:
            sql += " AND mh.donem_ay = %s"
            params.append(ay)

        sql += " ORDER BY p.ad"

        cursor.execute(sql, params)
        bordrolar = [dict(row) for row in cursor.fetchall()]

        if not bordrolar:
            return jsonify({'error': 'Bordro bulunamadı'}), 404

        # PDF oluştur
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.toplu_maas_bordrosu_pdf(bordrolar)

        donem_text = f"{ay}_{yil}" if ay and yil else "tum"
        filename = f"bordro_toplu_{donem_text}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"PDF oluşturma hatası: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@salary_bp.route("/salary/<int:maas_id>/pdf", methods=["GET"])
@login_required
def salary_pdf_single(maas_id):
    """Tek bordro PDF'i"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Maaş bilgisini getir
        cursor.execute("""
            SELECT mh.*, p.ad, p.soyad, p.tc_kimlik_no, d.departman_adi,
                   pos.pozisyon_adi
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon pos ON pp.pozisyon_id = pos.pozisyon_id
            WHERE mh.maas_hesap_id = %s
        """, (maas_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Bordro bulunamadı'}), 404

        # Detayları getir
        cursor.execute("""
            SELECT md.*, mb.bilesen_adi, mb.bilesen_tipi
            FROM Maas_Detay md
            JOIN Maas_Bileseni mb ON md.bilesen_id = mb.bilesen_id
            WHERE md.maas_hesap_id = %s
        """, (maas_id,))
        detaylar = [{
            'bilesen_adi': d['bilesen_adi'],
            'tip': d['bilesen_tipi'],
            'tutar': d['tutar']
        } for d in cursor.fetchall()]

        bordro_data = {
            'personel': {
                'ad': row['ad'],
                'soyad': row['soyad'],
                'tc_kimlik_no': row.get('tc_kimlik_no'),
                'departman_adi': row.get('departman_adi'),
                'pozisyon_adi': row.get('pozisyon_adi')
            },
            'maas': {
                'donem_yil': row['donem_yil'],
                'donem_ay': row['donem_ay'],
                'brut_maas': row['brut_maas'],
                'toplam_ekleme': row['toplam_ekleme'],
                'toplam_kesinti': row['toplam_kesinti'],
                'net_maas': row['net_maas'],
                'odendi_mi': bool(row['odendi_mi']),
                'odeme_tarihi': str(row['odeme_tarihi']) if row['odeme_tarihi'] else None
            },
            'detaylar': detaylar
        }

        # PDF oluştur
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.maas_bordrosu_pdf(bordro_data)

        filename = f"bordro_{row['ad']}_{row['soyad']}_{row['donem_ay']}_{row['donem_yil']}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"PDF oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()