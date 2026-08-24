from io import BytesIO
import textwrap

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations, machine_summary


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _text(draw, xy, text, size=20, bold=False, fill="#0f172a", anchor=None):
    draw.text(xy, str(text), font=_font(size, bold), fill=fill, anchor=anchor)


def _center(draw, box, text, size=16, bold=False, fill="#0f172a", spacing=4):
    x1, y1, x2, y2 = box
    font = _font(size, bold)
    value = str(text)
    bbox = draw.multiline_textbbox((0, 0), value, font=font, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = x1 + ((x2 - x1) - tw) / 2
    y = y1 + ((y2 - y1) - th) / 2
    draw.multiline_text((x, y), value, font=font, fill=fill, spacing=spacing, align="center")


def _left(draw, box, text, size=15, bold=False, fill="#0f172a", spacing=4):
    x1, y1, x2, y2 = box
    font = _font(size, bold)
    value = str(text)
    bbox = draw.multiline_textbbox((0, 0), value, font=font, spacing=spacing)
    th = bbox[3] - bbox[1]
    y = y1 + max(8, ((y2 - y1) - th) / 2)
    draw.multiline_text((x1 + 12, y), value, font=font, fill=fill, spacing=spacing)


def _safe_reason(value):
    text = "" if value is None else str(value).strip()
    return "NA" if text.upper() in {"", "NA", "NAN", "NONE"} else text


def _fmt_int(value):
    return "—" if pd.isna(value) else f"{int(round(float(value))):,}"


def _fmt_pct(value):
    return "—" if pd.isna(value) else f"{float(value):.2f}%"


def _machine_value(summary, machine, column):
    rec = summary[summary["Machine"].astype(str).str.upper() == str(machine).upper()]
    return None if rec.empty else rec.iloc[0][column]


def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    summary, overall = machine_summary(data)

    navy = "#061a3f"
    navy2 = "#0a2a5e"
    blue = "#2563eb"
    green = "#047857"
    green_light = "#34d399"
    red = "#dc2626"
    red_light = "#fb7185"
    text = "#0f172a"
    muted = "#64748b"
    grid = "#d9e2ef"
    alt = "#f8fafc"

    width = 2048
    margin = 34
    header_h = 190
    top_gap = 26
    group_h = 52
    sub_h = 54
    summary_h = 236

    columns = [
        ("EDITION DATE", 138),
        ("MACHINE", 180),
        ("MACHINE\nIN-CHARGE", 200),
        ("PUBLICATION", 130),
        ("PO", 132),
        ("PRED QTY", 132),
        ("PRED %", 112),
        ("ACT QTY", 132),
        ("ACT %", 112),
        ("EXTRA\nWASTE", 120),
        ("REASON FOR EXTRA WASTE", 592),
    ]
    widths = [w for _, w in columns]

    row_heights = []
    for _, row in data.iterrows():
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))
        lines = textwrap.wrap(reason, width=66, break_long_words=False, break_on_hyphens=False) or ["NA"]
        row_heights.append(max(86, 30 + len(lines) * 24))

    table_y = header_h + top_gap
    height = table_y + group_h + sub_h + sum(row_heights) + 34 + summary_h + 46
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Header
    draw.rounded_rectangle((0, 0, width, header_h), radius=28, fill=navy)
    _text(draw, (48, 54), "PIQ", 56, True, "white")
    _text(draw, (174, 76), "PressIQ", 24, True, "#e2e8f0")
    _text(draw, (width // 2, 54), "Actual vs Predicted Waste Report", 42, True, "white", "ma")

    date = "—"
    if "Edition Date" in data and data["Edition Date"].notna().any():
        date = pd.to_datetime(data["Edition Date"].dropna().iloc[0]).strftime("%d %B %Y")
    shift = "MAIN SHIFT" if str(report_type).strip().upper() == "MAIN" else "SUPPLEMENT"
    pill_w, pill_h = 390, 52
    pill_x = (width - pill_w) // 2
    pill_y = 110
    draw.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=26, fill="#0b2858", outline="#31558d", width=2)
    _text(draw, (width // 2, pill_y + pill_h / 2), f"{shift}   •   {date}", 20, True, "#eaf2ff", "mm")

    pred_total = overall["Predicted %"]
    act_total = overall["Actual %"]
    within = pred_total is not None and act_total is not None and act_total <= pred_total
    status = "WITHIN TARGET" if within else "ABOVE TARGET"
    status_color = green_light if within else red_light
    sx1, sy1, sx2, sy2 = width - 500, 24, width - 38, 162
    draw.rounded_rectangle((sx1, sy1, sx2, sy2), radius=20, fill="#071b40", outline="#1e5a72" if within else "#5f3046", width=2)
    _text(draw, ((sx1 + sx2) / 2, sy1 + 26), "PERFORMANCE STATUS", 16, True, "#cbd5e1", "ma")
    _text(draw, ((sx1 + sx2) / 2, sy1 + 64), status, 28, True, status_color, "ma")
    if pred_total is not None and act_total is not None:
        sign = "≤" if within else ">"
        _text(draw, ((sx1 + sx2) / 2, sy1 + 108), f"Actual {act_total:.2f}% {sign} Predicted {pred_total:.2f}%", 17, False, "white", "ma")

    # Table headers
    y = table_y
    fixed = [0, 1, 2, 3, 4, 9, 10]
    for index in fixed:
        name, col_w = columns[index]
        left = margin + sum(widths[:index])
        draw.rectangle((left, y, left + col_w, y + group_h + sub_h), fill=navy2, outline="#53719c", width=1)
        _center(draw, (left, y, left + col_w, y + group_h + sub_h), name, 15, True, "white")

    pred_left = margin + sum(widths[:5])
    pred_w = widths[5] + widths[6]
    draw.rectangle((pred_left, y, pred_left + pred_w, y + group_h), fill=navy2, outline="#53719c", width=1)
    _text(draw, (pred_left + pred_w / 2, y + group_h / 2), "PREDICTED WASTE", 15, True, "white", "mm")

    act_left = margin + sum(widths[:7])
    act_w = widths[7] + widths[8]
    draw.rectangle((act_left, y, act_left + act_w, y + group_h), fill=navy2, outline="#53719c", width=1)
    _text(draw, (act_left + act_w / 2, y + group_h / 2), "ACTUAL WASTE", 15, True, "white", "mm")

    for index, label in [(5, "Qty"), (6, "%"), (7, "Qty"), (8, "%")]:
        left = margin + sum(widths[:index])
        col_w = widths[index]
        draw.rectangle((left, y + group_h, left + col_w, y + group_h + sub_h), fill=navy2, outline="#53719c", width=1)
        _text(draw, (left + col_w / 2, y + group_h + sub_h / 2), label, 15, True, "white", "mm")

    y += group_h + sub_h

    # Rows
    for row_num, (_, row) in enumerate(data.iterrows()):
        row_h = row_heights[row_num]
        fill = "white" if row_num % 2 == 0 else alt
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))
        reason = "\n".join(textwrap.wrap(reason, width=66, break_long_words=False, break_on_hyphens=False) or ["NA"])
        values = [
            pd.to_datetime(row["Edition Date"]).strftime("%d/%m/%Y") if pd.notna(row["Edition Date"]) else "—",
            row["Machine"], row["Machine In-charge"], row["Publication"], _fmt_int(row["PO"]),
            _fmt_int(row["Predicted Waste"]), _fmt_pct(row["Predicted %"]), _fmt_int(row["Actual Waste"]),
            _fmt_pct(row["Actual %"]), _fmt_int(row["Extra Waste"]), reason,
        ]
        x = margin
        for j, ((_, col_w), value) in enumerate(zip(columns, values)):
            draw.rectangle((x, y, x + col_w, y + row_h), fill=fill, outline=grid, width=1)
            color = text
            bold = j in {5, 6, 7, 8, 9}
            if j == 6:
                color = blue
            if j == 8 and pd.notna(row["Predicted %"]) and pd.notna(row["Actual %"]) and row["Actual %"] > row["Predicted %"]:
                color = red
            if j == 9 and pd.notna(row["Extra Waste"]) and float(row["Extra Waste"]) > 0:
                color = red
            if j == 10:
                _left(draw, (x, y, x + col_w, y + row_h), value, 15, False, text)
            else:
                _center(draw, (x, y, x + col_w, y + row_h), value, 15, bold, color)
            x += col_w
        y += row_h

    # Summary
    y += 34
    gap = 22
    card_w = (width - 2 * margin - gap) // 2

    def draw_summary(left, title, kind):
        top = y
        bottom = top + summary_h - 24
        draw.rounded_rectangle((left, top, left + card_w, bottom), radius=20, fill="white", outline=grid, width=2)
        draw.rounded_rectangle((left, top, left + card_w, top + 58), radius=20, fill=navy2)
        draw.rectangle((left, top + 36, left + card_w, top + 58), fill=navy2)
        _text(draw, (left + 24, top + 30), title, 18, True, "white", "lm")

        machines = [("CROMO %", "Cromoman-C"), ("COL A %", "Colorman-A"), ("COL B %", "Colorman-B")]
        metric_area = card_w - 230
        metric_w = metric_area / 3
        for idx, (label, machine) in enumerate(machines):
            cx = left + metric_w * idx + metric_w / 2
            value = _machine_value(summary, machine, "Predicted %" if kind == "pred" else "Actual %")
            _text(draw, (cx, top + 105), label, 15, True, muted, "ma")
            _text(draw, (cx, top + 158), "—" if pd.isna(value) else f"{value:.2f}%", 30, True, blue if kind == "pred" else green, "ma")

        tx1, ty1 = left + card_w - 205, top + 82
        tx2, ty2 = left + card_w - 24, bottom - 26
        draw.rounded_rectangle((tx1, ty1, tx2, ty2), radius=16, fill=navy if kind == "pred" else "#065f46")
        _text(draw, ((tx1 + tx2) / 2, ty1 + 34), "TOTAL", 15, True, "white", "ma")
        total = overall["Predicted %" if kind == "pred" else "Actual %"]
        _text(draw, ((tx1 + tx2) / 2, ty1 + 90), "—" if total is None else f"{total:.2f}%", 34, True, "white", "ma")

    draw_summary(margin, "PREDICTED SUMMARY", "pred")
    draw_summary(margin + card_w + gap, "ACTUAL SUMMARY", "act")

    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()
