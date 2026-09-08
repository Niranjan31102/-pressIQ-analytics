from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# PRESSIQ EMERGENCY LARGE-TEXT PNG
# No Playwright / Chromium required.
# Designed to visually resemble the previous HTML report.
# ============================================================

NAVY = "#061A3F"
NAVY2 = "#0B2F63"
BLUE = "#1769E0"
GREEN = "#087A57"
RED = "#E53935"
TEXT = "#0F172A"
GRID = "#D8E1EC"
ALT = "#F8FAFC"
WHITE = "#FFFFFF"


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _center(draw, box, value, size=18, bold=False, fill=TEXT, spacing=4):
    x1, y1, x2, y2 = box
    text = str(value)
    font = _font(size, bold)

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=spacing,
        align="center",
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.multiline_text(
        (
            x1 + ((x2 - x1) - tw) / 2,
            y1 + ((y2 - y1) - th) / 2,
        ),
        text,
        font=font,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def _left(draw, box, value, size=18, bold=False, fill=TEXT, spacing=5):
    x1, y1, x2, y2 = box
    text = str(value)
    font = _font(size, bold)

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=spacing,
    )
    th = bbox[3] - bbox[1]

    draw.multiline_text(
        (
            x1 + 12,
            y1 + max(8, ((y2 - y1) - th) / 2),
        ),
        text,
        font=font,
        fill=fill,
        spacing=spacing,
    )


def _safe_reason(value):
    text = "" if value is None else str(value).strip()
    return "NA" if text.upper() in {"", "NA", "NAN", "NONE"} else text


def _fmt_int(value):
    if pd.isna(value):
        return "—"
    return f"{int(round(float(value))):,}"


def _fmt_pct(value):
    if pd.isna(value):
        return "—"
    return f"{float(value):.2f}%"


def _wrap_by_pixels(draw, text, max_width, font):
    words = str(text).split()

    if not words:
        return ["NA"]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word

        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _build_summary(data):
    work = data.copy()
    work["_press"] = work["Machine"].astype(str).str.upper().str.strip()

    press_order = ["PRESS 1", "PRESS 3", "PRESS 4", "PRESS 5"]
    result = []

    for press in press_order:
        group = work[work["_press"] == press]
        if group.empty:
            continue

        po = pd.to_numeric(group["PO"], errors="coerce").fillna(0).sum()
        pred = pd.to_numeric(group["Predicted Waste"], errors="coerce").sum(min_count=1)
        actual = pd.to_numeric(group["Actual Waste"], errors="coerce").fillna(0).sum()

        result.append(
            {
                "name": press.title(),
                "predicted": round(pred / po * 100, 2)
                if po and pd.notna(pred) else None,
                "actual": round(actual / po * 100, 2)
                if po else None,
            }
        )

    total_po = pd.to_numeric(work["PO"], errors="coerce").fillna(0).sum()
    total_pred = pd.to_numeric(work["Predicted Waste"], errors="coerce").sum(min_count=1)
    total_actual = pd.to_numeric(work["Actual Waste"], errors="coerce").fillna(0).sum()

    overall = {
        "predicted": round(total_pred / total_po * 100, 2)
        if total_po and pd.notna(total_pred) else None,
        "actual": round(total_actual / total_po * 100, 2)
        if total_po else None,
    }

    return result, overall


