from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# FINAL TOUCH-UP VERSION
# Focus: table readability, font size, boldness, clean summary
# ============================================================

NAVY = "#071F4A"
NAVY_2 = "#0C3470"
BLUE = "#1769E0"
GREEN = "#087A57"
RED = "#E53935"
TEXT = "#0F172A"
GRID = "#D8E1EC"
ALT = "#F7F9FC"
WHITE = "#FFFFFF"


def _font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def _txt(draw, xy, text, size=18, bold=False, fill=TEXT, anchor=None):
    draw.text(
        xy,
        str(text),
        font=_font(size, bold),
        fill=fill,
        anchor=anchor,
    )


def _center(draw, box, text, size=17, bold=False, fill=TEXT, spacing=4):
    x1, y1, x2, y2 = box
    font = _font(size, bold)
    value = str(text)

    bbox = draw.multiline_textbbox(
        (0, 0),
        value,
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
        value,
        font=font,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def _left(draw, box, text, size=17, bold=False, fill=TEXT, spacing=5):
    x1, y1, x2, y2 = box
    font = _font(size, bold)
    value = str(text)

    bbox = draw.multiline_textbbox(
        (0, 0),
        value,
        font=font,
        spacing=spacing,
    )

    th = bbox[3] - bbox[1]

    draw.multiline_text(
        (
            x1 + 14,
            y1 + max(8, ((y2 - y1) - th) / 2),
        ),
        value,
        font=font,
        fill=fill,
        spacing=spacing,
    )


def _safe_reason(value):
    text = "" if value is None else str(value).strip()

    if text.upper() in {"", "NA", "NAN", "NONE"}:
        return "NA"

    return text


def _fmt_int(value):
    return "—" if pd.isna(value) else f"{int(round(float(value))):,}"


def _fmt_pct(value):
    return "—" if pd.isna(value) else f"{float(value):.2f}%"


def _wrap_pixels(draw, text, max_width, font):
    words = str(text).split()

    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = f"{current} {word}"

        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)

    return lines


# ============================================================
# MACHINE SUMMARY
# ============================================================

def _machine_bucket(row):
    display_machine = str(row.get("Machine", "")).upper().strip()
    calc_machine = str(row.get("Calc Machine", "")).upper().strip()

    if "PRESS-4" in display_machine or "PRESS 4" in display_machine:
        return "PRESS-4 / COL B"

    if "CROMOMAN-C" in {display_machine, calc_machine}:
        return "CROMO"

    if "COLORMAN-A" in {display_machine, calc_machine}:
        return "COL A"

    if "COLORMAN-B" in {display_machine, calc_machine}:
        return "COL B"

    return display_machine or calc_machine or "OTHER"


def _build_summary(data):
    work = data.copy()
    work["_bucket"] = work.apply(_machine_bucket, axis=1)

    order = ["CROMO", "COL A", "COL B", "PRESS-4 / COL B"]
    machines = []

    for bucket in order:
        group = work[work["_bucket"] == bucket]

        if group.empty:
            continue

        po = pd.to_numeric(group["PO"], errors="coerce").fillna(0).sum()
        pred = pd.to_numeric(
            group["Predicted Waste"], errors="coerce"
        ).sum(min_count=1)
        actual = pd.to_numeric(
            group["Actual Waste"], errors="coerce"
        ).fillna(0).sum()

        machines.append(
            {
                "name": bucket,
                "predicted": round(pred / po * 100, 2)
                if po and pd.notna(pred)
                else None,
                "actual": round(actual / po * 100, 2)
                if po
                else None,
            }
        )

    po = pd.to_numeric(work["PO"], errors="coerce").fillna(0).sum()
    pred = pd.to_numeric(
        work["Predicted Waste"], errors="coerce"
    ).sum(min_count=1)
    actual = pd.to_numeric(
        work["Actual Waste"], errors="coerce"
    ).fillna(0).sum()

    overall = {
        "predicted": round(pred / po * 100, 2)
        if po and pd.notna(pred)
        else None,
        "actual": round(actual / po * 100, 2)
        if po
        else None,
    }

    return machines, overall


# ============================================================
# FINAL PNG
# ============================================================

