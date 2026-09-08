from io import BytesIO
import textwrap

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from modules.avp_engine import finalize_calculations


# ============================================================
# EMERGENCY STABLE PNG RENDERER
# No Playwright / Chromium required.
# Designed for Streamlit Cloud when packages.txt is disabled.
# ============================================================

NAVY = "#061A3F"
NAVY2 = "#0B2F63"
BLUE = "#1565D8"
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


def _center(draw, box, value, size=16, bold=False, fill=TEXT, spacing=4):
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


def _left(draw, box, value, size=15, bold=False, fill=TEXT, spacing=4):
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
    """
    Machine column currently contains plant-head press names:
    Press 1 / Press 3 / Press 4 / Press 5.
    """
    work = data.copy()
    work["_press"] = work["Machine"].astype(str).str.upper().str.strip()

    press_order = ["PRESS 1", "PRESS 3", "PRESS 4", "PRESS 5"]
    result = []

    for press in press_order:
        group = work[work["_press"] == press]

        if group.empty:
            continue

        po = pd.to_numeric(group["PO"], errors="coerce").fillna(0).sum()
        pred = pd.to_numeric(
            group["Predicted Waste"],
            errors="coerce",
        ).sum(min_count=1)
        actual = pd.to_numeric(
            group["Actual Waste"],
            errors="coerce",
        ).fillna(0).sum()

        result.append(
            {
                "name": press.title(),
                "predicted": round(pred / po * 100, 2)
                if po and pd.notna(pred)
                else None,
                "actual": round(actual / po * 100, 2)
                if po
                else None,
            }
        )

    total_po = pd.to_numeric(work["PO"], errors="coerce").fillna(0).sum()
    total_pred = pd.to_numeric(
        work["Predicted Waste"],
        errors="coerce",
    ).sum(min_count=1)
    total_actual = pd.to_numeric(
        work["Actual Waste"],
        errors="coerce",
    ).fillna(0).sum()

    overall = {
        "predicted": round(total_pred / total_po * 100, 2)
        if total_po and pd.notna(total_pred)
        else None,
        "actual": round(total_actual / total_po * 100, 2)
        if total_po
        else None,
    }

    return result, overall