def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    machines, overall = _build_summary(data)

    # Smaller canvas than previous emergency version.
    # Streamlit therefore displays the text much larger.
    W = 1180
    M = 16

    HEADER_H = 118
    TABLE_GAP = 18
    GROUP_H = 52
    SUB_H = 44

    columns = [
        ("EDITION\nDATE", 88),
        ("PRESS", 88),
        ("MACHINE\nIN-CHARGE", 118),
        ("PUBLICATION", 82),
        ("PO", 76),
        ("PRED QTY", 74),
        ("PRED %", 66),
        ("ACT QTY", 74),
        ("ACT %", 66),
        ("EXTRA\nWASTE", 78),
        ("REASON FOR EXTRA WASTE", 338),
    ]

    widths = [w for _, w in columns]

    dummy = Image.new("RGB", (W, 100), WHITE)
    ddraw = ImageDraw.Draw(dummy)

    reason_font = _font(18, True)
    reason_inner_width = columns[-1][1] - 24

    wrapped_reasons = []
    row_heights = []

    for _, row in data.iterrows():
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))

        lines = _wrap_by_pixels(
            ddraw,
            reason,
            reason_inner_width,
            reason_font,
        )

        wrapped_reasons.append("\n".join(lines))

        if len(lines) == 1:
            row_h = 76
        elif len(lines) == 2:
            row_h = 90
        elif len(lines) == 3:
            row_h = 106
        else:
            row_h = 40 + len(lines) * 25

        row_heights.append(row_h)

    SUMMARY_GAP = 24
    SUMMARY_H = 200
    BOTTOM = 18

    table_top = HEADER_H + TABLE_GAP

    H = (
        table_top
        + GROUP_H
        + SUB_H
        + sum(row_heights)
        + SUMMARY_GAP
        + SUMMARY_H
        + BOTTOM
    )

    image = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(image)

    # ========================================================
    # HEADER
    # ========================================================

    draw.rounded_rectangle(
        (0, 0, W, HEADER_H),
        radius=18,
        fill=NAVY,
    )

    draw.text(
        (22, 27),
        "PIQ",
        font=_font(44, True),
        fill=WHITE,
    )

    draw.text(
        (102, 47),
        "PressIQ",
        font=_font(21, True),
        fill="#E2E8F0",
    )

    title = "Actual vs Predicted Waste Report"
    title_font = _font(34, True)
    tb = draw.textbbox((0, 0), title, font=title_font)
    tw = tb[2] - tb[0]

    draw.text(
        ((W - tw) / 2, 24),
        title,
        font=title_font,
        fill=WHITE,
    )

    issue_date = "—"
    if "Edition Date" in data.columns and data["Edition Date"].notna().any():
        issue_date = pd.to_datetime(
            data["Edition Date"].dropna().iloc[0]
        ).strftime("%d %B %Y")

    shift = (
        "NIGHT SHIFT"
        if str(report_type).strip().upper() == "MAIN"
        else "SUPPLEMENT"
    )

    subtitle = f"{shift}  •  {issue_date}"
    subtitle_font = _font(18, True)
    sb = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw = sb[2] - sb[0]

    draw.text(
        ((W - sw) / 2, 76),
        subtitle,
        font=subtitle_font,
        fill="#DCEAFF",
    )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    y = table_top

    fixed = [0, 1, 2, 3, 4, 9, 10]

    for idx in fixed:
        x = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (x, y, x + w, y + GROUP_H + SUB_H),
            fill=NAVY2,
            outline="#5476A5",
            width=1,
        )

        _center(
            draw,
            (x, y, x + w, y + GROUP_H + SUB_H),
            columns[idx][0],
            17,
            True,
            WHITE,
        )

    pred_left = M + sum(widths[:5])
    pred_w = widths[5] + widths[6]

    draw.rectangle(
        (pred_left, y, pred_left + pred_w, y + GROUP_H),
        fill=NAVY2,
        outline="#5476A5",
        width=1,
    )

    _center(
        draw,
        (pred_left, y, pred_left + pred_w, y + GROUP_H),
        "PREDICTED WASTE",
        17,
        True,
        WHITE,
    )

    actual_left = M + sum(widths[:7])
    actual_w = widths[7] + widths[8]

    draw.rectangle(
        (actual_left, y, actual_left + actual_w, y + GROUP_H),
        fill=NAVY2,
        outline="#5476A5",
        width=1,
    )

    _center(
        draw,
        (actual_left, y, actual_left + actual_w, y + GROUP_H),
        "ACTUAL WASTE",
        17,
        True,
        WHITE,
    )

    for idx, label in [(5, "Qty"), (6, "%"), (7, "Qty"), (8, "%")]:
        x = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (x, y + GROUP_H, x + w, y + GROUP_H + SUB_H),
            fill=NAVY2,
            outline="#5476A5",
            width=1,
        )

        _center(
            draw,
            (x, y + GROUP_H, x + w, y + GROUP_H + SUB_H),
            label,
            16,
            True,
            WHITE,
        )

    y += GROUP_H + SUB_H

    # ========================================================
    # TABLE ROWS
    # ========================================================

    for i, (_, row) in enumerate(data.iterrows()):
        row_h = row_heights[i]
        bg = WHITE if i % 2 == 0 else ALT

        date_text = (
            pd.to_datetime(row["Edition Date"]).strftime("%d/%m/%Y")
            if pd.notna(row["Edition Date"])
            else "—"
        )

        values = [
            date_text,
            row.get("Machine", "—"),
            row.get("Machine In-charge", "—"),
            row.get("Publication", "—"),
            _fmt_int(row.get("PO")),
            _fmt_int(row.get("Predicted Waste")),
            _fmt_pct(row.get("Predicted %")),
            _fmt_int(row.get("Actual Waste")),
            _fmt_pct(row.get("Actual %")),
            _fmt_int(row.get("Extra Waste")),
            wrapped_reasons[i],
        ]

        x = M

        for j, ((_, w), value) in enumerate(zip(columns, values)):
            draw.rectangle(
                (x, y, x + w, y + row_h),
                fill=bg,
                outline=GRID,
                width=1,
            )

            color = TEXT

            if j == 6:
                color = BLUE

            if (
                j == 8
                and pd.notna(row.get("Predicted %"))
                and pd.notna(row.get("Actual %"))
            ):
                if float(row["Actual %"]) > float(row["Predicted %"]):
                    color = RED
                elif float(row["Actual %"]) < float(row["Predicted %"]):
                    color = GREEN

            if (
                j == 9
                and pd.notna(row.get("Predicted Waste"))
                and pd.notna(row.get("Actual Waste"))
            ):
                if float(row["Actual Waste"]) > float(row["Predicted Waste"]):
                    color = RED
                elif float(row["Actual Waste"]) < float(row["Predicted Waste"]):
                    color = GREEN

            if j == 10:
                _left(
                    draw,
                    (x, y, x + w, y + row_h),
                    value,
                    18,
                    True,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (x, y, x + w, y + row_h),
                    value,
                    18,
                    True,
                    color,
                )

            x += w

        y += row_h

    # ========================================================
    # SUMMARY
    # ========================================================

    y += SUMMARY_GAP

    gap = 18
    card_w = (W - 2 * M - gap) // 2

    def draw_summary(left, title, kind):
        draw.rounded_rectangle(
            (left, y, left + card_w, y + SUMMARY_H),
            radius=14,
            fill=WHITE,
            outline=GRID,
            width=2,
        )

        draw.rounded_rectangle(
            (left, y, left + card_w, y + 50),
            radius=14,
            fill=NAVY2,
        )

        draw.rectangle(
            (left, y + 31, left + card_w, y + 50),
            fill=NAVY2,
        )

        draw.text(
            (left + 16, y + 14),
            title,
            font=_font(18, True),
            fill=WHITE,
        )

        total_w = 138
        total_right = left + card_w - 12
        total_left = total_right - total_w

        metrics_left = left + 10
        metrics_right = total_left - 8
        metrics_w = metrics_right - metrics_left

        count = max(1, len(machines))
        each = metrics_w / count

        for idx, machine in enumerate(machines):
            cx = metrics_left + each * idx + each / 2

            _center(
                draw,
                (cx - each / 2, y + 66, cx + each / 2, y + 111),
                f"{machine['name']} %",
                15,
                True,
                TEXT,
            )

            value = machine[kind]

            _center(
                draw,
                (cx - each / 2, y + 114, cx + each / 2, y + 172),
                "—" if value is None else f"{value:.2f}%",
                28,
                True,
                BLUE if kind == "predicted" else GREEN,
            )

        total_top = y + 62
        total_bottom = y + 177

        draw.rounded_rectangle(
            (total_left, total_top, total_right, total_bottom),
            radius=12,
            fill=NAVY if kind == "predicted" else "#075F46",
        )

        _center(
            draw,
            (total_left, total_top + 6, total_right, total_top + 47),
            "TOTAL PREDICT" if kind == "predicted" else "TOTAL ACTUAL",
            13,
            True,
            WHITE,
        )

        total_value = overall[kind]

        _center(
            draw,
            (total_left, total_top + 49, total_right, total_bottom - 6),
            "—" if total_value is None else f"{total_value:.2f}%",
            32,
            True,
            WHITE,
        )

    draw_summary(M, "PREDICTED SUMMARY", "predicted")
    draw_summary(M + card_w + gap, "ACTUAL SUMMARY", "actual")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
