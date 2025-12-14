from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from io import BytesIO
import datetime


class PDFGenerator:

    def __init__(self):
        self.buffer = BytesIO()
        self.pagesize = A4
        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=30,
            alignment=1
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#495057'),
            spaceAfter=12
        )

    def _header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#0d6efd'))
        canvas.drawString(2 * cm, A4[1] - 2 * cm, "HR YÃ¶netim Sistemi")

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.5 * cm, f"OluÅŸturulma: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
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

        data = [['TC Kimlik', 'Ad Soyad', 'Departman', 'Pozisyon', 'MaaÅŸ', 'Telefon', 'Ä°ÅŸe GiriÅŸ']]

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
        <b>MaaÅŸ:</b> {personel.get('taban_maas', 0)} TL<br/>
        <b>Telefon:</b> {personel.get('telefon', '-')}<br/>
        <b>Email:</b> {personel.get('email', '-')}<br/>
        <b>Ä°ÅŸe GiriÅŸ:</b> {personel.get('ise_giris_tarihi', '-')}
        """
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 1 * cm))

        if devam_ozet:
            elements.append(Paragraph("Devam Durumu (Son 30 GÃ¼n)", self.heading_style))
            devam_data = [['Durum', 'GÃ¼n SayÄ±sÄ±']]
            for d in devam_ozet:
                durum_tr = {'Normal': 'Var', 'Izinli': 'Ä°zinli', 'Devamsiz': 'DevamsÄ±z'}.get(d.get('durum'),
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
            elements.append(devam_table)
            elements.append(Spacer(1, 0.5 * cm))

        if izinler:
            elements.append(Paragraph("Ä°zin GeÃ§miÅŸi", self.heading_style))
            izin_data = [['Ä°zin TÃ¼rÃ¼', 'BaÅŸlangÄ±Ã§', 'BitiÅŸ', 'GÃ¼n', 'Durum']]
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
            elements.append(izin_table)
            elements.append(Spacer(1, 0.5 * cm))

        if maaslar:
            elements.append(PageBreak())
            elements.append(Paragraph("MaaÅŸ BordrolarÄ± (Son 6 Ay)", self.heading_style))
            maas_data = [['DÃ¶nem', 'BrÃ¼t', 'Eklemeler', 'Kesintiler', 'Net', 'Durum']]
            for m in maaslar:
                durum = 'Ã–dendi' if m.get('odendi_mi') == 1 else 'Bekliyor'
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

        summary = Paragraph(f"<b>DÃ¶nem:</b> {tarih_baslangic} - {tarih_bitis}", self.styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.5 * cm))

        data = [['Tarih', 'Personel', 'Departman', 'Durum']]

        for d in devam_kayitlari:
            durum_tr = {'Normal': 'âœ“ Var', 'Izinli': 'âš  Ä°zinli', 'Devamsiz': 'âœ— Yok'}.get(d.get('durum'),
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
        title = Paragraph(f"Ä°zin Raporu{filtre_text}", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        data = [['Personel', 'Ä°zin TÃ¼rÃ¼', 'BaÅŸlangÄ±Ã§', 'BitiÅŸ', 'GÃ¼n SayÄ±sÄ±', 'Durum']]

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

    def maas_bordrosu_pdf(self, bordro_data):
        """
        Profesyonel maaş bordrosu PDF'i oluşturur
        bordro_data: {
            'personel': {...},
            'maas': {...},
            'detaylar': [...]
        }
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        # Başlık
        title = Paragraph("MAAŞ BORDROSU", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3 * cm))

        # Dönem bilgisi
        donem_text = f"<b>Dönem:</b> {bordro_data['maas']['donem_ay']}/{bordro_data['maas']['donem_yil']}"
        elements.append(Paragraph(donem_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.5 * cm))

        # Personel Bilgileri
        elements.append(Paragraph("Personel Bilgileri", self.heading_style))

        personel_info = f"""
        <b>Ad Soyad:</b> {bordro_data['personel']['ad']} {bordro_data['personel']['soyad']}<br/>
        <b>TC Kimlik No:</b> {bordro_data['personel'].get('tc_kimlik_no', '-')}<br/>
        <b>Departman:</b> {bordro_data['personel'].get('departman_adi', '-')}<br/>
        <b>Pozisyon:</b> {bordro_data['personel'].get('pozisyon_adi', '-')}
        """
        elements.append(Paragraph(personel_info, self.styles['Normal']))
        elements.append(Spacer(1, 0.8 * cm))

        # Maaş Özeti
        elements.append(Paragraph("Maaş Özeti", self.heading_style))

        ozet_data = [
            ['Açıklama', 'Tutar'],
            ['Brüt Maaş', f"{bordro_data['maas']['brut_maas']:,.2f} TL"],
            ['Toplam Eklemeler', f"+{bordro_data['maas']['toplam_ekleme']:,.2f} TL"],
            ['Toplam Kesintiler', f"-{bordro_data['maas']['toplam_kesinti']:,.2f} TL"],
        ]

        ozet_table = Table(ozet_data, colWidths=[10 * cm, 6 * cm])
        ozet_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(ozet_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Net Maaş (Vurgulu)
        net_maas_data = [['NET MAAŞ (Ödenen)', f"{bordro_data['maas']['net_maas']:,.2f} TL"]]
        net_table = Table(net_maas_data, colWidths=[10 * cm, 6 * cm])
        net_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
        ]))
        elements.append(net_table)
        elements.append(Spacer(1, 1 * cm))

        # Detaylı Hesaplama
        if bordro_data.get('detaylar'):
            elements.append(Paragraph("Detaylı Hesaplama", self.heading_style))

            detay_data = [['Bileşen', 'Tip', 'Tutar']]

            for detay in bordro_data['detaylar']:
                tip_color = 'green' if detay['tip'] == 'Ekleme' else 'red'
                tip_icon = '+' if detay['tip'] == 'Ekleme' else '-'

                detay_data.append([
                    detay['bilesen_adi'],
                    detay['tip'],
                    f"{tip_icon}{detay['tutar']:,.2f} TL"
                ])

            detay_table = Table(detay_data, colWidths=[8 * cm, 4 * cm, 4 * cm])
            detay_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            elements.append(detay_table)
            elements.append(Spacer(1, 1 * cm))

        # Ödeme Durumu
        odeme_durumu = 'ÖDENDİ' if bordro_data['maas'].get('odendi_mi') else 'ÖDEME BEKLENİYOR'
        odeme_color = colors.HexColor('#198754') if bordro_data['maas'].get('odendi_mi') else colors.HexColor('#ffc107')

        durum_text = f"<b>Durum:</b> {odeme_durumu}"
        if bordro_data['maas'].get('odeme_tarihi'):
            durum_text += f" | <b>Ödeme Tarihi:</b> {bordro_data['maas']['odeme_tarihi']}"

        elements.append(Paragraph(durum_text, self.styles['Normal']))
        elements.append(Spacer(1, 1.5 * cm))

        # İmza Alanları
        imza_data = [
            ['Personel İmzası', 'Muhasebe İmzası', 'Yönetici İmzası'],
            ['', '', ''],
            ['___________________', '___________________', '___________________']
        ]

        imza_table = Table(imza_data, colWidths=[5.3 * cm, 5.3 * cm, 5.3 * cm])
        imza_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, 1), 30),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(imza_table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer

    def toplu_maas_bordrosu_pdf(self, bordrolar):
        """
        Birden fazla personelin bordrosunu tek PDF'de oluşturur
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A4),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=3 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        # Ana başlık
        if bordrolar and len(bordrolar) > 0:
            donem = f"{bordrolar[0]['donem_ay']}/{bordrolar[0]['donem_yil']}"
            title = Paragraph(f"Maaş Bordroları Toplu Raporu - {donem}", self.title_style)
        else:
            title = Paragraph("Maaş Bordroları Toplu Raporu", self.title_style)

        elements.append(title)
        elements.append(Spacer(1, 0.5 * cm))

        summary = Paragraph(
            f"<b>Toplam Bordro Sayısı:</b> {len(bordrolar)} | <b>Oluşturulma:</b> {datetime.date.today().strftime('%d/%m/%Y')}",
            self.styles['Normal']
        )
        elements.append(summary)
        elements.append(Spacer(1, 0.5 * cm))

        # Tablo başlıkları
        data = [['Personel', 'Departman', 'Brüt Maaş', 'Eklemeler', 'Kesintiler', 'Net Maaş', 'Durum']]

        toplam_brut = 0
        toplam_ekleme = 0
        toplam_kesinti = 0
        toplam_net = 0

        for bordro in bordrolar:
            durum = '✓ Ödendi' if bordro.get('odendi_mi') else '⏳ Bekliyor'

            data.append([
                f"{bordro.get('ad', '')} {bordro.get('soyad', '')}",
                str(bordro.get('departman_adi', '-')),
                f"{bordro.get('brut_maas', 0):,.2f} TL",
                f"+{bordro.get('toplam_ekleme', 0):,.2f} TL",
                f"-{bordro.get('toplam_kesinti', 0):,.2f} TL",
                f"{bordro.get('net_maas', 0):,.2f} TL",
                durum
            ])

            toplam_brut += bordro.get('brut_maas', 0)
            toplam_ekleme += bordro.get('toplam_ekleme', 0)
            toplam_kesinti += bordro.get('toplam_kesinti', 0)
            toplam_net += bordro.get('net_maas', 0)

        # Toplam satırı
        data.append([
            'TOPLAM',
            '',
            f"{toplam_brut:,.2f} TL",
            f"+{toplam_ekleme:,.2f} TL",
            f"-{toplam_kesinti:,.2f} TL",
            f"{toplam_net:,.2f} TL",
            ''
        ])

        table = Table(data, colWidths=[5 * cm, 4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm])
        table.setStyle(TableStyle([
            # Başlık stili
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (5, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # İçerik stili
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            # Toplam satırı stili
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
        ]))

        elements.append(table)

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        self.buffer.seek(0)
        return self.buffer