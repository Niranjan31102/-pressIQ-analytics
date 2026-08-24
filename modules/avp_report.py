from io import BytesIO
import textwrap

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# DESIGN CONSTANTS
# ============================================================

NAVY = "#061A3F"
NAVY_2 = "#0A2B63"
BLUE = "#123C78"
BLUE_VALUE = "#1769E0"
GREEN = "#087A57"
GREEN_VALUE = "#07875F"
RED = "#E53935"
TEXT = "#111827"
MUTED = "#64748B"
GRID = "#D9E2EF"
ALT = "#F8FAFC"
WHITE = "#FFFFFF"


# ============================================================
# FONT / TEXT HELPERS
# ============================================================

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
            continue

    return ImageFont.load_default()


def _text(draw, xy, value, size=20, bold=False, fill=TEXT, anchor=None):
    draw.text(
        xy,
        str(value),
        font=_font(size, bold),
        fill=fill,
        anchor=anchor,
    )


def _center(draw, box, value, size=18, bold=False, fill=TEXT, spacing=4):
    x1, y1, x2, y2 = box
    value = str(value)
    font = _font(size, bold)

    bbox = draw.multiline_textbbox(
        (0, 0),
        value,
        font=font,
        spacing=spacing,
        align="center",
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = x1 + ((x2 - x1) - tw) / 2
    y = y1 + ((y2 - y1) - th) / 2

    draw.multiline_text(
        (x, y),
        value,
        font=font,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def _left(draw, box, value, size=18, bold=False, fill=TEXT, spacing=5):
    x1, y1, x2, y2 = box
    value = str(value)
    font = _font(size, bold)

    bbox = draw.multiline_textbbox(
        (0, 0),
        value,
        font=font,
        spacing=spacing,
    )

    th = bbox[3] - bbox[1]
    y = y1 + max(10, ((y2 - y1) - th) / 2)

    draw.multiline_text(
        (x1 + 14, y),
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
    if pd.isna(value):
        return "—"

    return f"{int(round(float(value))):,}"


def _fmt_pct(value):
    if pd.isna(value):
        return "—"

    return f"{float(value):.2f}%"


# ============================================================
# MACHINE SUMMARY
# ============================================================

def _machine_bucket(row):
    display_machine = str(row.get("Machine", "")).strip().upper()
    calc_machine = str(row.get("Calc Machine", "")).strip().upper()

    # Press-4 gets its own summary bucket and must not be counted in COL B.
    if "PRESS-4" in display_machine or "PRESS 4" in display_machine:
        return "PRESS-4 / COL B"

    if calc_machine == "CROMOMAN-C" or display_machine == "CROMOMAN-C":
        return "CROMO"

    if calc_machine == "COLORMAN-A" or display_machine == "COLORMAN-A":
        return "COL A"

    if calc_machine == "COLORMAN-B" or display_machine == "COLORMAN-B":
        return "COL B"

    return display_machine or calc_machine or "OTHER"


def _build_machine_summary(data):
    work = data.copy()
    work["_Summary Machine"] = work.apply(_machine_bucket, axis=1)

    order = ["CROMO", "COL A", "COL B", "PRESS-4 / COL B"]
    summary = []

    for bucket in order:
        group = work[work["_Summary Machine"] == bucket]

        if group.empty:
            continue

        total_po = pd.to_numeric(group["PO"], errors="coerce").fillna(0).sum()
        total_pred = pd.to_numeric(
            group["Predicted Waste"], errors="coerce"
        ).sum(min_count=1)
        total_actual = pd.to_numeric(
            group["Actual Waste"], errors="coerce"
        ).fillna(0).sum()

        summary.append(
            {
                "Label": bucket,
                "Predicted %": (
                    round(total_pred / total_po * 100, 2)
                    if total_po and pd.notna(total_pred)
                    else None
                ),
                "Actual %": (
                    round(total_actual / total_po * 100, 2)
                    if total_po
                    else None
                ),
            }
        )

    total_po = pd.to_numeric(work["PO"], errors="coerce").fillna(0).sum()
    total_pred = pd.to_numeric(
        work["Predicted Waste"], errors="coerce"
    ).sum(min_count=1)
    total_actual = pd.to_numeric(
        work["Actual Waste"], errors="coerce"
    ).fillna(0).sum()

    overall = {
        "Predicted %": (
            round(total_pred / total_po * 100, 2)
            if total_po and pd.notna(total_pred)
            else None
        ),
        "Actual %": (
            round(total_actual / total_po * 100, 2)
            if total_po
            else None
        ),
    }

    return summary, overall


# ============================================================
# DECORATIVE ICONS
# ============================================================

def _draw_status_icon(draw, center, good):
    cx, cy = center
    outline = "#16C98D" if good else "#FB7185"

    draw.ellipse(
        (cx - 34, cy - 34, cx + 34, cy + 34),
        outline=outline,
        width=5,
    )

    if good:
        draw.line(
            (cx - 16, cy, cx - 3, cy + 13),
            fill=outline,
            width=6,
        )
        draw.line(
            (cx - 3, cy + 13, cx + 20, cy - 14),
            fill=outline,
            width=6,
        )
    else:
        draw.line(
            (cx - 15, cy - 15, cx + 15, cy + 15),
            fill=outline,
            width=5,
        )
        draw.line(
            (cx + 15, cy - 15, cx - 15, cy + 15),
            fill=outline,
            width=5,
        )


def _draw_summary_icon(draw, center, kind, color):
    cx, cy = center

    draw.ellipse(
        (cx - 27, cy - 27, cx + 27, cy + 27),
        fill="#F2F7FF" if kind == "pred" else "#EFFAF6",
    )

    if kind == "pred":
        points = [
            (0, -15),
            (11, -11),
            (15, 0),
            (11, 11),
            (0, 15),
            (-11, 11),
            (-15, 0),
            (-11, -11),
        ]

        for dx, dy in points:
            draw.ellipse(
                (
                    cx + dx - 3,
                    cy + dy - 3,
                    cx + dx + 3,
                    cy + dy + 3,
                ),
                fill=color,
            )
    else:
        polygon = [
            (cx, cy - 17),
            (cx - 13, cy + 5),
            (cx - 9, cy + 15),
            (cx, cy + 20),
            (cx + 9, cy + 15),
            (cx + 13, cy + 5),
        ]
        draw.polygon(polygon, fill=color)


# ============================================================
# FINAL MANAGEMENT PNG
# ============================================================

def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    machine_summary, overall = _build_machine_summary(data)

    width = 2048
    margin = 38

    header_h = 198
    table_gap = 34

    group_header_h = 56
    sub_header_h = 54

    columns = [
        ("EDITION DATE", 150),
        ("MACHINE", 185),
        ("MACHINE\nIN-CHARGE", 205),
        ("PUBLICATION", 135),
        ("PO", 130),
        ("PRED QTY", 130),
        ("PRED %", 112),
        ("ACT QTY", 130),
        ("ACT %", 112),
        ("EXTRA WASTE\n(Qty)", 125),
        ("REASON FOR EXTRA WASTE", 568),
    ]

    widths = [item[1] for item in columns]

    # Long reasons increase row height automatically.
    row_heights = []
    wrapped_reasons = []

    for _, row in data.iterrows():
        reason = _safe_reason(row.get("Reason for Extra Waste", "NA"))

        lines = textwrap.wrap(
            reason,
            width=59,
            break_long_words=False,
            break_on_hyphens=False,
        ) or ["NA"]

        wrapped_reasons.append("\n".join(lines))

        row_heights.append(
            max(
                92,
                34 + len(lines) * 24,
            )
        )

    summary_top_gap = 48
    summary_h = 258
    bottom_pad = 42

    table_top = header_h + table_gap

    height = (
        table_top
        + group_header_h
        + sub_header_h
        + sum(row_heights)
        + summary_top_gap
        + summary_h
        + bottom_pad
    )

    image = Image.new(
        "RGB",
        (width, height),
        WHITE,
    )

    draw = ImageDraw.Draw(image)

    # ========================================================
    # HEADER
    # ========================================================

    draw.rounded_rectangle(
        (0, 0, width, header_h),
        radius=28,
        fill=NAVY,
    )

    _text(
        draw,
        (48, 56),
        "PIQ",
        58,
        True,
        WHITE,
    )

    _text(
        draw,
        (177, 79),
        "PressIQ Analytics",
        23,
        True,
        "#E2E8F0",
    )

    _text(
        draw,
        (width // 2, 54),
        "Actual vs Predicted Waste Report",
        43,
        True,
        WHITE,
        "ma",
    )

    issue_date = "—"

    if (
        "Edition Date" in data.columns
        and data["Edition Date"].notna().any()
    ):
        issue_date = pd.to_datetime(
            data["Edition Date"].dropna().iloc[0]
        ).strftime("%d %B %Y")

    production_label = (
        "MAIN SHIFT"
        if str(report_type).strip().upper() == "MAIN"
        else "SUPPLEMENT"
    )

    pill_w = 405
    pill_h = 54
    pill_x1 = width // 2 - pill_w // 2
    pill_y1 = 112

    draw.rounded_rectangle(
        (
            pill_x1,
            pill_y1,
            pill_x1 + pill_w,
            pill_y1 + pill_h,
        ),
        radius=27,
        fill="#0B2858",
        outline="#315C95",
        width=2,
    )

    _text(
        draw,
        (
            width // 2,
            pill_y1 + pill_h / 2,
        ),
        f"{production_label}    {issue_date}",
        20,
        True,
        "#EAF2FF",
        "mm",
    )

    predicted_total = overall["Predicted %"]
    actual_total = overall["Actual %"]

    within_target = (
        predicted_total is not None
        and actual_total is not None
        and actual_total <= predicted_total
    )

    status = "WITHIN TARGET" if within_target else "ABOVE TARGET"
    status_color = "#35D39A" if within_target else "#FB7185"

    sx1 = width - 510
    sy1 = 25
    sx2 = width - 40
    sy2 = 171

    draw.rounded_rectangle(
        (sx1, sy1, sx2, sy2),
        radius=20,
        fill="#071B40",
        outline="#1B665B" if within_target else "#71334B",
        width=2,
    )

    _draw_status_icon(
        draw,
        (sx1 + 73, sy1 + 74),
        within_target,
    )

    _text(
        draw,
        (sx1 + 135, sy1 + 30),
        "PERFORMANCE STATUS",
        16,
        True,
        "#CBD5E1",
    )

    _text(
        draw,
        (sx1 + 135, sy1 + 65),
        status,
        28,
        True,
        status_color,
    )

    if predicted_total is not None and actual_total is not None:
        comparison = "≤" if within_target else ">"

        _text(
            draw,
            (sx1 + 135, sy1 + 112),
            (
                f"Actual {actual_total:.2f}% "
                f"{comparison} Predicted {predicted_total:.2f}%"
            ),
            17,
            False,
            WHITE,
        )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    y = table_top

    fixed_indexes = [0, 1, 2, 3, 4, 9, 10]

    for index in fixed_indexes:
        left = margin + sum(widths[:index])
        col_w = widths[index]

        draw.rectangle(
            (
                left,
                y,
                left + col_w,
                y + group_header_h + sub_header_h,
            ),
            fill=NAVY_2,
            outline="#496A98",
            width=1,
        )

        _center(
            draw,
            (
                left,
                y,
                left + col_w,
                y + group_header_h + sub_header_h,
            ),
            columns[index][0],
            15,
            True,
            WHITE,
        )

    pred_left = margin + sum(widths[:5])
    pred_width = widths[5] + widths[6]

    draw.rectangle(
        (
            pred_left,
            y,
            pred_left + pred_width,
            y + group_header_h,
        ),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )

    _text(
        draw,
        (
            pred_left + pred_width / 2,
            y + group_header_h / 2,
        ),
        "PREDICTED WASTE",
        16,
        True,
        WHITE,
        "mm",
    )

    actual_left = margin + sum(widths[:7])
    actual_width = widths[7] + widths[8]

    draw.rectangle(
        (
            actual_left,
            y,
            actual_left + actual_width,
            y + group_header_h,
        ),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )

    _text(
        draw,
        (
            actual_left + actual_width / 2,
            y + group_header_h / 2,
        ),
        "ACTUAL WASTE",
        16,
        True,
        WHITE,
        "mm",
    )

    for index, label in [
        (5, "Qty"),
        (6, "%"),
        (7, "Qty"),
        (8, "%"),
    ]:
        left = margin + sum(widths[:index])
        col_w = widths[index]

        draw.rectangle(
            (
                left,
                y + group_header_h,
                left + col_w,
                y + group_header_h + sub_header_h,
            ),
            fill=NAVY_2,
            outline="#496A98",
            width=1,
        )

        _text(
            draw,
            (
                left + col_w / 2,
                y + group_header_h + sub_header_h / 2,
            ),
            label,
            15,
            True,
            WHITE,
            "mm",
        )

    y += group_header_h + sub_header_h

    # ========================================================
    # DATA ROWS
    # ========================================================

    for row_number, (_, row) in enumerate(data.iterrows()):
        row_h = row_heights[row_number]
        fill = WHITE if row_number % 2 == 0 else ALT

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
            wrapped_reasons[row_number],
        ]

        x = margin

        for column_index, ((_, col_w), value) in enumerate(
            zip(columns, values)
        ):
            draw.rectangle(
                (
                    x,
                    y,
                    x + col_w,
                    y + row_h,
                ),
                fill=fill,
                outline=GRID,
                width=1,
            )

            color = TEXT
            bold = column_index in {5, 6, 7, 8, 9}

            if column_index == 6:
                color = BLUE_VALUE

            if (
                column_index == 8
                and pd.notna(row.get("Predicted %"))
                and pd.notna(row.get("Actual %"))
                and float(row["Actual %"]) > float(row["Predicted %"])
            ):
                color = RED

            if (
                column_index == 9
                and pd.notna(row.get("Extra Waste"))
                and float(row["Extra Waste"]) > 0
            ):
                color = RED

            if column_index == 10:
                _left(
                    draw,
                    (
                        x,
                        y,
                        x + col_w,
                        y + row_h,
                    ),
                    value,
                    15,
                    False,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (
                        x,
                        y,
                        x + col_w,
                        y + row_h,
                    ),
                    value,
                    15,
                    bold,
                    color,
                )

            x += col_w

        y += row_h

    # ========================================================
    # PREDICTED / ACTUAL SUMMARY
    # ========================================================

    y += summary_top_gap

    summary_gap = 28
    summary_width = (
        width
        - 2 * margin
        - summary_gap
    ) // 2

    def draw_summary(left, title, kind):
        card_bottom = y + summary_h

        draw.rounded_rectangle(
            (
                left,
                y,
                left + summary_width,
                card_bottom,
            ),
            radius=20,
            fill=WHITE,
            outline=GRID,
            width=2,
        )

        draw.rounded_rectangle(
            (
                left,
                y,
                left + summary_width,
                y + 62,
            ),
            radius=20,
            fill=NAVY_2,
        )

        draw.rectangle(
            (
                left,
                y + 38,
                left + summary_width,
                y + 62,
            ),
            fill=NAVY_2,
        )

        _text(
            draw,
            (left + 28, y + 32),
            title,
            18,
            True,
            WHITE,
            "lm",
        )

        total_card_w = 190
        total_margin = 24
        metrics_left = left + 20
        metrics_right = left + summary_width - total_card_w - total_margin - 12
        metrics_width = metrics_right - metrics_left

        metric_count = len(machine_summary)
        metric_width = metrics_width / max(metric_count, 1)

        for index, machine in enumerate(machine_summary):
            cx = (
                metrics_left
                + metric_width * index
                + metric_width / 2
            )

            _draw_summary_icon(
                draw,
                (cx, y + 111),
                kind,
                BLUE_VALUE if kind == "pred" else GREEN_VALUE,
            )

            label = machine["Label"]

            if label == "PRESS-4 / COL B":
                label_text = "PRESS-4 /\nCOL B %"
            else:
                label_text = f"{label} %"

            _center(
                draw,
                (
                    cx - metric_width / 2,
                    y + 142,
                    cx + metric_width / 2,
                    y + 188,
                ),
                label_text,
                14,
                True,
                TEXT,
            )

            value = (
                machine["Predicted %"]
                if kind == "pred"
                else machine["Actual %"]
            )

            _text(
                draw,
                (cx, y + 218),
                "—" if value is None else f"{value:.2f}%",
                27,
                True,
                BLUE_VALUE if kind == "pred" else GREEN_VALUE,
                "ma",
            )

        total_x2 = left + summary_width - total_margin
        total_x1 = total_x2 - total_card_w
        total_y1 = y + 84
        total_y2 = y + 232

        draw.rounded_rectangle(
            (
                total_x1,
                total_y1,
                total_x2,
                total_y2,
            ),
            radius=16,
            fill=NAVY if kind == "pred" else "#075F46",
        )

        _text(
            draw,
            (
                (total_x1 + total_x2) / 2,
                total_y1 + 38,
            ),
            "TOTAL PREDICT" if kind == "pred" else "TOTAL ACTUAL",
            14,
            True,
            WHITE,
            "ma",
        )

        total_value = (
            overall["Predicted %"]
            if kind == "pred"
            else overall["Actual %"]
        )

        _text(
            draw,
            (
                (total_x1 + total_x2) / 2,
                total_y1 + 98,
            ),
            "—" if total_value is None else f"{total_value:.2f}%",
            34,
            True,
            WHITE,
            "ma",
        )

    draw_summary(
        margin,
        "PREDICTED SUMMARY",
        "pred",
    )

    draw_summary(
        margin + summary_width + summary_gap,
        "ACTUAL SUMMARY",
        "act",
    )

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output.getvalue()
