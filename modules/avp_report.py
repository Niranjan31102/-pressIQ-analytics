from io import BytesIO
import textwrap

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# FINAL APPROVED MANAGEMENT REPORT DESIGN
# ============================================================

NAVY = "#061A3F"
NAVY_2 = "#0B2F63"
BLUE = "#1E6AE1"
GREEN = "#0C7A58"
RED = "#E53935"
TEXT = "#111827"
MUTED = "#64748B"
GRID = "#DDE5F0"
ALT = "#FAFBFD"
WHITE = "#FFFFFF"


# ============================================================
# FONT HELPERS
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
    font = _font(size, bold)
    value = str(value)

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


def _left(draw, box, value, size=18, bold=False, fill=TEXT, spacing=5):
    x1, y1, x2, y2 = box
    font = _font(size, bold)
    value = str(value)

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
            y1 + max(10, ((y2 - y1) - th) / 2),
        ),
        value,
        font=font,
        fill=fill,
        spacing=spacing,
    )


# ============================================================
# DATA HELPERS
# ============================================================

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

    order = [
        "CROMO",
        "COL A",
        "COL B",
        "PRESS-4 / COL B",
    ]

    machines = []

    for bucket in order:
        group = work[work["_bucket"] == bucket]

        if group.empty:
            continue

        po = pd.to_numeric(
            group["PO"],
            errors="coerce",
        ).fillna(0).sum()

        predicted = pd.to_numeric(
            group["Predicted Waste"],
            errors="coerce",
        ).sum(min_count=1)

        actual = pd.to_numeric(
            group["Actual Waste"],
            errors="coerce",
        ).fillna(0).sum()

        machines.append(
            {
                "name": bucket,
                "predicted": (
                    round(predicted / po * 100, 2)
                    if po and pd.notna(predicted)
                    else None
                ),
                "actual": (
                    round(actual / po * 100, 2)
                    if po
                    else None
                ),
            }
        )

    total_po = pd.to_numeric(
        work["PO"],
        errors="coerce",
    ).fillna(0).sum()

    total_predicted = pd.to_numeric(
        work["Predicted Waste"],
        errors="coerce",
    ).sum(min_count=1)

    total_actual = pd.to_numeric(
        work["Actual Waste"],
        errors="coerce",
    ).fillna(0).sum()

    overall = {
        "predicted": (
            round(total_predicted / total_po * 100, 2)
            if total_po and pd.notna(total_predicted)
            else None
        ),
        "actual": (
            round(total_actual / total_po * 100, 2)
            if total_po
            else None
        ),
    }

    return machines, overall


# ============================================================
# DECORATIVE ICONS
# ============================================================

def _draw_status_icon(draw, center, good):
    cx, cy = center
    color = "#2DD39A" if good else "#FB7185"

    draw.ellipse(
        (cx - 32, cy - 32, cx + 32, cy + 32),
        outline=color,
        width=5,
    )

    if good:
        draw.line(
            (cx - 15, cy, cx - 3, cy + 12),
            fill=color,
            width=6,
        )
        draw.line(
            (cx - 3, cy + 12, cx + 19, cy - 14),
            fill=color,
            width=6,
        )
    else:
        draw.line(
            (cx - 14, cy - 14, cx + 14, cy + 14),
            fill=color,
            width=5,
        )
        draw.line(
            (cx + 14, cy - 14, cx - 14, cy + 14),
            fill=color,
            width=5,
        )


def _draw_pred_icon(draw, cx, cy):
    draw.ellipse(
        (cx - 25, cy - 25, cx + 25, cy + 25),
        fill="#EFF6FF",
    )

    for dx, dy in [
        (0, -14),
        (10, -10),
        (14, 0),
        (10, 10),
        (0, 14),
        (-10, 10),
        (-14, 0),
        (-10, -10),
    ]:
        draw.ellipse(
            (
                cx + dx - 3,
                cy + dy - 3,
                cx + dx + 3,
                cy + dy + 3,
            ),
            fill=BLUE,
        )


def _draw_actual_icon(draw, cx, cy):
    draw.ellipse(
        (cx - 25, cy - 25, cx + 25, cy + 25),
        fill="#ECFDF5",
    )

    draw.polygon(
        [
            (cx, cy - 17),
            (cx - 12, cy + 5),
            (cx - 8, cy + 14),
            (cx, cy + 19),
            (cx + 8, cy + 14),
            (cx + 12, cy + 5),
        ],
        fill=GREEN,
    )


# ============================================================
# FINAL REPORT
# ============================================================

