from flask import Blueprint, jsonify, request, send_file
from utils.db import get_connection
from utils.pdf_generator import PDFGenerator
from api.auth import login_required, admin_required, decode_token
import datetime
import calendar
from decimal import Decimal, ROUND_HALF_UP

SGK_EMPLOYEE_RATE = Decimal('0.14')
SGK_EMPLOYER_RATE = Decimal('0.205') 
INCOME_TAX_BANDS = [
    (Decimal('32000'), Decimal('0.15')),
    (Decimal('70000'), Decimal('0.20')),
    (Decimal('250000'), Decimal('0.27')),
    (Decimal('880000'), Decimal('0.35')),
    (Decimal('9999999999'), Decimal('0.40')),
]


def _get_request_user():
    """Decode JWT from Authorization header and return payload."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    return decode_token(token)


def annual_income_tax(annual_taxable: Decimal) -> Decimal:
    tax = Decimal('0')
    remaining = Decimal(annual_taxable)
    lower = Decimal('0')
    for upper, rate in INCOME_TAX_BANDS:
        bracket = min(remaining, upper - lower)
        if bracket <= 0:
            lower = upper
            continue
        tax += bracket * rate
        remaining -= bracket
        lower = upper
        if remaining <= 0:
            break
    return tax

salary_bp = Blueprint('salary', __name__, url_prefix='/api')


@salary_bp.route("/salary", methods=["GET"])
@login_required
def salary_list():
    conn = get_connection()
    cursor = conn.cursor()
    
    yil = request.args.get('yil')
    ay = request.args.get('ay')
    
    archived = request.args.get('archived', '0')
    try:
        aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1
    except Exception:
        aktif_flag = 1

    user_data = _get_request_user() or {}
    user_role = user_data.get('role')
    current_personel_id = user_data.get('personel_id')
    requested_personel_id = request.args.get('personel_id')

    try:
        sql = """
            SELECT mh.maas_hesap_id, mh.personel_id, mh.donem_yil, mh.donem_ay,
                   mh.brut_maas, mh.toplam_ekleme, mh.toplam_kesinti, mh.net_maas,
                   mh.odeme_tarihi, mh.odendi_mi,
                   p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE p.aktif_mi = %s
        """
        params = [aktif_flag]

        if user_role != 'admin':
            # Çalışanlar sadece kendi bordrolarını görebilir
            if not current_personel_id:
                return jsonify({'error': 'Personel bilgisi bulunamadı'}), 400
            sql += " AND mh.personel_id = %s"
            params.append(current_personel_id)
        elif requested_personel_id:
            # Admin isterse belirli bir personeli filtreleyebilir
            sql += " AND mh.personel_id = %s"
            params.append(requested_personel_id)

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
            SELECT mh.*, p.ad, p.soyad, d.departman_adi 
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE mh.maas_hesap_id = %s
        """, (maas_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Maaş kaydı bulunamadı'}), 404
        
        cursor.execute("""
            SELECT md.*, mb.bilesen_adi, mb.tip
            FROM Maas_Detay md
            JOIN Maas_Bileseni mb ON md.bilesen_id = mb.bilesen_id
            WHERE md.maas_hesap_id = %s
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
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


@salary_bp.route("/salary/generate", methods=["POST"])
@admin_required
def salary_generate():
    data = request.get_json() or {}
    try:
        yil = int(data.get('yil'))
        ay = int(data.get('ay'))
    except Exception:
        return jsonify({'error': 'yil ve ay zorunludur'}), 400

    personel_filter = data.get('personel_id')
    month_start = datetime.date(yil, ay, 1)
    last_day = calendar.monthrange(yil, ay)[1]
    month_end = datetime.date(yil, ay, last_day)
    working_days = 0
    cur = month_start
    while cur <= month_end:
        if cur.weekday() < 5:
            working_days += 1
        cur += datetime.timedelta(days=1)

    if working_days == 0:
        return jsonify({'error': 'Geçersiz ay, çalışma günü bulunamadı'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT p.personel_id, poz.taban_maas
            FROM Personel p
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.aktif_mi = 1
        """
        params = []
        if personel_filter:
            sql += " AND p.personel_id = %s"
            params.append(personel_filter)

        cursor.execute(sql, params)
        employees = cursor.fetchall()

        def round2(x):
            return float(Decimal(x).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        def get_or_create_bilesen(name: str, tip: str = 'kesinti'):
            cursor.execute("SELECT bilesen_id FROM Maas_Bileseni WHERE bilesen_adi = %s", (name,))
            r = cursor.fetchone()
            if r:
                return r['bilesen_id']
            cursor.execute("INSERT INTO Maas_Bileseni (bilesen_adi, bilesen_tipi, sabit_mi, varsayilan_tutar) VALUES (%s, %s, %s, %s)", (name, tip, 0, 0))
            return cursor.lastrowid

        def annual_income_tax(annual_taxable: Decimal) -> Decimal:
            tax = Decimal('0')
            remaining = annual_taxable
            lower = Decimal('0')
            for upper, rate in INCOME_TAX_BANDS:
                bracket = min(remaining, upper - lower)
                if bracket <= 0:
                    lower = upper
                    continue
                tax += bracket * rate
                remaining -= bracket
                lower = upper
                if remaining <= 0:
                    break
            return tax

        created = []
        for row in employees:
            pid = row['personel_id']
            taban = Decimal(row.get('taban_maas') or 0)
            try:
                cursor.execute("SELECT maas_hesap_id FROM Maas_Hesap WHERE personel_id = %s AND donem_yil = %s AND donem_ay = %s", (pid, yil, ay))
                existing = [r['maas_hesap_id'] for r in cursor.fetchall()]
                if existing:
                    cursor.execute("DELETE FROM Maas_Detay WHERE maas_hesap_id IN (%s)" % (', '.join(['%s'] * len(existing))), tuple(existing))
                    cursor.execute("DELETE FROM Maas_Hesap WHERE maas_hesap_id IN (%s)" % (', '.join(['%s'] * len(existing))), tuple(existing))
            except Exception:
                pass
            cursor.execute("""
                SELECT ik.baslangic_tarihi as bas, ik.bitis_tarihi as bit, it.ucretli_mi as ucretli
                FROM Izin_Kayit ik
                JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
                WHERE ik.personel_id = %s AND ik.onay_durumu = 'Onaylandi'
                  AND NOT (ik.bitis_tarihi < %s OR ik.baslangic_tarihi > %s)
            """, (pid, month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))

            leaves = cursor.fetchall()
            unpaid_days = 0
            for l in leaves:
                try:
                    bas = l['bas'] if isinstance(l['bas'], datetime.date) else datetime.datetime.strptime(str(l['bas'])[:10], '%Y-%m-%d').date()
                    bit = l['bit'] if isinstance(l['bit'], datetime.date) else datetime.datetime.strptime(str(l['bit'])[:10], '%Y-%m-%d').date()
                except Exception:
                    continue

                overlap_start = max(bas, month_start)
                overlap_end = min(bit, month_end)
                if overlap_end < overlap_start:
                    continue
                d = overlap_start
                overlap_count = 0
                while d <= overlap_end:
                    if d.weekday() < 5:
                        overlap_count += 1
                    d += datetime.timedelta(days=1)
                if not l.get('ucretli'):
                    unpaid_days += overlap_count
            cursor.execute("SELECT SUM(ek_mesai_saat) as toplam_ek FROM Devam WHERE personel_id = %s AND tarih BETWEEN %s AND %s", (pid, month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
            ek_row = cursor.fetchone()
            overtime_hours = float(ek_row['toplam_ek'] or 0)
            OVERTIME_MULTIPLIER = Decimal('1.5')
            if working_days == 0:
                continue

            daily_rate = (taban / Decimal(working_days))
            unpaid_deduction = (daily_rate * Decimal(unpaid_days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            hourly_rate = (daily_rate / Decimal(8))
            overtime_pay = (hourly_rate * Decimal(overtime_hours) * OVERTIME_MULTIPLIER).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sgk_employee = (taban * SGK_EMPLOYEE_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            taxable_monthly = (taban - sgk_employee - unpaid_deduction)
            if taxable_monthly < 0:
                taxable_monthly = Decimal('0.00')

            annual_taxable = (taxable_monthly * Decimal(12))
            annual_income = annual_income_tax(annual_taxable)
            monthly_income_tax = (annual_income / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            toplam_kesinti = (unpaid_deduction + sgk_employee + monthly_income_tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            toplam_ekleme = Decimal('0.00')
            if overtime_pay > 0:
                toplam_ekleme += overtime_pay
            net_maas = (taban - toplam_kesinti + toplam_ekleme).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            cursor.execute("""
                INSERT INTO Maas_Hesap (personel_id, donem_yil, donem_ay, brut_maas, toplam_ekleme, toplam_kesinti, net_maas, odendi_mi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """, (pid, yil, ay, float(taban), float(toplam_ekleme), float(toplam_kesinti), float(net_maas)))
            mh_id = cursor.lastrowid
            b_sgk_calisan = get_or_create_bilesen('SGK Çalışan', 'kesinti')
            b_gelir_vergi = get_or_create_bilesen('Gelir Vergisi', 'kesinti')
            b_ucretsiz = get_or_create_bilesen('Ücretsiz İzin Kesintisi', 'kesinti')
            b_sgk_isveren = get_or_create_bilesen('SGK İşveren', 'ekleme')

            if float(sgk_employee) > 0:
                cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)", (mh_id, b_sgk_calisan, float(sgk_employee)))
            if float(monthly_income_tax) > 0:
                cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)", (mh_id, b_gelir_vergi, float(monthly_income_tax)))
            if float(unpaid_deduction) > 0:
                cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)", (mh_id, b_ucretsiz, float(unpaid_deduction)))
            if float(overtime_pay) > 0:
                b_ekmesai = get_or_create_bilesen('Ek Mesai', 'ekleme')
                cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)", (mh_id, b_ekmesai, float(overtime_pay)))
            employer_sgk = (taban * SGK_EMPLOYER_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            cursor.execute("INSERT INTO Maas_Detay (maas_hesap_id, bilesen_id, tutar) VALUES (%s, %s, %s)", (mh_id, b_sgk_isveren, float(employer_sgk)))
            created.append({'personel_id': pid, 'net_maas': float(net_maas), 'kesinti': float(toplam_kesinti)})

        conn.commit()
        return jsonify({'message': f'{len(created)} bordro oluşturuldu', 'created': created})
    except Exception as e:
        conn.rollback()
        print(f'Bordro oluşturma hatası: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@salary_bp.route("/salary/preview", methods=["POST"])
@login_required
def salary_preview():
    data = request.get_json() or {}
    try:
        yil = int(data.get('yil'))
        ay = int(data.get('ay'))
    except Exception:
        return jsonify({'error': 'yil ve ay zorunludur'}), 400

    personel_filter = data.get('personel_id')

    month_start = datetime.date(yil, ay, 1)
    last_day = calendar.monthrange(yil, ay)[1]
    month_end = datetime.date(yil, ay, last_day)
    working_days = 0
    cur = month_start
    while cur <= month_end:
        if cur.weekday() < 5:
            working_days += 1
        cur += datetime.timedelta(days=1)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT p.personel_id, p.ad, p.soyad, poz.taban_maas
            FROM Personel p
            LEFT JOIN Personel_Pozisyon pp ON p.personel_id = pp.personel_id AND pp.guncel_mi = 1
            LEFT JOIN Pozisyon poz ON pp.pozisyon_id = poz.pozisyon_id
            WHERE p.aktif_mi = 1
        """
        params = []
        if personel_filter:
            sql += " AND p.personel_id = %s"
            params.append(personel_filter)

        cursor.execute(sql, params)
        employees = cursor.fetchall()

        previews = []
        for row in employees:
            pid = row['personel_id']
            taban = Decimal(row.get('taban_maas') or 0)
            cursor.execute("""
                SELECT ik.baslangic_tarihi as bas, ik.bitis_tarihi as bit, it.ucretli_mi as ucretli
                FROM Izin_Kayit ik
                JOIN Izin_Turu it ON ik.izin_turu_id = it.izin_turu_id
                WHERE ik.personel_id = %s AND ik.onay_durumu = 'Onaylandi'
                  AND NOT (ik.bitis_tarihi < %s OR ik.baslangic_tarihi > %s)
            """, (pid, month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
            leaves = cursor.fetchall()
            unpaid_days = 0
            for l in leaves:
                try:
                    bas = l['bas'] if isinstance(l['bas'], datetime.date) else datetime.datetime.strptime(str(l['bas'])[:10], '%Y-%m-%d').date()
                    bit = l['bit'] if isinstance(l['bit'], datetime.date) else datetime.datetime.strptime(str(l['bit'])[:10], '%Y-%m-%d').date()
                except Exception:
                    continue
                overlap_start = max(bas, month_start)
                overlap_end = min(bit, month_end)
                if overlap_end < overlap_start:
                    continue
                d = overlap_start
                overlap_count = 0
                while d <= overlap_end:
                    if d.weekday() < 5:
                        overlap_count += 1
                    d += datetime.timedelta(days=1)
                if not l.get('ucretli'):
                    unpaid_days += overlap_count

            cursor.execute("SELECT SUM(ek_mesai_saat) as toplam_ek FROM Devam WHERE personel_id = %s AND tarih BETWEEN %s AND %s", (pid, month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d')))
            ek_row = cursor.fetchone()
            overtime_hours = float(ek_row['toplam_ek'] or 0)

            if working_days == 0:
                continue

            daily_rate = (taban / Decimal(working_days))
            unpaid_deduction = (daily_rate * Decimal(unpaid_days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sgk_employee = (taban * SGK_EMPLOYEE_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            taxable_monthly = (taban - sgk_employee - unpaid_deduction)
            if taxable_monthly < 0:
                taxable_monthly = Decimal('0.00')
            annual_taxable = (taxable_monthly * Decimal(12))
            annual_income = annual_income_tax(annual_taxable)
            monthly_income_tax = (annual_income / Decimal(12)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            hourly_rate = (daily_rate / Decimal(8))
            OVERTIME_MULTIPLIER = Decimal('1.5')
            overtime_pay = (hourly_rate * Decimal(overtime_hours) * OVERTIME_MULTIPLIER).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            toplam_kesinti = (unpaid_deduction + sgk_employee + monthly_income_tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            toplam_ekleme = overtime_pay
            net_maas = (taban - toplam_kesinti + toplam_ekleme).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            previews.append({
                'personel_id': pid,
                'ad': row.get('ad'),
                'soyad': row.get('soyad'),
                'brut_maas': float(taban),
                'unpaid_days': unpaid_days,
                'unpaid_deduction': float(unpaid_deduction),
                'sgk_employee': float(sgk_employee),
                'monthly_income_tax': float(monthly_income_tax),
                'overtime_hours': overtime_hours,
                'overtime_pay': float(overtime_pay),
                'toplam_kesinti': float(toplam_kesinti),
                'toplam_ekleme': float(toplam_ekleme),
                'net_maas': float(net_maas),
            })

        return jsonify({'previews': previews})
    except Exception as e:
        print(f'Bordro önizleme hatası: {e}')
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
            UPDATE Maas_Hesap SET odendi_mi = 1, odeme_tarihi = CURDATE()
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
def salary_pdf():
    yil = request.args.get('yil')
    ay = request.args.get('ay')
    personel = request.args.get('personel_id')

    archived = request.args.get('archived', '0')
    aktif_flag = 0 if str(archived) in ['1', 'true', 'True'] else 1

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT mh.maas_hesap_id, mh.personel_id, mh.donem_yil, mh.donem_ay,
                   mh.brut_maas, mh.toplam_ekleme, mh.toplam_kesinti, mh.net_maas,
                   mh.odeme_tarihi, mh.odendi_mi,
                   p.ad, p.soyad, d.departman_adi
            FROM Maas_Hesap mh
            JOIN Personel p ON mh.personel_id = p.personel_id
            LEFT JOIN Departman d ON p.departman_id = d.departman_id
            WHERE p.aktif_mi = %s
        """
        params = [aktif_flag]
        if yil:
            sql += " AND mh.donem_yil = %s"
            params.append(yil)
        if ay:
            sql += " AND mh.donem_ay = %s"
            params.append(ay)
        if personel:
            sql += " AND mh.personel_id = %s"
            params.append(personel)

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
        for m in maaslar:
            cursor.execute("SELECT md.tutar, mb.bilesen_adi, mb.bilesen_tipi FROM Maas_Detay md JOIN Maas_Bileseni mb ON md.bilesen_id = mb.bilesen_id WHERE md.maas_hesap_id = %s", (m['maas_hesap_id'],))
            m['detaylar'] = [{'bilesen_adi': d['bilesen_adi'], 'tutar': d['tutar'], 'tip': d['bilesen_tipi']} for d in cursor.fetchall()]
        gen = PDFGenerator()
        buffer = gen.payrolls_pdf(maaslar, yil=yil, ay=ay)
        fname = f"bordro_toplu_{ay}_{yil}.pdf" if yil and ay else "bordro_toplu.pdf"
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=fname)
    except Exception as e:
        print(f"PDF bordro hatası: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
