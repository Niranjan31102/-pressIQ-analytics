from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# APPROVED MANAGEMENT REPORT DESIGN
# ============================================================

NAVY = "#041A3D"
NAVY_2 = "#0A2E63"
BLUE = "#1769E0"
GREEN = "#087A57"
RED = "#E53935"
TEXT = "#111827"
MUTED = "#64748B"
GRID = "#D8E1ED"
ALT = "#F8FAFC"
WHITE = "#FFFFFF"


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
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


def _center(draw, box, text, size=16, bold=False, fill=TEXT, spacing=4):
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


def _left(draw, box, text, size=15, bold=False, fill=TEXT, spacing=4):
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
            x1 + 12,
            y1 + max(8, ((y2 - y1) - th) / 2),
        ),
        value,
        font=font,
        fill=fill,
        spacing=spacing,
    )


def _safe_reason(value):
    text = "" if value is None else str(value).strip()
    return "NA" if text.upper() in {"", "NA", "NAN", "NONE"} else text


def _fmt_int(value):
    return "—" if pd.isna(value) else f"{int(round(float(value))):,}"


def _fmt_pct(value):
    return "—" if pd.isna(value) else f"{float(value):.2f}%"


def _wrap_pixels(draw, text, max_width, font, max_lines=None):
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

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while draw.textlength(last + "...", font=font) > max_width and len(last) > 1:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."

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
    result = []

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

        result.append(
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

    return result, overall


# ============================================================
# ICONS
# ============================================================

def _status_icon(draw, cx, cy, good):
    color = "#2FD19A" if good else "#FB7185"

    draw.ellipse(
        (cx - 30, cy - 30, cx + 30, cy + 30),
        outline=color,
        width=5,
    )

    if good:
        draw.line((cx - 14, cy, cx - 3, cy + 11), fill=color, width=6)
        draw.line((cx - 3, cy + 11, cx + 18, cy - 14), fill=color, width=6)
    else:
        draw.line((cx - 13, cy - 13, cx + 13, cy + 13), fill=color, width=5)
        draw.line((cx + 13, cy - 13, cx - 13, cy + 13), fill=color, width=5)


def _pred_icon(draw, cx, cy):
    draw.ellipse(
        (cx - 24, cy - 24, cx + 24, cy + 24),
        fill="#EFF6FF",
    )
    for dx, dy in [
        (0, -13), (9, -9), (13, 0), (9, 9),
        (0, 13), (-9, 9), (-13, 0), (-9, -9),
    ]:
        draw.ellipse(
            (cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3),
            fill=BLUE,
        )


def _actual_icon(draw, cx, cy):
    draw.ellipse(
        (cx - 24, cy - 24, cx + 24, cy + 24),
        fill="#ECFDF5",
    )
    draw.polygon(
        [
            (cx, cy - 16),
            (cx - 11, cy + 4),
            (cx - 7, cy + 13),
            (cx, cy + 18),
            (cx + 7, cy + 13),
            (cx + 11, cy + 4),
        ],
        fill=GREEN,
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    machine_summary, overall = _build_summary(data)

    # Approved reference is around 1536 wide. Keep same visual density.
    W = 1536
    M = 28

    HEADER_H = 148
    TABLE_TOP_GAP = 28
    GROUP_H = 46
    SUB_H = 40

    columns = [
        ("EDITION DATE", 115),
        ("MACHINE", 125),
        ("MACHINE\nIN-CHARGE", 145),
        ("PUBLICATION", 102),
        ("PO", 92),
        ("PRED QTY", 92),
        ("PRED %", 80),
        ("ACT QTY", 92),
        ("ACT %", 80),
        ("EXTRA WASTE\n(Qty)", 102),
        ("REASON FOR EXTRA WASTE", 483),
    ]
    widths = [w for _, w in columns]

    # Temporary draw for pixel-accurate reason wrapping.
    dummy = Image.new("RGB", (W, 100), WHITE)
    ddraw = ImageDraw.Draw(dummy)
    reason_font = _font(15, False)

    wrapped_reasons = []
    row_heights = []

    reason_inner_width = columns[-1][1] - 26

    for _, row in data.iterrows():
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))
        lines = _wrap_pixels(
            ddraw,
            reason,
            reason_inner_width,
            reason_font,
        )
        wrapped_reasons.append("\n".join(lines))

        if len(lines) == 1:
            row_h = 70
        elif len(lines) == 2:
            row_h = 80
        else:
            row_h = max(92, 30 + len(lines) * 21)

        row_heights.append(row_h)

    SUMMARY_GAP = 34
    SUMMARY_H = 202
    BOTTOM = 28

    table_top = HEADER_H + TABLE_TOP_GAP

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
        radius=20,
        fill=NAVY,
    )

    _txt(draw, (34, 40), "PIQ", 50, True, WHITE)
    _txt(draw, (133, 60), "PressIQ Analytics", 19, True, "#E2E8F0")

    _txt(
        draw,
        (W // 2, 38),
        "Actual vs Predicted Waste Report",
        35,
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

    pill_w = 308
    pill_h = 40
    px = W // 2 - pill_w // 2
    py = 92

    draw.rounded_rectangle(
        (px, py, px + pill_w, py + pill_h),
        radius=20,
        fill="#0B2858",
        outline="#315C95",
        width=2,
    )

    _txt(
        draw,
        (W // 2, py + pill_h / 2),
        f"{shift}    {issue_date}",
        15,
        True,
        "#F0F6FF",
        "mm",
    )

    pred_total = overall["predicted"]
    act_total = overall["actual"]

    within = (
        pred_total is not None
        and act_total is not None
        and act_total <= pred_total
    )

    status = "WITHIN TARGET" if within else "ABOVE TARGET"
    status_color = "#34D399" if within else "#FB7185"

    sx1 = W - 365
    sy1 = 16
    sx2 = W - 22
    sy2 = 132

    draw.rounded_rectangle(
        (sx1, sy1, sx2, sy2),
        radius=16,
        fill="#071B40",
        outline="#1C665C" if within else "#76334B",
        width=2,
    )

    _status_icon(draw, sx1 + 54, sy1 + 56, within)

    _txt(
        draw,
        (sx1 + 101, sy1 + 19),
        "PERFORMANCE STATUS",
        12,
        True,
        "#CBD5E1",
    )
    _txt(
        draw,
        (sx1 + 101, sy1 + 47),
        status,
        21,
        True,
        status_color,
    )

    if pred_total is not None and act_total is not None:
        sign = "≤" if within else ">"
        _txt(
            draw,
            (sx1 + 101, sy1 + 84),
            f"Actual {act_total:.2f}% {sign} Predicted {pred_total:.2f}%",
            13,
            False,
            WHITE,
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
            outline="#496A98",
            width=1,
        )

        _center(
            draw,
            (left, y, left + w, y + GROUP_H + SUB_H),
            columns[idx][0],
            13,
            True,
            WHITE,
        )

    pred_left = M + sum(widths[:5])
    pred_w = widths[5] + widths[6]

    draw.rectangle(
        (pred_left, y, pred_left + pred_w, y + GROUP_H),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )
    _txt(
        draw,
        (pred_left + pred_w / 2, y + GROUP_H / 2),
        "PREDICTED WASTE",
        13,
        True,
        WHITE,
        "mm",
    )

    act_left = M + sum(widths[:7])
    act_w = widths[7] + widths[8]

    draw.rectangle(
        (act_left, y, act_left + act_w, y + GROUP_H),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )
    _txt(
        draw,
        (act_left + act_w / 2, y + GROUP_H / 2),
        "ACTUAL WASTE",
        13,
        True,
        WHITE,
        "mm",
    )

    for idx, label in [(5, "Qty"), (6, "%"), (7, "Qty"), (8, "%")]:
        left = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (left, y + GROUP_H, left + w, y + GROUP_H + SUB_H),
            fill=NAVY_2,
            outline="#496A98",
            width=1,
        )
        _txt(
            draw,
            (left + w / 2, y + GROUP_H + SUB_H / 2),
            label,
            13,
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

            color = TEXT
            bold = j in {5, 6, 7, 8, 9}

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
                    15,
                    False,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (x, y, x + w, y + row_h),
                    value,
                    15,
                    bold,
                    color,
                )

            x += w

        y += row_h

    # ========================================================
    # SUMMARY SECTION
    # ========================================================

    y += SUMMARY_GAP

    gap = 22
    card_w = (W - 2 * M - gap) // 2

    def draw_summary(left, title, kind):
        draw.rounded_rectangle(
            (left, y, left + card_w, y + SUMMARY_H),
            radius=18,
            fill=WHITE,
            outline=GRID,
            width=2,
        )

        draw.rounded_rectangle(
            (left, y, left + card_w, y + 48),
            radius=18,
            fill=NAVY_2,
        )
        draw.rectangle(
            (left, y + 29, left + card_w, y + 48),
            fill=NAVY_2,
        )

        _txt(
            draw,
            (left + 20, y + 24),
            title,
            15,
            True,
            WHITE,
            "lm",
        )

        total_w = 150
        total_right = left + card_w - 18
        total_left = total_right - total_w

        metrics_left = left + 14
        metrics_right = total_left - 12
        metrics_w = metrics_right - metrics_left

        count = max(1, len(machine_summary))
        each = metrics_w / count

        for idx, machine in enumerate(machine_summary):
            cx = metrics_left + each * idx + each / 2

            if kind == "pred":
                _pred_icon(draw, cx, y + 86)
            else:
                _actual_icon(draw, cx, y + 86)

            label = machine["name"]
            label = (
                "PRESS-4 /\nCOL B %"
                if label == "PRESS-4 / COL B"
                else f"{label} %"
            )

            _center(
                draw,
                (cx - each / 2, y + 111, cx + each / 2, y + 148),
                label,
                12,
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
                (cx, y + 176),
                "—" if value is None else f"{value:.2f}%",
                23,
                True,
                BLUE if kind == "pred" else GREEN,
                "ma",
            )

        total_top = y + 65
        total_bottom = y + 184

        draw.rounded_rectangle(
            (total_left, total_top, total_right, total_bottom),
            radius=14,
            fill=NAVY if kind == "pred" else "#075F46",
        )

        _txt(
            draw,
            ((total_left + total_right) / 2, total_top + 29),
            "TOTAL PREDICT" if kind == "pred" else "TOTAL ACTUAL",
            12,
            True,
            WHITE,
            "ma",
        )

        total_value = (
            overall["predicted"]
            if kind == "pred"
            else overall["actual"]
        )

        _txt(
            draw,
            ((total_left + total_right) / 2, total_top + 80),
            "—" if total_value is None else f"{total_value:.2f}%",
            31,
            True,
            WHITE,
            "ma",
        )

    draw_summary(M, "PREDICTED SUMMARY", "pred")
    draw_summary(M + card_w + gap, "ACTUAL SUMMARY", "actual")

    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()