def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    machines, overall = _build_summary(data)

    # Main target: readable on management WhatsApp/mobile.
    W = 1600
    M = 28

    HEADER_H = 112
    TABLE_GAP = 20
    GROUP_H = 48
    SUB_H = 44

    columns = [
        ("EDITION DATE", 120),
        ("MACHINE", 130),
        ("MACHINE\nIN-CHARGE", 150),
        ("PUBLICATION", 105),
        ("PO", 95),
        ("PRED QTY", 100),
        ("PRED %", 88),
        ("ACT QTY", 100),
        ("ACT %", 88),
        ("EXTRA WASTE\n(Qty)", 100),
        ("REASON FOR EXTRA WASTE", 496),
    ]

    widths = [w for _, w in columns]

    # Reason wrapping by actual pixel width.
    temp = Image.new("RGB", (W, 100), WHITE)
    tdraw = ImageDraw.Draw(temp)
    reason_font = _font(17, False)

    wrapped_reasons = []
    row_heights = []

    reason_width = columns[-1][1] - 28

    for _, row in data.iterrows():
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))

        lines = _wrap_pixels(
            tdraw,
            reason,
            reason_width,
            reason_font,
        )

        wrapped_reasons.append("\n".join(lines))

        # Compact normal rows, grow only when remark is genuinely long.
        if len(lines) == 1:
            row_h = 72
        elif len(lines) == 2:
            row_h = 86
        elif len(lines) == 3:
            row_h = 100
        else:
            row_h = 38 + len(lines) * 22

        row_heights.append(row_h)

    SUMMARY_GAP = 28
    SUMMARY_H = 200
    BOTTOM = 26

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
    # SIMPLE CLEAN HEADER
    # ========================================================

    draw.rounded_rectangle(
        (0, 0, W, HEADER_H),
        radius=18,
        fill=NAVY,
    )

    _txt(
        draw,
        (34, 30),
        "PIQ",
        46,
        True,
        WHITE,
    )

    _txt(
        draw,
        (128, 51),
        "PressIQ",
        22,
        True,
        "#E2E8F0",
    )

    _txt(
        draw,
        (W // 2, 36),
        "Actual vs Predicted Waste Report",
        34,
        True,
        WHITE,
        "ma",
    )

    issue_date = "—"

    if "Edition Date" in data.columns and data["Edition Date"].notna().any():
        issue_date = pd.to_datetime(
            data["Edition Date"].dropna().iloc[0]
        ).strftime("%d %B %Y")

    shift = (
        "MAIN SHIFT"
        if str(report_type).strip().upper() == "MAIN"
        else "SUPPLEMENT"
    )

    _txt(
        draw,
        (W // 2, 79),
        f"{shift}   •   {issue_date}",
        17,
        True,
        "#DCEAFF",
        "ma",
    )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    y = table_top

    fixed = [0, 1, 2, 3, 4, 9, 10]

    for idx in fixed:
        left = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (left, y, left + w, y + GROUP_H + SUB_H),
            fill=NAVY_2,
            outline="#5578AA",
            width=1,
        )

        _center(
            draw,
            (left, y, left + w, y + GROUP_H + SUB_H),
            columns[idx][0],
            15,
            True,
            WHITE,
        )

    pred_left = M + sum(widths[:5])
    pred_w = widths[5] + widths[6]

    draw.rectangle(
        (pred_left, y, pred_left + pred_w, y + GROUP_H),
        fill=NAVY_2,
        outline="#5578AA",
        width=1,
    )

    _txt(
        draw,
        (pred_left + pred_w / 2, y + GROUP_H / 2),
        "PREDICTED WASTE",
        15,
        True,
        WHITE,
        "mm",
    )

    act_left = M + sum(widths[:7])
    act_w = widths[7] + widths[8]

    draw.rectangle(
        (act_left, y, act_left + act_w, y + GROUP_H),
        fill=NAVY_2,
        outline="#5578AA",
        width=1,
    )

    _txt(
        draw,
        (act_left + act_w / 2, y + GROUP_H / 2),
        "ACTUAL WASTE",
        15,
        True,
        WHITE,
        "mm",
    )

    for idx, label in [
        (5, "Qty"),
        (6, "%"),
        (7, "Qty"),
        (8, "%"),
    ]:
        left = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (left, y + GROUP_H, left + w, y + GROUP_H + SUB_H),
            fill=NAVY_2,
            outline="#5578AA",
            width=1,
        )

        _txt(
            draw,
            (left + w / 2, y + GROUP_H + SUB_H / 2),
            label,
            14,
            True,
            WHITE,
            "mm",
        )

    y += GROUP_H + SUB_H

    # ========================================================
    # DATA ROWS
    # ========================================================

    for i, (_, row) in enumerate(data.iterrows()):
        row_h = row_heights[i]
        fill = WHITE if i % 2 == 0 else ALT

        edition_date = (
            pd.to_datetime(row["Edition Date"]).strftime("%d/%m/%Y")
            if pd.notna(row["Edition Date"])
            else "—"
        )

        values = [
            edition_date,
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
                fill=fill,
                outline=GRID,
                width=1,
            )

            # Management table: stronger visual hierarchy.
            color = TEXT
            bold = True if j in {1, 2, 3, 4, 5, 6, 7, 8, 9} else False

            if j == 6:
                color = BLUE

            if (
                j == 8
                and pd.notna(row.get("Predicted %"))
                and pd.notna(row.get("Actual %"))
                and float(row["Actual %"]) > float(row["Predicted %"])
            ):
                color = RED

            if (
                j == 9
                and pd.notna(row.get("Extra Waste"))
                and float(row["Extra Waste"]) > 0
            ):
                color = RED

            if j == 10:
                _left(
                    draw,
                    (x, y, x + w, y + row_h),
                    value,
                    17,
                    False,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (x, y, x + w, y + row_h),
                    value,
                    17,
                    bold,
                    color,
                )

            x += w

        y += row_h

    # ========================================================
    # SUMMARY
    # ========================================================

    y += SUMMARY_GAP

    gap = 22
    card_w = (W - 2 * M - gap) // 2

    def draw_summary(left, title, kind):
        draw.rounded_rectangle(
            (left, y, left + card_w, y + SUMMARY_H),
            radius=16,
            fill=WHITE,
            outline=GRID,
            width=2,
        )

        draw.rounded_rectangle(
            (left, y, left + card_w, y + 50),
            radius=16,
            fill=NAVY_2,
        )

        draw.rectangle(
            (left, y + 31, left + card_w, y + 50),
            fill=NAVY_2,
        )

        _txt(
            draw,
            (left + 20, y + 25),
            title,
            17,
            True,
            WHITE,
            "lm",
        )

        total_w = 160
        total_right = left + card_w - 18
        total_left = total_right - total_w

        metrics_left = left + 14
        metrics_right = total_left - 12
        metrics_w = metrics_right - metrics_left

        count = max(1, len(machines))
        each = metrics_w / count

        for idx, machine in enumerate(machines):
            cx = metrics_left + each * idx + each / 2

            label = machine["name"]
            label = (
                "PRESS-4 /\nCOL B %"
                if label == "PRESS-4 / COL B"
                else f"{label} %"
            )

            _center(
                draw,
                (cx - each / 2, y + 70, cx + each / 2, y + 118),
                label,
                14,
                True,
                TEXT,
            )

            value = (
                machine["predicted"]
                if kind == "pred"
                else machine["actual"]
            )

            _txt(
                draw,
                (cx, y + 151),
                "—" if value is None else f"{value:.2f}%",
                26,
                True,
                BLUE if kind == "pred" else GREEN,
                "ma",
            )

        total_top = y + 66
        total_bottom = y + 178

        draw.rounded_rectangle(
            (total_left, total_top, total_right, total_bottom),
            radius=14,
            fill=NAVY if kind == "pred" else "#075F46",
        )

        _txt(
            draw,
            ((total_left + total_right) / 2, total_top + 28),
            "TOTAL PREDICT" if kind == "pred" else "TOTAL ACTUAL",
            12,
            True,
            WHITE,
            "ma",
        )

        total_val = (
            overall["predicted"]
            if kind == "pred"
            else overall["actual"]
        )

        _txt(
            draw,
            ((total_left + total_right) / 2, total_top + 76),
            "—" if total_val is None else f"{total_val:.2f}%",
            31,
            True,
            WHITE,
            "ma",
        )

    draw_summary(
        M,
        "PREDICTED SUMMARY",
        "pred",
    )

    draw_summary(
        M + card_w + gap,
        "ACTUAL SUMMARY",
        "actual",
    )

    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()
