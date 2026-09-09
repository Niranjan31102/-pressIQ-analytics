from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
import fitz
from modules.avp_engine import finalize_calculations

NAVY = colors.HexColor('#061A3F')
NAVY_2 = colors.HexColor('#103A73')
BLUE = colors.HexColor('#1769E0')
GREEN = colors.HexColor('#087A57')
RED = colors.HexColor('#E53935')
TEXT = colors.HexColor('#0F172A')
GRID = colors.HexColor('#D8E1EC')
ALT = colors.HexColor('#F8FAFC')
WHITE = colors.white


def _safe_reason(value):
    text = '' if value is None else str(value).strip()
    return 'NA' if text.upper() in {'', 'NA', 'NAN', 'NONE'} else text


def _fmt_int(value):
    if pd.isna(value):
        return '—'
    return f"{int(round(float(value))):,}"


def _fmt_pct(value):
    if pd.isna(value):
        return '—'
    return f"{float(value):.2f}%"


def _first_date(data):
    if 'Edition Date' in data.columns and data['Edition Date'].notna().any():
        return pd.to_datetime(data['Edition Date'].dropna().iloc[0]).strftime('%d %B %Y')
    return '—'


def _report_shift(report_type):
    return 'NIGHT SHIFT' if str(report_type).strip().upper() == 'MAIN' else 'SUPPLEMENT'


def _build_summary(data):
    work = data.copy()
    work['_press'] = work['Machine'].astype(str).str.upper().str.strip()
    order = ['PRESS 1', 'PRESS 3', 'PRESS 4', 'PRESS 5']
    rows = []
    for press in order:
        group = work[work['_press'] == press]
        if group.empty:
            continue
        po = pd.to_numeric(group['PO'], errors='coerce').fillna(0).sum()
        pred = pd.to_numeric(group['Predicted Waste'], errors='coerce').sum(min_count=1)
        act = pd.to_numeric(group['Actual Waste'], errors='coerce').fillna(0).sum()
        rows.append({
            'name': press.title(),
            'predicted': round(pred / po * 100, 2) if po and pd.notna(pred) else None,
            'actual': round(act / po * 100, 2) if po else None,
        })
    total_po = pd.to_numeric(work['PO'], errors='coerce').fillna(0).sum()
    total_pred = pd.to_numeric(work['Predicted Waste'], errors='coerce').sum(min_count=1)
    total_act = pd.to_numeric(work['Actual Waste'], errors='coerce').fillna(0).sum()
    overall = {
        'predicted': round(total_pred / total_po * 100, 2) if total_po and pd.notna(total_pred) else None,
        'actual': round(total_act / total_po * 100, 2) if total_po else None,
    }
    return rows, overall


def _styles():
    return {
        'head': ParagraphStyle('head', fontName='Helvetica-Bold', fontSize=9.8, leading=11.2, textColor=WHITE, alignment=TA_CENTER),
        'subhead': ParagraphStyle('subhead', fontName='Helvetica-Bold', fontSize=9.2, leading=10.4, textColor=WHITE, alignment=TA_CENTER),
        'cell': ParagraphStyle('cell', fontName='Helvetica-Bold', fontSize=10.4, leading=12.4, textColor=TEXT, alignment=TA_CENTER),
        'reason': ParagraphStyle('reason', fontName='Helvetica-Bold', fontSize=10.4, leading=12.8, textColor=TEXT, alignment=TA_LEFT),
        'pred': ParagraphStyle('pred', fontName='Helvetica-Bold', fontSize=10.4, leading=12.4, textColor=BLUE, alignment=TA_CENTER),
        'bad': ParagraphStyle('bad', fontName='Helvetica-Bold', fontSize=10.4, leading=12.4, textColor=RED, alignment=TA_CENTER),
        'good': ParagraphStyle('good', fontName='Helvetica-Bold', fontSize=10.4, leading=12.4, textColor=GREEN, alignment=TA_CENTER),
        'summary_label': ParagraphStyle('summary_label', fontName='Helvetica-Bold', fontSize=9.5, leading=11, textColor=TEXT, alignment=TA_CENTER),
        'summary_pred': ParagraphStyle('summary_pred', fontName='Helvetica-Bold', fontSize=16.5, leading=18.5, textColor=BLUE, alignment=TA_CENTER),
        'summary_actual': ParagraphStyle('summary_actual', fontName='Helvetica-Bold', fontSize=16.5, leading=18.5, textColor=GREEN, alignment=TA_CENTER),
    }


