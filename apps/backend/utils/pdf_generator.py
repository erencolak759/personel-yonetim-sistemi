from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import datetime
class PDFGenerator:

    def __init__(self):
        self.buffer = BytesIO()
        self.pagesize = A4
        self.styles = getSampleStyleSheet()
        self.font_name = self._register_font()
        if self.font_name:
            for k in ['Normal', 'BodyText', 'Heading1', 'Heading2']:
                if k in self.styles:
                    try:
                        self.styles[k].fontName = self.font_name
                    except Exception:
                        pass

        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0d6efd'),
            fontName=self.font_name or self.styles['Heading1'].fontName,
            spaceAfter=30,
            alignment=1
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#495057'),
            fontName=self.font_name or self.styles['Heading2'].fontName,
            spaceAfter=12
        )

    def _register_font(self):
        candidates = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
            '/Library/Fonts/Arial Unicode.ttf',
            '/Library/Fonts/DejaVu Sans.ttf',
            'C:\\Windows\\Fonts\\arial.ttf'
        ]

        for path in candidates:
            try:
                if os.path.exists(path):
                    font_name = 'CustomSans'
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    return font_name
            except Exception:
                continue

        env_path = os.environ.get('DEJAVU_TTF_PATH')
        if env_path and os.path.exists(env_path):
            try:
                font_name = 'CustomSans'
                pdfmetrics.registerFont(TTFont(font_name, env_path))
                return font_name
            except Exception:
                pass

        return None

    def _header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#0d6efd'))
        canvas.drawString(2 * cm, A4[1] - 2 * cm, "HR Yönetim Sistemi")

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.5 * cm, f"Oluşturulma: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.5 * cm, f"Sayfa {doc.page}")

        canvas.restoreState()

    def personel_listesi_pdf(self, personeller):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        title = Paragraph("Personel Listesi Raporu", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        summary = Paragraph(
            f"<b>Toplam Personel:</b> {len(personeller)} | <b>Tarih:</b> {datetime.date.today().strftime('%d/%m/%Y')}",
            self.styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.5 * cm))

        data = [['TC Kimlik', 'Ad Soyad', 'Departman', 'Pozisyon', 'Maaş', 'Telefon', 'İşe Giriş']]

        for p in personeller:
            data.append([
                str(p.get('tc_kimlik_no', '-')),
                f"{p.get('ad', '')} {p.get('soyad', '')}",
                str(p.get('departman_adi', '-')),
                str(p.get('pozisyon_adi', '-')),
                f"{p.get('taban_maas', 0)} TL",
                str(p.get('telefon', '-')),
                str(p.get('ise_giris_tarihi', '-'))
            ])

        table = Table(data, colWidths=[3 * cm, 4 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm, 3 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        if self.font_name:
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.font_name)
            ]))

        elements.append(table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer

    def personel_detay_pdf(self, personel, izinler, devam_ozet, maaslar):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        title = Paragraph(f"Personel Detay Raporu", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        info_text = f"""
        <b>Ad Soyad:</b> {personel.get('ad', '')} {personel.get('soyad', '')}<br/>
        <b>TC Kimlik:</b> {personel.get('tc_kimlik_no', '-')}<br/>
        <b>Departman:</b> {personel.get('departman_adi', '-')}<br/>
        <b>Pozisyon:</b> {personel.get('pozisyon_adi', '-')}<br/>
        <b>Maaş:</b> {personel.get('taban_maas', 0)} TL<br/>
        <b>Telefon:</b> {personel.get('telefon', '-')}<br/>
        <b>Email:</b> {personel.get('email', '-')}<br/>
        <b>İşe Giriş:</b> {personel.get('ise_giris_tarihi', '-')}
        """
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 1 * cm))

        if devam_ozet:
            elements.append(Paragraph("Devam Durumu (Son 30 Gün)", self.heading_style))
            devam_data = [['Durum', 'Gün Sayısı']]
            for d in devam_ozet:
                durum_tr = {'Normal': 'Var', 'Izinli': 'İzinli', 'Devamsiz': 'Devamsız'}.get(d.get('durum'),
                                                                                             d.get('durum'))
                devam_data.append([durum_tr, str(d.get('adet', 0))])

            devam_table = Table(devam_data, colWidths=[8 * cm, 4 * cm])
            devam_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            if self.font_name:
                devam_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.font_name)
                ]))
            elements.append(devam_table)
            elements.append(Spacer(1, 0.5 * cm))

        if izinler:
            elements.append(Paragraph("İzin Geçmişi", self.heading_style))
            izin_data = [['İzin Türü', 'Başlangıç', 'Bitiş', 'Gün', 'Durum']]
            for iz in izinler:
                izin_data.append([
                    str(iz.get('izin_adi', '-')),
                    str(iz.get('baslangic_tarihi', '-')),
                    str(iz.get('bitis_tarihi', '-')),
                    str(iz.get('gun_sayisi', 0)),
                    str(iz.get('onay_durumu', '-'))
                ])

            izin_table = Table(izin_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 2 * cm, 3 * cm])
            izin_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0dcaf0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            if self.font_name:
                izin_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.font_name)
                ]))
            elements.append(izin_table)
            elements.append(Spacer(1, 0.5 * cm))

        if maaslar:
            elements.append(PageBreak())
            elements.append(Paragraph("Maaş Bordroları (Son 6 Ay)", self.heading_style))
            maas_data = [['Dönem', 'Brüt', 'Eklemeler', 'Kesintiler', 'Net', 'Durum']]
            for m in maaslar:
                durum = 'Ödendi' if m.get('odendi_mi') == 1 else 'Bekliyor'
                maas_data.append([
                    f"{m.get('donem_ay')}/{m.get('donem_yil')}",
                    f"{m.get('brut_maas', 0)} TL",
                    f"+{m.get('toplam_ekleme', 0)} TL",
                    f"-{m.get('toplam_kesinti', 0)} TL",
                    f"{m.get('net_maas', 0)} TL",
                    durum
                ])

            maas_table = Table(maas_data, colWidths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
            maas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            if self.font_name:
                maas_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.font_name)
                ]))
            elements.append(maas_table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer

    def devam_raporu_pdf(self, devam_kayitlari, tarih_baslangic, tarih_bitis):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        title = Paragraph(f"Devam Raporu", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        summary = Paragraph(f"<b>Dönem:</b> {tarih_baslangic} - {tarih_bitis}", self.styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.5 * cm))

        data = [['Tarih', 'Personel', 'Departman', 'Durum']]

        for d in devam_kayitlari:
            durum_tr = {'Normal': '✓ Var', 'Izinli': '⚠ İzinli', 'Devamsiz': '✗ Yok'}.get(d.get('durum'),
                                                                                          d.get('durum'))
            data.append([
                str(d.get('tarih', '-')),
                f"{d.get('ad', '')} {d.get('soyad', '')}",
                str(d.get('departman_adi', '-')),
                durum_tr
            ])

        table = Table(data, colWidths=[4 * cm, 6 * cm, 5 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        elements.append(table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer

    def izin_raporu_pdf(self, izinler, filtre=None):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        filtre_text = f" ({filtre})" if filtre else ""
        title = Paragraph(f"İzin Raporu{filtre_text}", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        data = [['Personel', 'İzin Türü', 'Başlangıç', 'Bitiş', 'Gün Sayısı', 'Durum']]

        for iz in izinler:
            data.append([
                f"{iz.get('ad', '')} {iz.get('soyad', '')}",
                str(iz.get('izin_adi', '-')),
                str(iz.get('baslangic_tarihi', '-')),
                str(iz.get('bitis_tarihi', '-')),
                str(iz.get('gun_sayisi', 0)),
                str(iz.get('onay_durumu', '-'))
            ])

        table = Table(data, colWidths=[5 * cm, 4 * cm, 3 * cm, 3 * cm, 2.5 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0dcaf0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        elements.append(table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer

    def payrolls_pdf(self, maaslar, yil=None, ay=None):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        title_text = "Maaş Bordroları"
        if yil and ay:
            title_text += f" - {ay}/{yil}"
        title = Paragraph(title_text, self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))
        data = [['Personel', 'Departman', 'Brüt', 'Eklemeler', 'Kesintiler', 'Net']]

        for m in maaslar:
            durum = 'Ödendi' if m.get('odendi_mi') else 'Bekliyor'
            data.append([
                f"{m.get('ad','')} {m.get('soyad','')}",
                m.get('departman_adi', '-'),
                f"{m.get('brut_maas', 0):,.2f} ₺",
                f"+{m.get('toplam_ekleme', 0):,.2f} ₺",
                f"-{m.get('toplam_kesinti', 0):,.2f} ₺",
                f"{m.get('net_maas', 0):,.2f} ₺",
            ])

        table = Table(data, colWidths=[6 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        if self.font_name:
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.font_name)
            ]))

        elements.append(table)
        for m in maaslar:
            elements.append(Spacer(1, 0.3 * cm))
            elements.append(Paragraph(f"Detaylar: {m.get('ad','')} {m.get('soyad','')} - {m.get('donem_ay')}/{m.get('donem_yil')}", self.heading_style))
            detay_data = [['Bileşen', 'Tutar']]
            for d in m.get('detaylar', []):
                tut = d.get('tutar', 0) or 0
                prefix = '+' if (d.get('tip') == 'ekleme') else '-'
                detay_data.append([d.get('bilesen_adi', ''), f"{prefix}{float(tut):,.2f} ₺"])

            dt = Table(detay_data, colWidths=[10 * cm, 4 * cm])
            dt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            if self.font_name:
                dt.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), self.font_name)]))
            elements.append(dt)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer