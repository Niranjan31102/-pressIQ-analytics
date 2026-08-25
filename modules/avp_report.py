from io import BytesIO

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# FINAL MANAGEMENT REPORT
# Frozen design:
# PIQ / PressIQ -> Report title/date -> Main table
# -> Predicted Summary -> Actual Summary
#
# Priority:
# LARGE readable text, bold numbers, clean reason wrapping,
# separate Press-4 / Colorman-B summary without double counting.
# ============================================================

NAVY = "#061A3F"
NAVY_2 = "#0A2E63"
BLUE = "#1565D8"
GREEN = "#087A57"
RED = "#E53935"
TEXT = "#0F172A"
GRID = "#D9E2EC"
ROW_ALT = "#F8FAFC"
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


def _draw_text(
    draw,
    xy,
    value,
    size,
    bold=False,
    fill=TEXT,
    anchor=None,
):
    draw.text(
        xy,
        str(value),
        font=_font(size, bold),
        fill=fill,
        anchor=anchor,
    )


def _draw_centered(
    draw,
    box,
    value,
    size,
    bold=False,
    fill=TEXT,
    spacing=4,
):
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

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    x = x1 + ((x2 - x1) - width) / 2
    y = y1 + ((y2 - y1) - height) / 2

    draw.multiline_text(
        (x, y),
        text,
        font=font,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def _draw_left(
    draw,
    box,
    value,
    size,
    bold=False,
    fill=TEXT,
    spacing=5,
):
    x1, y1, x2, y2 = box

    text = str(value)
    font = _font(size, bold)

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=spacing,
    )

    text_height = bbox[3] - bbox[1]

    draw.multiline_text(
        (
            x1 + 12,
            y1 + max(8, ((y2 - y1) - text_height) / 2),
        ),
        text,
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


def _format_integer(value):
    if pd.isna(value):
        return "—"

    return f"{int(round(float(value))):,}"


def _format_percent(value):
    if pd.isna(value):
        return "—"

    return f"{float(value):.2f}%"


def _wrap_by_pixels(
    draw,
    text,
    max_width,
    font,
):
    words = str(text).split()

    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"

        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)

    return lines


# ============================================================
# MACHINE SUMMARY
# ============================================================

def _machine_bucket(row):
    display_machine = str(
        row.get("Machine", "")
    ).upper().strip()

    calc_machine = str(
        row.get("Calc Machine", "")
    ).upper().strip()

    # Press-4 is physically Colorman-B but must be
    # presented independently and excluded from regular COL B.
    if (
        "PRESS-4" in display_machine
        or "PRESS 4" in display_machine
    ):
        return "PRESS-4 / COL B"

    if (
        display_machine == "CROMOMAN-C"
        or calc_machine == "CROMOMAN-C"
    ):
        return "CROMO"

    if (
        display_machine == "COLORMAN-A"
        or calc_machine == "COLORMAN-A"
    ):
        return "COL A"

    if (
        display_machine == "COLORMAN-B"
        or calc_machine == "COLORMAN-B"
    ):
        return "COL B"

    return display_machine or calc_machine or "OTHER"


def _build_machine_summary(data):
    working = data.copy()

    working["_summary_machine"] = working.apply(
        _machine_bucket,
        axis=1,
    )

    machine_order = [
        "CROMO",
        "COL A",
        "COL B",
        "PRESS-4 / COL B",
    ]

    machine_rows = []

    for machine_name in machine_order:
        group = working[
            working["_summary_machine"] == machine_name
        ]

        if group.empty:
            continue

        total_po = pd.to_numeric(
            group["PO"],
            errors="coerce",
        ).fillna(0).sum()

        total_predicted = pd.to_numeric(
            group["Predicted Waste"],
            errors="coerce",
        ).sum(min_count=1)

        total_actual = pd.to_numeric(
            group["Actual Waste"],
            errors="coerce",
        ).fillna(0).sum()

        predicted_percent = (
            round(
                total_predicted / total_po * 100,
                2,
            )
            if total_po and pd.notna(total_predicted)
            else None
        )

        actual_percent = (
            round(
                total_actual / total_po * 100,
                2,
            )
            if total_po
            else None
        )

        machine_rows.append(
            {
                "name": machine_name,
                "predicted": predicted_percent,
                "actual": actual_percent,
            }
        )

    total_po = pd.to_numeric(
        working["PO"],
        errors="coerce",
    ).fillna(0).sum()

    total_predicted = pd.to_numeric(
        working["Predicted Waste"],
        errors="coerce",
    ).sum(min_count=1)

    total_actual = pd.to_numeric(
        working["Actual Waste"],
        errors="coerce",
    ).fillna(0).sum()

    overall = {
        "predicted": (
            round(
                total_predicted / total_po * 100,
                2,
            )
            if total_po and pd.notna(total_predicted)
            else None
        ),
        "actual": (
            round(
                total_actual / total_po * 100,
                2,
            )
            if total_po
            else None
        ),
    }

    return machine_rows, overall