def _make_main_table(data, available_width):
    st = _styles()
    proportions = [0.075, 0.085, 0.105, 0.075, 0.065, 0.065, 0.060, 0.065, 0.060, 0.075, 0.270]
    col_widths = [available_width * p for p in proportions]
    header_1 = [
        Paragraph('EDITION<br/>DATE', st['head']),
        Paragraph('PRESS', st['head']),
        Paragraph('MACHINE<br/>IN-CHARGE', st['head']),
        Paragraph('PUBLICATION', st['head']),
        Paragraph('PO', st['head']),
        Paragraph('PREDICTED WASTE', st['head']), '',
        Paragraph('ACTUAL WASTE', st['head']), '',
        Paragraph('EXTRA WASTE<br/>(Qty)', st['head']),
        Paragraph('REASON FOR EXTRA WASTE', st['head']),
    ]
    header_2 = ['', '', '', '', '', Paragraph('Qty', st['subhead']), Paragraph('%', st['subhead']), Paragraph('Qty', st['subhead']), Paragraph('%', st['subhead']), '', '']
    table_data = [header_1, header_2]
    for _, row in data.iterrows():
        pred_pct = row.get('Predicted %')
        actual_pct = row.get('Actual %')
        predicted_qty = row.get('Predicted Waste')
        actual_qty = row.get('Actual Waste')
        actual_style = st['cell']
        if pd.notna(pred_pct) and pd.notna(actual_pct):
            if float(actual_pct) > float(pred_pct):
                actual_style = st['bad']
            elif float(actual_pct) < float(pred_pct):
                actual_style = st['good']
        extra_style = st['cell']
        if pd.notna(predicted_qty) and pd.notna(actual_qty):
            if float(actual_qty) > float(predicted_qty):
                extra_style = st['bad']
            elif float(actual_qty) < float(predicted_qty):
                extra_style = st['good']
        date_value = pd.to_datetime(row['Edition Date']).strftime('%d/%m/%Y') if pd.notna(row.get('Edition Date')) else '—'
        table_data.append([
            Paragraph(date_value, st['cell']),
            Paragraph(str(row.get('Machine', '—')), st['cell']),
            Paragraph(str(row.get('Machine In-charge', '—')), st['cell']),
            Paragraph(str(row.get('Publication', '—')), st['cell']),
            Paragraph(_fmt_int(row.get('PO')), st['cell']),
            Paragraph(_fmt_int(row.get('Predicted Waste')), st['cell']),
            Paragraph(_fmt_pct(row.get('Predicted %')), st['pred']),
            Paragraph(_fmt_int(row.get('Actual Waste')), st['cell']),
            Paragraph(_fmt_pct(row.get('Actual %')), actual_style),
            Paragraph(_fmt_int(row.get('Extra Waste')), extra_style),
            Paragraph(_safe_reason(row.get('Reason for Extra Waste', 'NA')), st['reason']),
        ])
    table = Table(table_data, colWidths=col_widths, repeatRows=2, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0, 0), (-1, 1), NAVY_2),
        ('TEXTCOLOR', (0, 0), (-1, 1), WHITE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -2), 'CENTER'),
        ('ALIGN', (-1, 2), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.55, GRID),
        ('BOX', (0, 0), (-1, -1), 0.8, GRID),
        ('TOPPADDING', (0, 0), (-1, 1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 8),
        ('TOPPADDING', (0, 2), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 8),
        ('SPAN', (0, 0), (0, 1)), ('SPAN', (1, 0), (1, 1)), ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)), ('SPAN', (4, 0), (4, 1)), ('SPAN', (5, 0), (6, 0)),
        ('SPAN', (7, 0), (8, 0)), ('SPAN', (9, 0), (9, 1)), ('SPAN', (10, 0), (10, 1)),
    ]
    for r in range(2, len(table_data)):
        if (r - 2) % 2 == 1:
            style.append(('BACKGROUND', (0, r), (-1, r), ALT))
    table.setStyle(TableStyle(style))
    return table