def generate_management_png(df, report_type):
    """
    Stable final PNG generator.
    Works without Chromium / Playwright.
    """

    data = finalize_calculations(df).reset_index(drop=True)
    machines, overall = _build_summary(data)

    # --------------------------------------------------------
    # Canvas
    # --------------------------------------------------------

    W = 1536
    M = 28

    HEADER_H = 138
    TABLE_GAP = 26
    GROUP_H = 50
    SUB_H = 44

    columns = [
        ("EDITION\nDATE", 112),
        ("PRESS", 110),
        ("MACHINE\nIN-CHARGE", 150),
        ("PUBLICATION", 105),
        ("PO", 95),
        ("PRED QTY", 96),
        ("PRED %", 82),
        ("ACT QTY", 96),
        ("ACT %", 82),
        ("EXTRA\nWASTE", 100),
        ("REASON FOR EXTRA WASTE", 436),
    ]

    widths = [w for _, w in columns]

    # --------------------------------------------------------
    # Dynamic reason wrapping
    # --------------------------------------------------------

    dummy = Image.new("RGB", (W, 100), WHITE)
    ddraw = ImageDraw.Draw(dummy)

    reason_font = _font(16, True)
    reason_inner_width = columns[-1][1] - 26

    wrapped_reasons = []
    row_heights = []

    for _, row in data.iterrows():
        reason = _safe_reason(
            row.get("Reason for Extra Waste", "NA")
        )

        lines = _wrap_by_pixels(
            ddraw,
            reason,
            reason_inner_width,
            reason_font,
        )

        wrapped_reasons.append("\n".join(lines))

        if len(lines) == 1:
            row_h = 72
        elif len(lines) == 2:
            row_h = 86
        elif len(lines) == 3:
            row_h = 100
        else:
            row_h = 34 + len(lines) * 23

        row_heights.append(row_h)

    SUMMARY_GAP = 28
    SUMMARY_H = 195
    BOTTOM = 24

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

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    draw.rounded_rectangle(
        (0, 0, W, HEADER_H),
        radius=22,
        fill=NAVY,
    )

    draw.text(
        (34, 35),
        "PIQ",
        font=_font(50, True),
        fill=WHITE,
    )

    draw.text(
        (130, 57),
        "PressIQ",
        font=_font(22, True),
        fill="#E2E8F0",
    )

    title = "Actual vs Predicted Waste Report"
    title_font = _font(38, True)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_box[2] - title_box[0]

    draw.text(
        ((W - title_w) / 2, 30),
        title,
        font=title_font,
        fill=WHITE,
    )

    issue_date = "—"

    if (
        "Edition Date" in data.columns
        and data["Edition Date"].notna().any()
    ):
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
    subtitle_box = draw.textbbox(
        (0, 0),
        subtitle,
        font=subtitle_font,
    )
    subtitle_w = subtitle_box[2] - subtitle_box[0]

    draw.text(
        ((W - subtitle_w) / 2, 88),
        subtitle,
        font=subtitle_font,
        fill="#DCEAFF",
    )

    # --------------------------------------------------------
    # Table header
    # --------------------------------------------------------

    y = table_top

    fixed = [0, 1, 2, 3, 4, 9, 10]

    for idx in fixed:
        x = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (
                x,
                y,
                x + w,
                y + GROUP_H + SUB_H,
            ),
            fill=NAVY2,
            outline="#5476A5",
            width=1,
        )

        _center(
            draw,
            (
                x,
                y,
                x + w,
                y + GROUP_H + SUB_H,
            ),
            columns[idx][0],
            15,
            True,
            WHITE,
        )

    pred_left = M + sum(widths[:5])
    pred_w = widths[5] + widths[6]

    draw.rectangle(
        (
            pred_left,
            y,
            pred_left + pred_w,
            y + GROUP_H,
        ),
        fill=NAVY2,
        outline="#5476A5",
        width=1,
    )

    _center(
        draw,
        (
            pred_left,
            y,
            pred_left + pred_w,
            y + GROUP_H,
        ),
        "PREDICTED WASTE",
        15,
        True,
        WHITE,
    )

    actual_left = M + sum(widths[:7])
    actual_w = widths[7] + widths[8]

    draw.rectangle(
        (
            actual_left,
            y,
            actual_left + actual_w,
            y + GROUP_H,
        ),
        fill=NAVY2,
        outline="#5476A5",
        width=1,
    )

    _center(
        draw,
        (
            actual_left,
            y,
            actual_left + actual_w,
            y + GROUP_H,
        ),
        "ACTUAL WASTE",
        15,
        True,
        WHITE,
    )

    for idx, label in [
        (5, "Qty"),
        (6, "%"),
        (7, "Qty"),
        (8, "%"),
    ]:
        x = M + sum(widths[:idx])
        w = widths[idx]

        draw.rectangle(
            (
                x,
                y + GROUP_H,
                x + w,
                y + GROUP_H + SUB_H,
            ),
            fill=NAVY2,
            outline="#5476A5",
            width=1,
        )

        _center(
            draw,
            (
                x,
                y + GROUP_H,
                x + w,
                y + GROUP_H + SUB_H,
            ),
            label,
            14,
            True,
            WHITE,
        )

    y += GROUP_H + SUB_H

    # --------------------------------------------------------
    # Rows
    # --------------------------------------------------------

    for i, (_, row) in enumerate(data.iterrows()):
        row_h = row_heights[i]
        fill = WHITE if i % 2 == 0 else ALT

        date_text = (
            pd.to_datetime(
                row["Edition Date"]
            ).strftime("%d/%m/%Y")
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

        for j, ((_, w), value) in enumerate(
            zip(columns, values)
        ):
            draw.rectangle(
                (
                    x,
                    y,
                    x + w,
                    y + row_h,
                ),
                fill=fill,
                outline=GRID,
                width=1,
            )

            color = TEXT

            if j == 6:
                color = BLUE

            # Actual Waste %:
            # red if above prediction, green if below prediction.
            if (
                j == 8
                and pd.notna(row.get("Predicted %"))
                and pd.notna(row.get("Actual %"))
            ):
                if float(row["Actual %"]) > float(row["Predicted %"]):
                    color = RED
                elif float(row["Actual %"]) < float(row["Predicted %"]):
                    color = GREEN

            # Extra Waste:
            # red when Actual > Predicted; green otherwise.
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
                    (
                        x,
                        y,
                        x + w,
                        y + row_h,
                    ),
                    value,
                    16,
                    True,
                    TEXT,
                )
            else:
                _center(
                    draw,
                    (
                        x,
                        y,
                        x + w,
                        y + row_h,
                    ),
                    value,
                    16,
                    True,
                    color,
                )

            x += w

        y += row_h

    # --------------------------------------------------------
    # Summary cards
    # --------------------------------------------------------

    y += SUMMARY_GAP

    card_gap = 22
    card_w = (W - 2 * M - card_gap) // 2

    def draw_summary_card(left, title, kind):
        draw.rounded_rectangle(
            (
                left,
                y,
                left + card_w,
                y + SUMMARY_H,
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
                left + card_w,
                y + 50,
            ),
            radius=16,
            fill=NAVY2,
        )

        draw.rectangle(
            (
                left,
                y + 31,
                left + card_w,
                y + 50,
            ),
            fill=NAVY2,
        )

        draw.text(
            (left + 18, y + 14),
            title,
            font=_font(17, True),
            fill=WHITE,
        )

        total_w = 150
        total_right = left + card_w - 16
        total_left = total_right - total_w

        metrics_left = left + 12
        metrics_right = total_left - 10
        metrics_width = metrics_right - metrics_left

        count = max(1, len(machines))
        each = metrics_width / count

        for idx, machine in enumerate(machines):
            cx = metrics_left + each * idx + each / 2

            _center(
                draw,
                (
                    cx - each / 2,
                    y + 69,
                    cx + each / 2,
                    y + 111,
                ),
                f"{machine['name']} %",
                14,
                True,
                TEXT,
            )

            value = machine[kind]

            _center(
                draw,
                (
                    cx - each / 2,
                    y + 115,
                    cx + each / 2,
                    y + 169,
                ),
                "—" if value is None else f"{value:.2f}%",
                25,
                True,
                BLUE if kind == "predicted" else GREEN,
            )

        total_top = y + 62
        total_bottom = y + 174

        draw.rounded_rectangle(
            (
                total_left,
                total_top,
                total_right,
                total_bottom,
            ),
            radius=13,
            fill=NAVY if kind == "predicted" else "#075F46",
        )

        _center(
            draw,
            (
                total_left,
                total_top + 8,
                total_right,
                total_top + 46,
            ),
            "TOTAL PREDICT" if kind == "predicted" else "TOTAL ACTUAL",
            12,
            True,
            WHITE,
        )

        total_value = overall[kind]

        _center(
            draw,
            (
                total_left,
                total_top + 48,
                total_right,
                total_bottom - 8,
            ),
            "—" if total_value is None else f"{total_value:.2f}%",
            30,
            True,
            WHITE,
        )

    draw_summary_card(
        M,
        "PREDICTED SUMMARY",
        "predicted",
    )

    draw_summary_card(
        M + card_w + card_gap,
        "ACTUAL SUMMARY",
        "actual",
    )

    output = BytesIO()
    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output.getvalue()