def generate_management_png(df, report_type):
    data = finalize_calculations(df).reset_index(drop=True)
    machines, overall = _build_summary(data)

    # ========================================================
    # CANVAS - APPROVED MANAGEMENT PROPORTIONS
    # ========================================================

    W = 1600
    M = 30

    HEADER_H = 155
    TABLE_GAP = 30
    GROUP_H = 42
    SUB_H = 40

    # Intentionally close to the approved reference.
    columns = [
        ("EDITION DATE", 115),
        ("MACHINE", 125),
        ("MACHINE\nIN-CHARGE", 145),
        ("PUBLICATION", 100),
        ("PO", 90),
        ("PRED QTY", 90),
        ("PRED %", 80),
        ("ACT QTY", 90),
        ("ACT %", 80),
        ("EXTRA WASTE\n(Qty)", 95),
        ("REASON FOR EXTRA WASTE", 530),
    ]

    widths = [width for _, width in columns]

    wrapped_reasons = []
    row_heights = []

    for _, row in data.iterrows():
        reason = _safe_reason(
            row.get(
                "Reason for Extra Waste",
                "NA",
            )
        )

        lines = textwrap.wrap(
            reason,
            width=55,
            break_long_words=False,
            break_on_hyphens=False,
        ) or ["NA"]

        wrapped_reasons.append(
            "\n".join(lines)
        )

        # Approved design uses compact rows.
        # Expand only for genuinely long reasons.
        if len(lines) == 1:
            row_height = 68
        elif len(lines) == 2:
            row_height = 78
        else:
            row_height = 28 + len(lines) * 22

        row_heights.append(
            row_height
        )

    SUMMARY_GAP = 34
    SUMMARY_H = 205
    BOTTOM = 30

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

    image = Image.new(
        "RGB",
        (W, H),
        WHITE,
    )

    draw = ImageDraw.Draw(
        image
    )

    # ========================================================
    # HEADER
    # ========================================================

    draw.rounded_rectangle(
        (0, 0, W, HEADER_H),
        radius=22,
        fill=NAVY,
    )

    # Brand area
    _text(
        draw,
        (36, 42),
        "PIQ",
        48,
        True,
        WHITE,
    )

    _text(
        draw,
        (132, 61),
        "PressIQ Analytics",
        18,
        True,
        "#E2E8F0",
    )

    # Main title
    _text(
        draw,
        (W // 2, 40),
        "Actual vs Predicted Waste Report",
        34,
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

    type_label = (
        "MAIN SHIFT"
        if str(report_type).strip().upper() == "MAIN"
        else "SUPPLEMENT"
    )

    # Date/shift pill
    pill_w = 300
    pill_h = 40
    pill_x1 = W // 2 - pill_w // 2
    pill_y1 = 95

    draw.rounded_rectangle(
        (
            pill_x1,
            pill_y1,
            pill_x1 + pill_w,
            pill_y1 + pill_h,
        ),
        radius=20,
        fill="#0B2858",
        outline="#315C95",
        width=2,
    )

    _text(
        draw,
        (
            W // 2,
            pill_y1 + pill_h / 2,
        ),
        f"{type_label}   {issue_date}",
        15,
        True,
        "#EEF5FF",
        "mm",
    )

    predicted_total = overall["predicted"]
    actual_total = overall["actual"]

    within_target = (
        predicted_total is not None
        and actual_total is not None
        and actual_total <= predicted_total
    )

    status = (
        "WITHIN TARGET"
        if within_target
        else "ABOVE TARGET"
    )

    status_color = (
        "#34D399"
        if within_target
        else "#FB7185"
    )

    status_x1 = W - 365
    status_y1 = 18
    status_x2 = W - 24
    status_y2 = 136

    draw.rounded_rectangle(
        (
            status_x1,
            status_y1,
            status_x2,
            status_y2,
        ),
        radius=17,
        fill="#071B40",
        outline="#1C665C" if within_target else "#76334B",
        width=2,
    )

    _draw_status_icon(
        draw,
        (
            status_x1 + 56,
            status_y1 + 58,
        ),
        within_target,
    )

    _text(
        draw,
        (
            status_x1 + 106,
            status_y1 + 22,
        ),
        "PERFORMANCE STATUS",
        12,
        True,
        "#CBD5E1",
    )

    _text(
        draw,
        (
            status_x1 + 106,
            status_y1 + 49,
        ),
        status,
        21,
        True,
        status_color,
    )

    if (
        predicted_total is not None
        and actual_total is not None
    ):
        symbol = (
            "≤"
            if within_target
            else ">"
        )

        _text(
            draw,
            (
                status_x1 + 106,
                status_y1 + 87,
            ),
            (
                f"Actual {actual_total:.2f}% "
                f"{symbol} Predicted {predicted_total:.2f}%"
            ),
            13,
            False,
            WHITE,
        )

    # ========================================================
    # TABLE HEADER
    # ========================================================

    y = table_top

    fixed_columns = [
        0,
        1,
        2,
        3,
        4,
        9,
        10,
    ]

    for index in fixed_columns:
        left = (
            M
            + sum(
                widths[:index]
            )
        )

        width = widths[index]

        draw.rectangle(
            (
                left,
                y,
                left + width,
                y + GROUP_H + SUB_H,
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
                left + width,
                y + GROUP_H + SUB_H,
            ),
            columns[index][0],
            12,
            True,
            WHITE,
        )

    # Predicted group
    pred_left = (
        M
        + sum(
            widths[:5]
        )
    )

    pred_width = (
        widths[5]
        + widths[6]
    )

    draw.rectangle(
        (
            pred_left,
            y,
            pred_left + pred_width,
            y + GROUP_H,
        ),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )

    _text(
        draw,
        (
            pred_left + pred_width / 2,
            y + GROUP_H / 2,
        ),
        "PREDICTED WASTE",
        12,
        True,
        WHITE,
        "mm",
    )

    # Actual group
    actual_left = (
        M
        + sum(
            widths[:7]
        )
    )

    actual_width = (
        widths[7]
        + widths[8]
    )

    draw.rectangle(
        (
            actual_left,
            y,
            actual_left + actual_width,
            y + GROUP_H,
        ),
        fill=NAVY_2,
        outline="#496A98",
        width=1,
    )

    _text(
        draw,
        (
            actual_left + actual_width / 2,
            y + GROUP_H / 2,
        ),
        "ACTUAL WASTE",
        12,
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
        left = (
            M
            + sum(
                widths[:index]
            )
        )

        width = widths[index]

        draw.rectangle(
            (
                left,
                y + GROUP_H,
                left + width,
                y + GROUP_H + SUB_H,
            ),
            fill=NAVY_2,
            outline="#496A98",
            width=1,
        )

        _text(
            draw,
            (
                left + width / 2,
                y + GROUP_H + SUB_H / 2,
            ),
            label,
            12,
            True,
            WHITE,
            "mm",
        )

    y += (
        GROUP_H
        + SUB_H
    )

    # ========================================================
    # TABLE ROWS
    # ========================================================

    for row_index, (_, row) in enumerate(
        data.iterrows()
    ):
        row_height = row_heights[
            row_index
        ]

        fill = (
            WHITE
            if row_index % 2 == 0
            else ALT
        )

        edition_date = (
            pd.to_datetime(
                row["Edition Date"]
            ).strftime(
                "%d/%m/%Y"
            )
            if pd.notna(
                row["Edition Date"]
            )
            else "—"
        )

        values = [
            edition_date,
            row.get(
                "Machine",
                "—",
            ),
            row.get(
                "Machine In-charge",
                "—",
            ),
            row.get(
                "Publication",
                "—",
            ),
            _fmt_int(
                row.get(
                    "PO"
                )
            ),
            _fmt_int(
                row.get(
                    "Predicted Waste"
                )
            ),
            _fmt_pct(
                row.get(
                    "Predicted %"
                )
            ),
            _fmt_int(
                row.get(
                    "Actual Waste"
                )
            ),
            _fmt_pct(
                row.get(
                    "Actual %"
                )
            ),
            _fmt_int(
                row.get(
                    "Extra Waste"
                )
            ),
            wrapped_reasons[
                row_index
            ],
        ]

        x = M

        for column_index, (
            (_, column_width),
            value,
        ) in enumerate(
            zip(
                columns,
                values,
            )
        ):
            draw.rectangle(
                (
                    x,
                    y,
                    x + column_width,
                    y + row_height,
                ),
                fill=fill,
                outline=GRID,
                width=1,
            )

            color = TEXT

            bold = (
                column_index
                in {
                    5,
                    6,
                    7,
                    8,
                    9,
                }
            )

            if column_index == 6:
                color = BLUE

            if (
                column_index == 8
                and pd.notna(
                    row.get(
                        "Predicted %"
                    )
                )
                and pd.notna(
                    row.get(
                        "Actual %"
                    )
                )
                and float(
                    row["Actual %"]
                )
                > float(
                    row[
                        "Predicted %"
                    ]
                )
            ):
                color = RED

            if (
                column_index == 9
                and pd.notna(
                    row.get(
                        "Extra Waste"
                    )
                )
                and float(
                    row[
                        "Extra Waste"
                    ]
                )
                > 0
            ):
                color = RED

            if column_index == 10:
                _left(
                    draw,
                    (
                        x,
                        y,
                        x + column_width,
                        y + row_height,
                    ),
                    value,
                    12,
                    False,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (
                        x,
                        y,
                        x + column_width,
                        y + row_height,
                    ),
                    value,
                    12,
                    bold,
                    color,
                )

            x += (
                column_width
            )

        y += (
            row_height
        )

    # ========================================================
    # SUMMARY CARDS
    # ========================================================

    y += SUMMARY_GAP

    summary_gap = 22

    card_width = (
        W
        - 2 * M
        - summary_gap
    ) // 2

    def draw_summary_card(
        left,
        title,
        kind,
    ):
        bottom = (
            y
            + SUMMARY_H
        )

        draw.rounded_rectangle(
            (
                left,
                y,
                left + card_width,
                bottom,
            ),
            radius=18,
            fill=WHITE,
            outline=GRID,
            width=2,
        )

        draw.rounded_rectangle(
            (
                left,
                y,
                left + card_width,
                y + 48,
            ),
            radius=18,
            fill=NAVY_2,
        )

        draw.rectangle(
            (
                left,
                y + 29,
                left + card_width,
                y + 48,
            ),
            fill=NAVY_2,
        )

        _text(
            draw,
            (
                left + 20,
                y + 24,
            ),
            title,
            14,
            True,
            WHITE,
            "lm",
        )

        total_width = 150

        total_right = (
            left
            + card_width
            - 18
        )

        total_left = (
            total_right
            - total_width
        )

        metric_left = (
            left
            + 12
        )

        metric_right = (
            total_left
            - 12
        )

        metric_area = (
            metric_right
            - metric_left
        )

        machine_count = max(
            1,
            len(
                machines
            ),
        )

        metric_width = (
            metric_area
            / machine_count
        )

        for index, machine in enumerate(
            machines
        ):
            center_x = (
                metric_left
                + metric_width * index
                + metric_width / 2
            )

            if kind == "pred":
                _draw_pred_icon(
                    draw,
                    center_x,
                    y + 88,
                )
            else:
                _draw_actual_icon(
                    draw,
                    center_x,
                    y + 88,
                )

            label = machine[
                "name"
            ]

            if label == "PRESS-4 / COL B":
                label_text = (
                    "PRESS-4 /\n"
                    "COL B %"
                )
            else:
                label_text = (
                    f"{label} %"
                )

            _center(
                draw,
                (
                    center_x
                    - metric_width / 2,
                    y + 114,
                    center_x
                    + metric_width / 2,
                    y + 150,
                ),
                label_text,
                11,
                True,
                TEXT,
            )

            value = (
                machine[
                    "predicted"
                ]
                if kind == "pred"
                else machine[
                    "actual"
                ]
            )

            _text(
                draw,
                (
                    center_x,
                    y + 177,
                ),
                (
                    "—"
                    if value is None
                    else f"{value:.2f}%"
                ),
                20,
                True,
                BLUE
                if kind == "pred"
                else GREEN,
                "ma",
            )

        total_top = (
            y
            + 68
        )

        total_bottom = (
            y
            + 187
        )

        draw.rounded_rectangle(
            (
                total_left,
                total_top,
                total_right,
                total_bottom,
            ),
            radius=14,
            fill=(
                NAVY
                if kind == "pred"
                else "#075F46"
            ),
        )

        _text(
            draw,
            (
                (
                    total_left
                    + total_right
                )
                / 2,
                total_top + 30,
            ),
            (
                "TOTAL PREDICT"
                if kind == "pred"
                else "TOTAL ACTUAL"
            ),
            11,
            True,
            WHITE,
            "ma",
        )

        total_value = (
            overall[
                "predicted"
            ]
            if kind == "pred"
            else overall[
                "actual"
            ]
        )

        _text(
            draw,
            (
                (
                    total_left
                    + total_right
                )
                / 2,
                total_top + 79,
            ),
            (
                "—"
                if total_value is None
                else f"{total_value:.2f}%"
            ),
            27,
            True,
            WHITE,
            "ma",
        )

    draw_summary_card(
        M,
        "PREDICTED SUMMARY",
        "pred",
    )

    draw_summary_card(
        M
        + card_width
        + summary_gap,
        "ACTUAL SUMMARY",
        "actual",
    )

    # ========================================================
    # EXPORT
    # ========================================================

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output.getvalue()