# ============================================================
# FINAL PNG GENERATOR
# ============================================================

def generate_management_png(df, report_type):
    data = finalize_calculations(
        df
    ).reset_index(drop=True)

    machine_summary, overall = _build_machine_summary(
        data
    )

    # --------------------------------------------------------
    # FIXED DESIGN DIMENSIONS
    # --------------------------------------------------------
    #
    # The report is intentionally designed around the size
    # Streamlit actually displays, instead of creating a very
    # large canvas that gets scaled down and makes text tiny.
    #
    # --------------------------------------------------------

    WIDTH = 1280
    MARGIN = 18

    HEADER_HEIGHT = 116
    TABLE_GAP = 18

    GROUP_HEADER_HEIGHT = 48
    SUB_HEADER_HEIGHT = 42

    # Total width = 1244
    # 1244 + 18 + 18 = 1280
    columns = [
        ("EDITION DATE", 92),
        ("MACHINE", 104),
        ("MACHINE\nIN-CHARGE", 116),
        ("PUBLICATION", 82),
        ("PO", 74),
        ("PRED QTY", 76),
        ("PRED %", 68),
        ("ACT QTY", 76),
        ("ACT %", 68),
        ("EXTRA\nWASTE", 78),
        ("REASON FOR EXTRA WASTE", 410),
    ]

    widths = [
        width
        for _, width in columns
    ]

    # --------------------------------------------------------
    # PIXEL-BASED REASON WRAPPING
    # --------------------------------------------------------

    dummy_image = Image.new(
        "RGB",
        (WIDTH, 100),
        WHITE,
    )

    dummy_draw = ImageDraw.Draw(
        dummy_image
    )

    REASON_FONT_SIZE = 17
    reason_font = _font(
        REASON_FONT_SIZE,
        True,
    )

    reason_inner_width = (
        columns[-1][1]
        - 24
    )

    wrapped_reasons = []
    row_heights = []

    for _, row in data.iterrows():
        reason = _safe_reason(
            row.get(
                "Reason for Extra Waste",
                "NA",
            )
        )

        lines = _wrap_by_pixels(
            dummy_draw,
            reason,
            reason_inner_width,
            reason_font,
        )

        wrapped_reasons.append(
            "\n".join(lines)
        )

        # Compact when short, expand like Excel when needed.
        if len(lines) == 1:
            row_height = 68
        elif len(lines) == 2:
            row_height = 80
        elif len(lines) == 3:
            row_height = 94
        else:
            row_height = (
                28
                + len(lines) * 23
            )

        row_heights.append(
            row_height
        )

    SUMMARY_GAP = 28
    SUMMARY_HEIGHT = 194
    BOTTOM_PADDING = 20

    table_top = (
        HEADER_HEIGHT
        + TABLE_GAP
    )

    HEIGHT = (
        table_top
        + GROUP_HEADER_HEIGHT
        + SUB_HEADER_HEIGHT
        + sum(row_heights)
        + SUMMARY_GAP
        + SUMMARY_HEIGHT
        + BOTTOM_PADDING
    )

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        WHITE,
    )

    draw = ImageDraw.Draw(
        image
    )

    # ========================================================
    # HEADER
    # ========================================================

    draw.rounded_rectangle(
        (
            0,
            0,
            WIDTH,
            HEADER_HEIGHT,
        ),
        radius=18,
        fill=NAVY,
    )

    _draw_text(
        draw,
        (24, 29),
        "PIQ",
        42,
        True,
        WHITE,
    )

    _draw_text(
        draw,
        (110, 49),
        "PressIQ",
        22,
        True,
        "#E2E8F0",
    )

    _draw_text(
        draw,
        (
            WIDTH // 2,
            30,
        ),
        "Actual vs Predicted Waste Report",
        32,
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
        ).strftime(
            "%d %B %Y"
        )

    production_label = (
        "MAIN SHIFT"
        if str(report_type).strip().upper() == "MAIN"
        else "SUPPLEMENT"
    )

    _draw_text(
        draw,
        (
            WIDTH // 2,
            78,
        ),
        f"{production_label}  •  {issue_date}",
        17,
        True,
        "#DCEAFF",
        "ma",
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
            MARGIN
            + sum(
                widths[:index]
            )
        )

        column_width = widths[index]

        draw.rectangle(
            (
                left,
                y,
                left + column_width,
                y
                + GROUP_HEADER_HEIGHT
                + SUB_HEADER_HEIGHT,
            ),
            fill=NAVY_2,
            outline="#5476A5",
            width=1,
        )

        _draw_centered(
            draw,
            (
                left,
                y,
                left + column_width,
                y
                + GROUP_HEADER_HEIGHT
                + SUB_HEADER_HEIGHT,
            ),
            columns[index][0],
            15,
            True,
            WHITE,
        )

    # Predicted group
    predicted_left = (
        MARGIN
        + sum(
            widths[:5]
        )
    )

    predicted_width = (
        widths[5]
        + widths[6]
    )

    draw.rectangle(
        (
            predicted_left,
            y,
            predicted_left + predicted_width,
            y + GROUP_HEADER_HEIGHT,
        ),
        fill=NAVY_2,
        outline="#5476A5",
        width=1,
    )

    _draw_text(
        draw,
        (
            predicted_left + predicted_width / 2,
            y + GROUP_HEADER_HEIGHT / 2,
        ),
        "PREDICTED WASTE",
        15,
        True,
        WHITE,
        "mm",
    )

    # Actual group
    actual_left = (
        MARGIN
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
            y + GROUP_HEADER_HEIGHT,
        ),
        fill=NAVY_2,
        outline="#5476A5",
        width=1,
    )

    _draw_text(
        draw,
        (
            actual_left + actual_width / 2,
            y + GROUP_HEADER_HEIGHT / 2,
        ),
        "ACTUAL WASTE",
        15,
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
            MARGIN
            + sum(
                widths[:index]
            )
        )

        column_width = widths[index]

        draw.rectangle(
            (
                left,
                y + GROUP_HEADER_HEIGHT,
                left + column_width,
                y
                + GROUP_HEADER_HEIGHT
                + SUB_HEADER_HEIGHT,
            ),
            fill=NAVY_2,
            outline="#5476A5",
            width=1,
        )

        _draw_text(
            draw,
            (
                left + column_width / 2,
                y
                + GROUP_HEADER_HEIGHT
                + SUB_HEADER_HEIGHT / 2,
            ),
            label,
            14,
            True,
            WHITE,
            "mm",
        )

    y += (
        GROUP_HEADER_HEIGHT
        + SUB_HEADER_HEIGHT
    )

    # ========================================================
    # TABLE DATA
    # ========================================================

    for row_index, (_, row) in enumerate(
        data.iterrows()
    ):
        row_height = row_heights[
            row_index
        ]

        row_fill = (
            WHITE
            if row_index % 2 == 0
            else ROW_ALT
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
            _format_integer(
                row.get(
                    "PO"
                )
            ),
            _format_integer(
                row.get(
                    "Predicted Waste"
                )
            ),
            _format_percent(
                row.get(
                    "Predicted %"
                )
            ),
            _format_integer(
                row.get(
                    "Actual Waste"
                )
            ),
            _format_percent(
                row.get(
                    "Actual %"
                )
            ),
            _format_integer(
                row.get(
                    "Extra Waste"
                )
            ),
            wrapped_reasons[
                row_index
            ],
        ]

        x = MARGIN

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
                fill=row_fill,
                outline=GRID,
                width=1,
            )

            color = TEXT

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
                    row["Predicted %"]
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
                    row["Extra Waste"]
                )
                > 0
            ):
                color = RED

            if column_index == 10:
                _draw_left(
                    draw,
                    (
                        x,
                        y,
                        x + column_width,
                        y + row_height,
                    ),
                    value,
                    REASON_FONT_SIZE,
                    True,
                    TEXT,
                )
            else:
                _draw_centered(
                    draw,
                    (
                        x,
                        y,
                        x + column_width,
                        y + row_height,
                    ),
                    value,
                    17,
                    True,
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

    summary_gap = 18

    card_width = (
        WIDTH
        - 2 * MARGIN
        - summary_gap
    ) // 2

    def draw_summary_card(
        left,
        title,
        kind,
    ):
        card_bottom = (
            y
            + SUMMARY_HEIGHT
        )

        draw.rounded_rectangle(
            (
                left,
                y,
                left + card_width,
                card_bottom,
            ),
            radius=16,
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
            radius=16,
            fill=NAVY_2,
        )

        draw.rectangle(
            (
                left,
                y + 30,
                left + card_width,
                y + 48,
            ),
            fill=NAVY_2,
        )

        _draw_text(
            draw,
            (
                left + 18,
                y + 24,
            ),
            title,
            17,
            True,
            WHITE,
            "lm",
        )

        total_width = 140

        total_right = (
            left
            + card_width
            - 14
        )

        total_left = (
            total_right
            - total_width
        )

        metrics_left = (
            left
            + 10
        )

        metrics_right = (
            total_left
            - 10
        )

        metrics_area = (
            metrics_right
            - metrics_left
        )

        machine_count = max(
            1,
            len(
                machine_summary
            ),
        )

        metric_width = (
            metrics_area
            / machine_count
        )

        for index, machine in enumerate(
            machine_summary
        ):
            center_x = (
                metrics_left
                + metric_width * index
                + metric_width / 2
            )

            machine_label = machine[
                "name"
            ]

            if machine_label == "PRESS-4 / COL B":
                display_label = (
                    "PRESS-4 /\n"
                    "COL B %"
                )
            else:
                display_label = (
                    f"{machine_label} %"
                )

            _draw_centered(
                draw,
                (
                    center_x
                    - metric_width / 2,
                    y + 67,
                    center_x
                    + metric_width / 2,
                    y + 112,
                ),
                display_label,
                14,
                True,
                TEXT,
            )

            value = (
                machine[
                    "predicted"
                ]
                if kind == "predicted"
                else machine[
                    "actual"
                ]
            )

            _draw_text(
                draw,
                (
                    center_x,
                    y + 149,
                ),
                (
                    "—"
                    if value is None
                    else f"{value:.2f}%"
                ),
                25,
                True,
                BLUE
                if kind == "predicted"
                else GREEN,
                "ma",
            )

        total_top = (
            y
            + 62
        )

        total_bottom = (
            y
            + 175
        )

        draw.rounded_rectangle(
            (
                total_left,
                total_top,
                total_right,
                total_bottom,
            ),
            radius=13,
            fill=(
                NAVY
                if kind == "predicted"
                else "#075F46"
            ),
        )

        _draw_text(
            draw,
            (
                (
                    total_left
                    + total_right
                )
                / 2,
                total_top + 27,
            ),
            (
                "TOTAL PREDICT"
                if kind == "predicted"
                else "TOTAL ACTUAL"
            ),
            12,
            True,
            WHITE,
            "ma",
        )

        total_value = (
            overall[
                "predicted"
            ]
            if kind == "predicted"
            else overall[
                "actual"
            ]
        )

        _draw_text(
            draw,
            (
                (
                    total_left
                    + total_right
                )
                / 2,
                total_top + 73,
            ),
            (
                "—"
                if total_value is None
                else f"{total_value:.2f}%"
            ),
            30,
            True,
            WHITE,
            "ma",
        )

    draw_summary_card(
        MARGIN,
        "PREDICTED SUMMARY",
        "predicted",
    )

    draw_summary_card(
        MARGIN
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