def _draw_summary_card(c, x, y, w, h, title, machines, overall_value, kind):
    st = _styles()
    c.setFillColor(WHITE)
    c.setStrokeColor(GRID)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)
    head_h = 26
    c.setFillColor(NAVY_2)
    c.roundRect(x, y + h - head_h, w, head_h, 10, stroke=0, fill=1)
    c.rect(x, y + h - head_h, w, head_h / 2, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x + 12, y + h - 17, title)
    total_w = 92
    inner_y = y + 10
    inner_h = h - head_h - 18
    total_x = x + w - total_w - 10
    c.setFillColor(NAVY if kind == 'predicted' else colors.HexColor('#075F46'))
    c.roundRect(total_x, inner_y, total_w, inner_h, 9, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 8.5)
    c.drawCentredString(total_x + total_w / 2, inner_y + inner_h - 24, 'TOTAL PREDICT' if kind == 'predicted' else 'TOTAL ACTUAL')
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(total_x + total_w / 2, inner_y + 22, '—' if overall_value is None else f'{overall_value:.2f}%')
    metrics_left = x + 8
    metrics_right = total_x - 8
    metrics_width = metrics_right - metrics_left
    count = max(1, len(machines))
    each = metrics_width / count
    for idx, machine in enumerate(machines):
        mx = metrics_left + each * idx
        label_p = Paragraph(f"{machine['name']} %", st['summary_label'])
        lw, lh = label_p.wrap(each - 6, 30)
        label_p.drawOn(c, mx + (each - lw) / 2, inner_y + inner_h - 34)
        val = machine[kind]
        value_style = st['summary_pred'] if kind == 'predicted' else st['summary_actual']
        value_p = Paragraph('—' if val is None else f'{val:.2f}%', value_style)
        vw, vh = value_p.wrap(each - 6, 35)
        value_p.drawOn(c, mx + (each - vw) / 2, inner_y + 13)
        if idx < count - 1:
            c.setStrokeColor(colors.HexColor('#E5E7EB'))
            c.setLineWidth(0.45)
            c.line(mx + each, inner_y + 4, mx + each, inner_y + inner_h - 4)


def _build_pdf(data, report_type):
    machines, overall = _build_summary(data)
    page_w = 420 * mm
    left = 7.5 * mm
    right = 7.5 * mm
    content_w = page_w - left - right
    header_h = 36 * mm
    gap_after_header = 7 * mm
    summary_gap = 7 * mm
    summary_h = 46 * mm
    bottom = 7 * mm
    main_table = _make_main_table(data, content_w)
    table_w, table_h = main_table.wrap(content_w, 10000)
    page_h = header_h + gap_after_header + table_h + summary_gap + summary_h + bottom
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=(page_w, page_h))
    header_y = page_h - header_h
    c.setFillColor(NAVY)
    c.roundRect(0, header_y, page_w, header_h, 8, stroke=0, fill=1)
    c.rect(0, header_y, page_w, header_h - 8, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 27)
    c.drawString(10 * mm, page_h - 21 * mm, 'PIQ')
    c.setFont('Helvetica-Bold', 13)
    c.drawString(38 * mm, page_h - 19 * mm, 'PressIQ')
    c.setFont('Helvetica-Bold', 23)
    c.drawCentredString(page_w / 2, page_h - 16 * mm, 'Actual vs Predicted Waste Report')
    c.setFont('Helvetica-Bold', 11.5)
    c.setFillColor(colors.HexColor('#DBEAFE'))
    c.drawCentredString(page_w / 2, page_h - 27 * mm, f'{_report_shift(report_type)}  •  {_first_date(data)}')
    table_y = header_y - gap_after_header - table_h
    main_table.drawOn(c, left, table_y)
    summary_y = table_y - summary_gap - summary_h
    card_gap = 6 * mm
    card_w = (content_w - card_gap) / 2
    _draw_summary_card(c, left, summary_y, card_w, summary_h, 'PREDICTED SUMMARY', machines, overall['predicted'], 'predicted')
    _draw_summary_card(c, left + card_w + card_gap, summary_y, card_w, summary_h, 'ACTUAL SUMMARY', machines, overall['actual'], 'actual')
    c.showPage()
    c.save()
    return output.getvalue()


def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    pdf_bytes = _build_pdf(data, report_type)
    pdf = fitz.open(stream=pdf_bytes, filetype='pdf')
    page = pdf[0]
    matrix = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    png_bytes = pix.tobytes('png')
    pdf.close()
    return png_bytes
