import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def find_col(df, possible_names):
    cols = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        key = name.strip().lower()
        if key in cols:
            return cols[key]
    return None


def read_edition_file(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    colmap = {
        "Edition Date": find_col(df, ["Edition Date (DD-MM-YYYY)", "Edition Date"]),
        "Edition": find_col(df, ["Edition"]),
        "Edition Name": find_col(df, ["Edition Name"]),
        "Print Order": find_col(df, ["Print Order"]),
        "Main/Supplement": find_col(df, ["Edition (Main/Supl)", "Main/Supplement"]),
        "Press": find_col(df, ["Press", "Press No", "Press Number", "Machine"]),
        "Folder": find_col(df, ["Folder", "Folder Type", "Folder Used"]),
        "Machine": find_col(df, ["Machine"]),
        "Main Pages": find_col(df, ["Total Main Pages (Broad sheet)", "Main Pages", "Total Main Pages"]),
        "Ballooned Pages": find_col(df, ["Total Balooned pages(Broad sheet)", "Total Ballooned Pages", "Ballooned Pages"]),
        "GNP/SNP": find_col(df, ["GNP/SNP", "SNP/GNP", "GNP", "SNP"]),
        "Complexity": find_col(df, ["Complexity"]),
        "Type of Start": find_col(df, ["Type of Start"]),
        "White Kg": find_col(df, ["White copies in Kg"]),
        "Scum Kg": find_col(df, ["Scum Copies in Kg"]),
        "Cut-off Kg": find_col(df, ["Cut-off Copies in Kg"]),
        "Registration Kg": find_col(df, ["Registration Copies in Kg"]),
        "Density Variation Kg": find_col(df, ["Density Variation Copies in Kg"]),
        "Other Kg": find_col(df, ["Other waste copies in Kg"]),
        "Pasting Kg": find_col(df, ["Total pasting copies in Kg"]),
        "Total Waste Kg": find_col(df, ["Total waste in KG", "Total Waste in KG"]),
        "Department": find_col(df, ["Department", "Dept"]),
        "Waste Reason": find_col(df, ["Waste Reason", "Reason", "Reason for Waste"]),
        "RS": find_col(df, ["RS", "RS No", "Reelstand", "Reel Stand"]),
        "PU": find_col(df, ["PU"]),
        "PC": find_col(df, ["PC"]),
        "BL": find_col(df, ["BL"]),
        "Remarks": find_col(df, ["Remarks", "Remark", "Comments", "Comment"]),
        "Corrective Action": find_col(df, ["Corrective Action", "Action Taken", "Action"]),
    }

    out = pd.DataFrame()

    for new_col, old_col in colmap.items():
        if old_col is None:
            out[new_col] = 0 if "Kg" in new_col or new_col == "Print Order" else ""
        else:
            out[new_col] = df[old_col]

    out["Edition Date"] = pd.to_datetime(out["Edition Date"], errors="coerce", dayfirst=True)
    out = out[out["Edition Date"].notna()].copy()

    kg_cols = [
        "White Kg",
        "Scum Kg",
        "Cut-off Kg",
        "Registration Kg",
        "Density Variation Kg",
        "Other Kg",
        "Pasting Kg",
        "Total Waste Kg",
        "Print Order",
        "Main Pages",
        "Ballooned Pages",
    ]

    for col in kg_cols:
        out[col] = to_num(out[col])

    text_cols = [
        "Edition",
        "Edition Name",
        "Machine",
        "Main/Supplement",
        "Press",
        "Folder",
        "GNP/SNP",
        "Complexity",
        "Type of Start",
        "Department",
        "Waste Reason",
        "RS",
        "PU",
        "PC",
        "BL",
        "Remarks",
        "Corrective Action",
    ]

    for col in text_cols:
        out[col] = out[col].astype(str).str.strip().replace("nan", "")

    out["White MT"] = out["White Kg"] / 1000
    out["Scum MT"] = out["Scum Kg"] / 1000
    out["Cut-off MT"] = out["Cut-off Kg"] / 1000
    out["Registration MT"] = out["Registration Kg"] / 1000
    out["Density Variation MT"] = out["Density Variation Kg"] / 1000
    out["Other MT"] = out["Other Kg"] / 1000
    out["Pasting MT"] = out["Pasting Kg"] / 1000
    out["Total Waste MT"] = out["Total Waste Kg"] / 1000
    out["Total Pages"] = out["Main Pages"] + out["Ballooned Pages"]

    return out


def round_display(df):
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if "MT" in col:
                out[col] = out[col].round(3)
            elif "KG" in col or "Kg" in col:
                out[col] = out[col].round(0)
            elif "%" in col:
                out[col] = out[col].round(2)
            else:
                out[col] = out[col].round(0)
    return out


def filter_by_date(df, start_date, end_date):
    return df[
        (df["Edition Date"].dt.date >= start_date) &
        (df["Edition Date"].dt.date <= end_date)
    ].copy()


def clean_text_value(value):
    value = str(value).strip()
    if value.lower() in ["nan", "none", ""]:
        return ""
    return value


def top_text_values(df, col, limit=5):
    if col not in df.columns:
        return []

    data = df[col].apply(clean_text_value).replace("", pd.NA).dropna()

    if data.empty:
        return []

    return data.value_counts().head(limit).index.tolist()


def top_edition_lines(issue_df, selected_col, limit=5):
    if issue_df.empty:
        return []

    edition_group = (
        issue_df.groupby(["Edition", "Edition Name"], dropna=False)[selected_col]
        .sum()
        .reset_index()
        .sort_values(selected_col, ascending=False)
        .head(limit)
    )

    lines = []

    for _, row in edition_group.iterrows():
        edition = clean_text_value(row.get("Edition", ""))
        edition_name = clean_text_value(row.get("Edition Name", ""))
        waste_kg = row[selected_col] * 1000

        label = edition_name if edition_name else edition
        if edition and edition_name:
            label = f"{edition} - {edition_name}"

        lines.append(f"{label}: {waste_kg:,.0f} KG")

    return lines


def remark_lines(issue_df, selected_col, limit=8):
    if issue_df.empty or "Remarks" not in issue_df.columns:
        return []

    remark_df = issue_df.copy()
    remark_df["Remarks"] = remark_df["Remarks"].apply(clean_text_value)
    remark_df = remark_df[remark_df["Remarks"] != ""]

    if remark_df.empty:
        return []

    remark_df = remark_df.sort_values(selected_col, ascending=False).head(limit)

    lines = []

    for _, row in remark_df.iterrows():
        date_val = row.get("Edition Date", "")

        try:
            date_text = pd.to_datetime(date_val).strftime("%d-%b")
        except Exception:
            date_text = ""

        edition = clean_text_value(row.get("Edition", ""))
        edition_name = clean_text_value(row.get("Edition Name", ""))
        remarks = clean_text_value(row.get("Remarks", ""))
        waste_reason = clean_text_value(row.get("Waste Reason", ""))
        pu = clean_text_value(row.get("PU", ""))
        pc = clean_text_value(row.get("PC", ""))

        loc_parts = []
        if pu:
            loc_parts.append(pu)
        if pc:
            loc_parts.append(pc)

        location_text = f" | Location: {' / '.join(loc_parts)}" if loc_parts else ""
        reason_text = f" | Issue: {waste_reason}" if waste_reason else ""

        edition_label = edition_name if edition_name else edition
        if edition and edition_name:
            edition_label = f"{edition} - {edition_name}"

        lines.append(
            f"{date_text} | {edition_label}{reason_text}{location_text} | Remark: {remarks}"
        )

    return lines


def issue_action_recommendations(selected_issue):
    recommendations = {
        "Registration Waste": {
            "owner": "Electrical + Production",
            "priorities": [
                (
                    "Register Control / Correction Response",
                    "Check correction response, camera/sensor cleanliness, register motor response, and stability of repeated PU / PC locations.",
                ),
                (
                    "PU / PC Hotspot Verification",
                    "Physically verify repeated PU / PC points and compare with previous register correction history.",
                ),
                (
                    "Start-up Discipline",
                    "Review first-good-copy approval timing and operator correction response during start-up.",
                ),
            ],
        },
        "Scum Waste": {
            "owner": "Production + Mechanical",
            "priorities": [
                (
                    "Dampening System Check",
                    "Verify dampening roller setting, water flow, water pan condition, and fountain solution parameters.",
                ),
                (
                    "Plate / Blanket Condition",
                    "Inspect plate surface and blanket condition where scum was repeatedly reported.",
                ),
                (
                    "Ink-Water Balance Discipline",
                    "Review operator correction timing and standardize scum response during start-up.",
                ),
            ],
        },
        "Cut-off Waste": {
            "owner": "Mechanical + Production",
            "priorities": [
                (
                    "Folder / Cut-off Timing",
                    "Check folder timing, cut-off setting, and related mechanical adjustment.",
                ),
                (
                    "Web Tension / Draw Setting",
                    "Verify web tension and draw settings during affected editions.",
                ),
                (
                    "Mechanical Play Verification",
                    "Inspect folder section for repeated cut-off variation.",
                ),
            ],
        },
        "Density Variation Waste": {
            "owner": "Production + Electrical",
            "priorities": [
                (
                    "Density Control Response",
                    "Check density correction response and ink key setting stability.",
                ),
                (
                    "Ink Flow / Roller Condition",
                    "Verify ink flow and roller condition on repeated locations.",
                ),
                (
                    "Sensor / Measurement Check",
                    "Validate density measurement and control feedback if repeated.",
                ),
            ],
        },
        "Other Waste": {
            "owner": "Production + Concerned Department",
            "priorities": [
                (
                    "Reason Classification",
                    "Review remarks and classify repeated other waste into proper reason codes.",
                ),
                (
                    "Ownership Assignment",
                    "Assign department ownership based on event remark and location.",
                ),
                (
                    "Repeat Event Control",
                    "Track repeated other waste by edition and location.",
                ),
            ],
        },
        "Pasting Waste": {
            "owner": "Mechanical + Production",
            "priorities": [
                (
                    "Paster Timing / Splice Quality",
                    "Check paster timing, splice quality, and paster response.",
                ),
                (
                    "Reelstand Condition",
                    "Verify reelstand condition where pasting waste is repeated.",
                ),
                (
                    "Reel Preparation Discipline",
                    "Review reel preparation and operator procedure before splice.",
                ),
            ],
        },
    }

    return recommendations.get(selected_issue, recommendations["Other Waste"])


def bullet_html(items):
    if not items:
        return "<li>No specific records available in uploaded file for this field.</li>"
    return "".join([f"<li>{item}</li>" for item in items])


def priority_card(title, evidence, action, owner):
    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-left:7px solid #2563eb;
            border-radius:18px;
            padding:18px 20px;
            margin-bottom:14px;
            box-shadow:0 6px 16px rgba(15,23,42,0.07);
        ">
            <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                {title}
            </div>
            <div style="font-size:14px;color:#334155;margin-bottom:6px;">
                <b>Evidence:</b> {evidence}
            </div>
            <div style="font-size:14px;color:#334155;margin-bottom:6px;">
                <b>Action:</b> {action}
            </div>
            <div style="font-size:14px;color:#334155;">
                <b>Owner:</b> {owner}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def scroll_to_top():
    st.markdown(
        """
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True,
    )


def action_card(title, subtitle, points, button_text, button_key, target_view, accent_color):
    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-left:8px solid {accent_color};
            border-radius:22px;
            padding:24px;
            min-height:235px;
            box-shadow:0 8px 22px rgba(15,23,42,0.08);
            margin-bottom:14px;
        ">
            <div style="font-size:24px;font-weight:850;color:#0f172a;margin-bottom:6px;">
                {title}
            </div>
            <div style="font-size:14px;color:#475569;margin-bottom:14px;">
                {subtitle}
            </div>
            {f'''
            <ul style="font-size:14px;color:#334155;line-height:1.8;">
                {''.join([f'<li>{p}</li>' for p in points])}
            </ul>
            ''' if points else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(button_text, key=button_key, use_container_width=True):
        st.session_state["edition_view"] = target_view
        st.rerun()


def build_segment_df(filtered):
    top_segment = {
        "White Waste": filtered["White MT"].sum(),
        "Scum Waste": filtered["Scum MT"].sum(),
        "Cut-off Waste": filtered["Cut-off MT"].sum(),
        "Registration Waste": filtered["Registration MT"].sum(),
        "Density Variation Waste": filtered["Density Variation MT"].sum(),
        "Other Waste": filtered["Other MT"].sum(),
        "Pasting Waste": filtered["Pasting MT"].sum(),
    }

    segment_df = pd.DataFrame({
        "Waste by Category": list(top_segment.keys()),
        "Waste MT": list(top_segment.values()),
    }).sort_values("Waste MT", ascending=False)

    return segment_df, top_segment


def build_segment_kg_df(df):
    return pd.DataFrame({
        "Waste Segment": [
            "Registration Waste",
            "Scum Waste",
            "White Waste",
            "Cut-off Waste",
            "Density Variation Waste",
            "Other Waste",
            "Pasting Waste",
        ],
        "Waste KG": [
            df["Registration MT"].sum() * 1000,
            df["Scum MT"].sum() * 1000,
            df["White MT"].sum() * 1000,
            df["Cut-off MT"].sum() * 1000,
            df["Density Variation MT"].sum() * 1000,
            df["Other MT"].sum() * 1000,
            df["Pasting MT"].sum() * 1000,
        ],
    }).sort_values("Waste KG", ascending=False)


def build_reported_action_area_df(df):
    work = df.copy()

    for col in ["Waste Reason", "Department", "Folder", "PU", "PC", "RS", "BL"]:
        if col not in work.columns:
            work[col] = ""

    def combine_area(row):
        parts = []
        for label in ["Folder", "PU", "PC", "RS", "BL"]:
            value = clean_text_value(row.get(label, ""))
            if value:
                parts.append(f"{label}: {value}")
        return " / ".join(parts) if parts else "Not specified"

    work["Reported Area"] = work.apply(combine_area, axis=1)
    work["Waste Reason"] = work["Waste Reason"].apply(clean_text_value)
    work["Department"] = work["Department"].apply(clean_text_value)
    work["Waste Reason"] = work["Waste Reason"].replace("", "Not specified")
    work["Department"] = work["Department"].replace("", "Not specified")
    work["Total Waste KG"] = work["Total Waste MT"] * 1000

    action_df = (
        work.groupby(["Waste Reason", "Department", "Reported Area"], dropna=False)["Total Waste KG"]
        .sum()
        .reset_index()
        .sort_values("Total Waste KG", ascending=False)
    )

    action_df = action_df[action_df["Total Waste KG"] > 0]
    action_df = action_df[
        ~(
            (action_df["Waste Reason"] == "Not specified") &
            (action_df["Department"] == "Not specified") &
            (action_df["Reported Area"].astype(str).str.startswith("Folder:"))
        )
    ]    

    return action_df


def build_all_remarks_df(df):
    work = df.copy()

    if "Remarks" not in work.columns:
        return pd.DataFrame()

    work["Remarks"] = work["Remarks"].apply(clean_text_value)
    work = work[work["Remarks"] != ""].copy()

    if work.empty:
        return pd.DataFrame()

    for col in ["Edition", "Edition Name", "Waste Reason", "Folder", "PU", "PC", "RS", "BL"]:
        if col not in work.columns:
            work[col] = ""

    def combine_area(row):
        parts = []
        for label in ["Folder", "PU", "PC", "RS", "BL"]:
            value = clean_text_value(row.get(label, ""))
            if value:
                parts.append(f"{label}: {value}")
        return " / ".join(parts)

    work["Date"] = pd.to_datetime(work["Edition Date"], errors="coerce").dt.strftime("%d-%b-%Y")
    work["Edition Detail"] = work.apply(
        lambda r: clean_text_value(r.get("Edition", "")) + " - " + clean_text_value(r.get("Edition Name", "")),
        axis=1,
    )
    work["Reported Area"] = work.apply(combine_area, axis=1)
    work["Total Waste KG"] = work["Total Waste MT"] * 1000

    return work[[
        "Date",
        "Edition Detail",
        "Waste Reason",
        "Reported Area",
        "Remarks",
        "Total Waste KG",
    ]].sort_values("Date")


def build_ai_context(plant_name, maint_start, maint_end, maint_df):
    total_waste_kg = maint_df["Total Waste MT"].sum() * 1000
    segment_df = build_segment_kg_df(maint_df)
    action_area_df = build_reported_action_area_df(maint_df)
    remarks_df = build_all_remarks_df(maint_df)

    segment_lines = [
        f"{row['Waste Segment']}: {row['Waste KG']:,.0f} KG"
        for _, row in segment_df.iterrows()
    ]

    action_lines = []
    for _, row in action_area_df.head(15).iterrows():
        action_lines.append(
            f"Issue: {row['Waste Reason']} | Department: {row['Department']} | "
            f"Area: {row['Reported Area']} | Waste: {row['Total Waste KG']:,.0f} KG"
        )

    remark_lines_text = []
    if not remarks_df.empty:
        for _, row in remarks_df.head(20).iterrows():
            remark_lines_text.append(
                f"{row['Date']} | {row['Edition Detail']} | Issue: {row['Waste Reason']} | "
                f"Area: {row['Reported Area']} | Remark: {row['Remarks']}"
            )

    return f"""
Plant: {plant_name}
Selected maintenance period: {maint_start} to {maint_end}
Total waste: {total_waste_kg:,.0f} KG

Segment-wise waste:
{chr(10).join(segment_lines)}

Reported action areas:
{chr(10).join(action_lines) if action_lines else "No reported action areas available."}

Night shift remarks:
{chr(10).join(remark_lines_text) if remark_lines_text else "No night shift remarks available."}
"""


def ask_pressiq_ai(question, context_text=None):
    if not GEMINI_AVAILABLE:
        return "Gemini package is not installed. Please add google-genai in requirements.txt and reboot app."

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return "Gemini API key is missing. Please add GEMINI_API_KEY in Streamlit Secrets."

    try:
        client = genai.Client(api_key=api_key)
        
        uploaded_context = context_text if context_text else "No uploaded report context provided."

        prompt = f"""
You are PressIQ AI Assistant for newspaper offset printing operations.

Answer in simple, practical language for maintenance, production, and shopfloor teams.

Use:
1. General newspaper offset printing knowledge.
2. Uploaded report context when available.

Rules:
- If question is about uploaded report, use uploaded context.
- If question is about printing process, explain practically.
- Do not invent plant-approved standards.
- If exact plant standard is required, say it should be checked with plant SOP, chemical supplier, or process standard.
- Keep the answer structured, direct, and action-oriented.
- Use KG where waste quantity is discussed.
- Avoid unnecessary long theory.

Uploaded report context:
{uploaded_context}

User question:
{question}
"""

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        return response.text

    except Exception as e:
        return f"Gemini Error: {e}"


def render_pressiq_ai_assistant(context_text=None):
    st.markdown("---")
    st.markdown("## Ask PressIQ Assistant")

    st.caption(
        "Ask about this report, scum, registration, dampening, cut-off, consumables, maintenance checks, or newspaper printing process."
    )

    user_question = st.text_input(
        "Type your question",
        placeholder="Example: Which issue needs maintenance priority from this report?",
        key="pressiq_ai_question",
    )

    if st.button("Ask PressIQ", key="ask_pressiq_button"):
        if not user_question.strip():
            st.warning("Please type a question.")
        else:
            with st.spinner("PressIQ Assistant is thinking..."):
                answer = ask_pressiq_ai(user_question, context_text)

            st.session_state["pressiq_ai_answer"] = answer

    if st.session_state.get("pressiq_ai_answer"):
        st.markdown("### PressIQ Answer")
        st.write(st.session_state["pressiq_ai_answer"])


def make_pdf_paragraph(text, style):
    text = escape(clean_text_value(text))
    return Paragraph(text, style)


def generate_maintenance_pdf(plant_name, start_date, end_date, maint_df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PressIQTitle",
        parent=styles["Title"],
        fontSize=15,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#0f172a"),
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=10,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=5,
        spaceAfter=4,
    )

    normal_style = ParagraphStyle(
        "NormalSmall",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
    )

    cell_style = ParagraphStyle(
        "CellSmall",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        alignment=TA_LEFT,
    )

    story = []

    total_waste_kg = maint_df["Total Waste MT"].sum() * 1000
    segment_kg_df = build_segment_kg_df(maint_df)
    action_area_df = build_reported_action_area_df(maint_df)
    remarks_df = build_all_remarks_df(maint_df)

    story.append(Paragraph("PressIQ Daily Maintenance Action Report", title_style))
    story.append(Paragraph(f"Plant: {plant_name}", normal_style))
    story.append(Paragraph(f"Period: {start_date} to {end_date}", normal_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph(f"<b>Overall Waste:</b> {total_waste_kg:,.0f} KG", section_style))

    seg_data = [[
        make_pdf_paragraph("Waste Segment", cell_style),
        make_pdf_paragraph("Waste KG", cell_style),
    ]]

    for _, row in segment_kg_df.iterrows():
        seg_data.append([
            make_pdf_paragraph(row["Waste Segment"], cell_style),
            make_pdf_paragraph(f"{row['Waste KG']:,.0f}", cell_style),
        ])

    seg_table = Table(seg_data, colWidths=[120 * mm, 35 * mm])
    seg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    story.append(seg_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Reported Areas Where Action / Improvement Required", section_style))

    if action_area_df.empty:
        story.append(Paragraph("No reported action areas found for the selected period.", normal_style))
    else:
        action_data = [[
            make_pdf_paragraph("Issue / Reason", cell_style),
            make_pdf_paragraph("Department", cell_style),
            make_pdf_paragraph("Reported Area", cell_style),
            make_pdf_paragraph("Waste KG", cell_style),
        ]]

        for _, row in action_area_df.iterrows():
            action_data.append([
                make_pdf_paragraph(row["Waste Reason"], cell_style),
                make_pdf_paragraph(row["Department"], cell_style),
                make_pdf_paragraph(row["Reported Area"], cell_style),
                make_pdf_paragraph(f"{row['Total Waste KG']:,.0f}", cell_style),
            ])

        action_table = Table(action_data, colWidths=[35 * mm, 28 * mm, 72 * mm, 25 * mm])
        action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ]))
        story.append(action_table)

    story.append(Spacer(1, 6))
    story.append(Paragraph("Overall Night Shift Remarks Captured", section_style))

    if remarks_df.empty:
        story.append(Paragraph("No night shift remarks found for the selected period.", normal_style))
    else:
        remark_data = [[
            make_pdf_paragraph("Date", cell_style),
            make_pdf_paragraph("Edition", cell_style),
            make_pdf_paragraph("Issue", cell_style),
            make_pdf_paragraph("Reported Area", cell_style),
            make_pdf_paragraph("Night Shift Remark", cell_style),
        ]]

        for _, row in remarks_df.iterrows():
            remark_data.append([
                make_pdf_paragraph(row["Date"], cell_style),
                make_pdf_paragraph(row["Edition Detail"], cell_style),
                make_pdf_paragraph(row["Waste Reason"], cell_style),
                make_pdf_paragraph(row["Reported Area"], cell_style),
                make_pdf_paragraph(row["Remarks"], cell_style),
            ])

        remark_table = Table(remark_data, colWidths=[18 * mm, 42 * mm, 24 * mm, 36 * mm, 45 * mm])
        remark_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(remark_table)

    story.append(Spacer(1, 8))
    

    doc.build(story)
    buffer.seek(0)
    return buffer


def render_summary_page(df, plant_name, start_date, end_date, min_date, max_date):
    filtered = filter_by_date(df, start_date, end_date)

    if filtered.empty:
        st.warning("No data found for selected date range.")
        return

    if st.button("← Change File / Date Range", key="back_to_input"):
        st.session_state["edition_view"] = "input"
        st.session_state["edition_analysis_ready"] = False
        st.rerun()

    total_waste_mt = filtered["Total Waste MT"].sum()
    total_print_order = filtered["Print Order"].sum()
    total_editions = len(filtered)
    avg_waste_mt = total_waste_mt / total_editions if total_editions else 0
    total_waste_display = f"{total_waste_mt:,.3f}(MT)"
    avg_waste_display = f"{avg_waste_mt:,.3f}(MT)"

    st.markdown(f"## Edition Wise Wastage Summary - {plant_name}")
    st.caption(f"Selected Period: {start_date} to {end_date}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Editions", f"{total_editions:,}")
    k2.metric("Total Waste", total_waste_display)
    k3.metric("Total Print Order", f"{total_print_order:,.0f}")
    k4.metric("Avg Waste / Edition", avg_waste_display)

    segment_df, top_segment = build_segment_df(filtered)


    
    st.markdown("## Waste by Category")

    st.dataframe(round_display(segment_df), use_container_width=True, hide_index=True)

    fig_pie = px.pie(
        segment_df,
        values="Waste MT",
        names="Waste by Category",
        hole=0.45,
        title="Waste category Share",
    )
    st.plotly_chart(fig_pie, use_container_width=True)


    st.markdown("---")
    st.markdown("## Choose Next Action")

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        action_card(
            title="Performance Review Board",
            subtitle="AI-powered plant performance and waste review dashboard.",
            points=[],
            button_text="Open Performance Review Board",
            button_key="open_performance_board",
            target_view="performance",
            accent_color="#7c3aed",
        )
    with action_col2:
        action_card(
            title="Daily Maintenance Action Desk",
            subtitle="AI-powered maintenance planning and action desk.",
            points=[],
            button_text="Open Daily Maintenance Action Desk",
            button_key="open_maintenance_desk",
            target_view="maintenance",
            accent_color="#2563eb",
        )


def render_maintenance_action_desk(df, min_date, max_date, plant_name):
    if st.button("← Back to Summary", key="back_from_maintenance"):
        st.session_state["edition_view"] = "summary"
        st.rerun()

    scroll_to_top()

    st.markdown(
        """
        <div id="page-top"></div>
        <script>
            setTimeout(function() {
                const topElement = window.parent.document.getElementById("page-top");
                if (topElement) {
                    topElement.scrollIntoView({behavior: "instant", block: "start"});
                }
                window.parent.scrollTo(0, 0);
                const main = window.parent.document.querySelector('section.main');
                if (main) {
                    main.scrollTo(0, 0);
                }
            }, 100);
        </script>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"## Daily Maintenance Action Desk - {plant_name}")

    st.markdown(
        """
        <div style="
            background:#f8fafc;
            border:1px solid #e5e7eb;
            border-left:7px solid #2563eb;
            border-radius:18px;
            padding:18px;
            margin-bottom:18px;
        ">
            This desk converts night-shift waste records into a morning maintenance action plan.
            It shows total waste in KG, selected issue impact, affected editions, shop-floor remarks,
            and priority action areas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        maint_start = st.date_input(
            "From Date",
            max_date,
            min_value=min_date,
            max_value=max_date,
            key="maintenance_start_date",
        )

    with c2:
        maint_end = st.date_input(
            "To Date",
            max_date,
            min_value=min_date,
            max_value=max_date,
            key="maintenance_end_date",
        )

    if maint_start > maint_end:
        st.error("From Date cannot be greater than To Date.")
        return

    maint_df = filter_by_date(df, maint_start, maint_end)

    if maint_df.empty:
        st.warning("No data found for selected maintenance date range.")
        return

    total_waste_kg = maint_df["Total Waste MT"].sum() * 1000
    segment_kg_df = build_segment_kg_df(maint_df)

    st.markdown("### Waste by Category")
    st.dataframe(
        round_display(segment_kg_df),
        use_container_width=True,
        hide_index=True,
    )

    issue_options = [
        "Registration Waste",
        "Scum Waste",
        "White Waste",
        "Cut-off Waste",
        "Density Variation Waste",
        "Other Waste",
        "Pasting Waste",
    ]

    selected_issue = st.selectbox(
        "Select Waste Issue for Maintenance Planning",
        issue_options,
        key="maintenance_issue_selector",
    )

    issue_to_col = {
        "Registration Waste": "Registration MT",
        "Scum Waste": "Scum MT",
        "White Waste": "White MT",
        "Cut-off Waste": "Cut-off MT",
        "Density Variation Waste": "Density Variation MT",
        "Other Waste": "Other MT",
        "Pasting Waste": "Pasting MT",
    }

    selected_col = issue_to_col[selected_issue]
    issue_df = maint_df[maint_df[selected_col] > 0].copy()

    issue_waste_kg = issue_df[selected_col].sum() * 1000
    issue_share = (issue_waste_kg / total_waste_kg * 100) if total_waste_kg else 0
    affected_editions = len(issue_df)

    rec = issue_action_recommendations(selected_issue)

    top_editions = top_edition_lines(issue_df, selected_col, limit=5)
    top_departments = top_text_values(issue_df, "Department", limit=3)
    top_reasons = top_text_values(issue_df, "Waste Reason", limit=5)
    top_pu = top_text_values(issue_df, "PU", limit=5)
    top_pc = top_text_values(issue_df, "PC", limit=5)
    top_rs = top_text_values(issue_df, "RS", limit=5)
    top_bl = top_text_values(issue_df, "BL", limit=5)
    top_folders = top_text_values(issue_df, "Folder", limit=5)
    remarks = remark_lines(issue_df, selected_col, limit=8)

    st.markdown("## Total Waste Overview")

    o1, o2, o3, o4 = st.columns(4)

    with o1:
        st.metric("Total Waste", f"{total_waste_kg:,.0f} KG")

    with o2:
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;height:95px;">
                <div style="font-size:13px;color:#64748b;font-weight:600;margin-bottom:8px;">
                    Selected Issue
                </div>
                <div style="font-size:22px;font-weight:700;color:#0f172a;line-height:1.2;">
                    {selected_issue}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with o3:
        st.metric("Issue Waste", f"{issue_waste_kg:,.0f} KG")

    with o4:
        st.metric("Issue Share", f"{issue_share:.1f}%")

    if selected_issue == "White Waste":
        st.markdown("## 1. White Waste Summary")

        w1, w2, w3 = st.columns(3)
        w1.metric("White Waste", f"{issue_waste_kg:,.0f} KG")
        w2.metric("Affected Editions", f"{affected_editions:,}")
        w3.metric("White Waste Share", f"{issue_share:.1f}%")

        st.markdown("### Editions with Higher White Waste")
        st.markdown(f"<ul>{bullet_html(top_editions)}</ul>", unsafe_allow_html=True)

        st.info(
            "White Waste is shown here for visibility and review. "
            "No maintenance priority action is generated for White Waste in this desk."
        )

        st.markdown("## 2. Maintenance Action Plan PDF")

        if REPORTLAB_AVAILABLE:
            pdf_buffer = generate_maintenance_pdf(plant_name, maint_start, maint_end, maint_df)
            st.download_button(
                "📥 Download Maintenance Action Plan PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"PressIQ_Daily_Maintenance_Action_Report_{plant_name}_{maint_start}_{maint_end}.pdf",
                mime="application/pdf",
            )
        else:
            st.error("PDF package missing. Add reportlab to requirements.txt and reboot app.")

        ai_context = build_ai_context(plant_name, maint_start, maint_end, maint_df)
        render_pressiq_ai_assistant(ai_context)
        st.markdown("---")

        if st.button("← Back to Summary", key="back_from_maintenance_bottom"):
            st.session_state["edition_view"] = "summary"
            st.rerun()
        return

    st.markdown("## 1. Maintenance Event Summary")

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.markdown("### Top Affected Editions")
        st.markdown(f"<ul>{bullet_html(top_editions)}</ul>", unsafe_allow_html=True)

        location_lines = []
        if top_folders:
            location_lines.append("Folder: " + ", ".join(top_folders))
        if top_pu:
            location_lines.append("PU: " + ", ".join(top_pu))
        if top_pc:
            location_lines.append("PC: " + ", ".join(top_pc))
        if top_rs:
            location_lines.append("RS: " + ", ".join(top_rs))
        if top_bl:
            location_lines.append("BL: " + ", ".join(top_bl))

        st.markdown("### Reported Hotspots")
        st.markdown(f"<ul>{bullet_html(location_lines)}</ul>", unsafe_allow_html=True)

    

    st.markdown("## 2. Priority Action Areas")

    if issue_waste_kg <= 0:
        st.warning("No waste impact found for selected issue in this date range.")
    else:
        for i, item in enumerate(rec["priorities"], start=1):
            title, action = item

            evidence_parts = []

            if top_pu:
                evidence_parts.append("PU: " + ", ".join(top_pu[:3]))
            if top_pc:
                evidence_parts.append("PC: " + ", ".join(top_pc[:3]))
            if top_reasons:
                evidence_parts.append("Reason: " + ", ".join(top_reasons[:3]))

            evidence = (
                f"{selected_issue} caused {issue_waste_kg:,.0f} KG waste across "
                f"{affected_editions} edition records."
            )

            if evidence_parts:
                evidence += " Reported signals include " + "; ".join(evidence_parts) + "."

            priority_card(
                title=f"Priority {i} — {title}",
                evidence=evidence,
                action=action,
                owner=rec["owner"],
            )
    st.markdown("## 3. Overall Night Shift Remarks Captured")

    if remarks:
        for idx, line in enumerate(remarks, start=1):
            st.markdown(
                f"""
                <div style="
                    background:#f8fafc;
                    border:1px solid #e5e7eb;
                    border-left:5px solid #64748b;
                    border-radius:14px;
                    padding:12px 14px;
                    margin-bottom:8px;
                    font-size:14px;
                    color:#334155;
                ">
                    <b>{idx}.</b> {line}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No night-shift remarks found for the selected issue and date range.")

    st.markdown("## 4. Maintenance Action Plan PDF")

    if REPORTLAB_AVAILABLE:
        pdf_buffer = generate_maintenance_pdf(plant_name, maint_start, maint_end, maint_df)
        st.download_button(
            "📥 Download Maintenance Action Plan PDF",
            data=pdf_buffer.getvalue(),
            file_name=f"PressIQ_Daily_Maintenance_Action_Report_{plant_name}_{maint_start}_{maint_end}.pdf",
            mime="application/pdf",
        )
    else:
        st.error("PDF package missing. Add reportlab to requirements.txt and reboot app.")
        st.markdown("---")

        if st.button("← Back to Summary", key="back_from_maintenance_bottom"):
            st.session_state["edition_view"] = "summary"
            st.rerun()

    ai_context = build_ai_context(plant_name, maint_start, maint_end, maint_df)
    render_pressiq_ai_assistant(ai_context)
    
def render_performance_review_board(df, min_date, max_date, plant_name):

    scroll_to_top()

    st.markdown(f"## Performance Review Board - {plant_name}")

    st.markdown(
        """
        <div style="
            background:#f8fafc;
            border:1px solid #e5e7eb;
            border-left:7px solid #7c3aed;
            border-radius:18px;
            padding:18px;
            margin-bottom:18px;
        ">
            This board is designed for plant head, production manager, and leadership review.
            It identifies edition loss, start-type loss, press-wise waste, and management focus areas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        perf_start = st.date_input(
            "From Date",
            min_date,
            min_value=min_date,
            max_value=max_date,
            key="performance_start_date",
        )

    with c2:
        perf_end = st.date_input(
            "To Date",
            max_date,
            min_value=min_date,
            max_value=max_date,
            key="performance_end_date",
        )

    if perf_start > perf_end:
        st.error("From Date cannot be greater than To Date.")
        return

    perf_df = filter_by_date(df, perf_start, perf_end)

    if perf_df.empty:
        st.warning("No data found for selected performance review date range.")
        return

    total_waste = perf_df["Total Waste MT"].sum()
    segment_df, _ = build_segment_df(perf_df)

    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric("Total Waste", f"{total_waste:,.3f}(MT)")

    with p2:
        st.empty()

    with p3:
        st.empty()

    with p4:
        st.empty()

    st.markdown("### Waste by Category")
    st.dataframe(round_display(segment_df), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## Edition Loss Intelligence")

    work = perf_df.copy()

    if "Total Pages" not in work.columns:
        work["Total Pages"] = 0

    if "GNP/SNP" not in work.columns:
        work["GNP/SNP"] = ""

    edition_perf = (
        work.groupby(["Edition", "Edition Name"], dropna=False)
        .agg(
            Total_Waste_MT=("Total Waste MT", "sum"),
            Runs=("Edition Name", "count"),
            Print_Order=("Print Order", "sum"),
            Total_Pages=("Total Pages", "sum"),
        )
        .reset_index()
    )

    gnp_runs_df = (
        work.assign(
            GNP_Flag=work["GNP/SNP"].astype(str).str.upper().str.strip().isin(["1", "1.0", "GNP"])
        )
        .groupby(["Edition", "Edition Name"], dropna=False)["GNP_Flag"]
        .sum()
        .reset_index()
        .rename(columns={"GNP_Flag": "GNP Runs"})
    )

    edition_perf = edition_perf.merge(
        gnp_runs_df,
        on=["Edition", "Edition Name"],
        how="left",
    )

    edition_perf["GNP Runs"] = edition_perf["GNP Runs"].fillna(0)

    edition_perf["Edition Detail"] = edition_perf.apply(
        lambda r: (
            clean_text_value(r["Edition"]) + " - " + clean_text_value(r["Edition Name"])
            if clean_text_value(r["Edition"]) and clean_text_value(r["Edition Name"])
            else clean_text_value(r["Edition Name"]) or clean_text_value(r["Edition"])
        ),
        axis=1,
    )

    edition_perf = edition_perf.sort_values("Total_Waste_MT", ascending=False)

    edition_display = edition_perf[
        [
            "Edition Detail",
            "Total_Waste_MT",
            "Runs",
            "Print_Order",
            "Total_Pages",
            "GNP Runs",
        ]
    ].rename(
        columns={
            "Total_Waste_MT": "Total Waste MT",
            "Runs": "No. of Runs",
            "Print_Order": "Print Order",
            "Total_Pages": "Total Pages",
        }
    )

    st.dataframe(round_display(edition_display), use_container_width=True, hide_index=True)

    st.markdown("### Edition Drill-down")

    for _, ed_row in edition_perf.head(15).iterrows():
        edition = ed_row["Edition"]
        edition_name = ed_row["Edition Name"]
        edition_label = ed_row["Edition Detail"]

        ed_detail = work[
            (work["Edition"].astype(str) == str(edition)) &
            (work["Edition Name"].astype(str) == str(edition_name))
        ].copy()

        with st.expander(
            f"{edition_label} | Waste: {ed_row['Total_Waste_MT']:,.3f}(MT) | Runs: {ed_row['Runs']}"
        ):
            start_summary = (
                ed_detail.groupby("Type of Start", dropna=False)
                .agg(
                    Runs=("Type of Start", "count"),
                    Waste_MT=("Total Waste MT", "sum"),
                )
                .reset_index()
                .sort_values("Waste_MT", ascending=False)
            )

            start_summary = start_summary.rename(
                columns={
                    "Type of Start": "Start Type",
                    "Waste_MT": "Waste MT",
                }
            )

            st.markdown("#### Start Type Split")
            st.dataframe(round_display(start_summary), use_container_width=True, hide_index=True)

            drill_cols = [
                "Edition Date",
                "Type of Start",
                "Print Order",
                "GNP/SNP",
                "Total Pages",
                "Total Waste MT",
                "Waste Reason",
                "Remarks",
            ]

            drill_cols = [c for c in drill_cols if c in ed_detail.columns]
            drill_df = ed_detail[drill_cols].copy()

            if "Edition Date" in drill_df.columns:
                drill_df["Edition Date"] = pd.to_datetime(
                    drill_df["Edition Date"],
                    errors="coerce",
                ).dt.strftime("%d-%b-%Y")

            st.markdown("#### Date-wise Issue Detail")
            st.dataframe(round_display(drill_df), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## Start Type Waste Review")

    start_type_df = (
        perf_df.groupby("Type of Start", dropna=False)
        .agg(
            Runs=("Type of Start", "count"),
            Waste_MT=("Total Waste MT", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                "Type of Start": "Start Type",
                "Waste_MT": "Waste MT",
            }
        )
        .sort_values("Waste MT", ascending=False)
    )

    st.dataframe(round_display(start_type_df), use_container_width=True, hide_index=True)

    s1, s2, s3 = st.columns(3)

    def start_type_metric(label, search_terms, col):
        temp = perf_df[
            perf_df["Type of Start"].astype(str).str.lower().apply(
                lambda x: any(term in x for term in search_terms)
            )
        ]
        runs = len(temp)
        waste = temp["Total Waste MT"].sum()
        with col:
            st.metric(label, f"{waste:,.3f}(MT)", f"{runs} Runs")

    start_type_metric("Cold Start Waste", ["cold"], s1)
    start_type_metric("Warm Planned Waste", ["warm-planned", "warm planned"], s2)
    start_type_metric("Warm Unplanned Waste", ["warm- unplanned", "warm-unplanned", "warm unplanned"], s3)

    st.markdown("---")
    st.markdown("## Press Wise Waste Review")

    press_source_col = "Folder"

    if press_source_col not in perf_df.columns:
        perf_df[press_source_col] = "Not specified"

    press_df = (
        perf_df.groupby(press_source_col, dropna=False)
        .agg(
            Runs=(press_source_col, "count"),
            Total_Waste_MT=("Total Waste MT", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                press_source_col: "Press",
                "Total_Waste_MT": "Total Waste MT",
            }
        )
        .sort_values("Total Waste MT", ascending=False)
    )

    press_df["Avg Waste / Run MT"] = press_df.apply(
        lambda r: r["Total Waste MT"] / r["Runs"] if r["Runs"] else 0,
        axis=1,
    )

    st.dataframe(round_display(press_df), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## Management Insight Preview")

    top_edition_text = edition_perf.iloc[0]["Edition Detail"] if not edition_perf.empty else "Not available"
    top_edition_waste = edition_perf.iloc[0]["Total_Waste_MT"] if not edition_perf.empty else 0

    top_press_text = press_df.iloc[0]["Press"] if not press_df.empty else "Not available"
    top_press_waste = press_df.iloc[0]["Total Waste MT"] if not press_df.empty else 0

    top_start_text = start_type_df.iloc[0]["Start Type"] if not start_type_df.empty else "Not available"
    top_start_waste = start_type_df.iloc[0]["Waste MT"] if not start_type_df.empty else 0

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-left:7px solid #7c3aed;
                border-radius:18px;
                padding:18px;
                margin-bottom:12px;
            ">
                <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                    Top Edition Loss
                </div>
                <div style="font-size:14px;color:#334155;">
                    <b>{top_edition_text}</b> generated <b>{top_edition_waste:,.3f}(MT)</b> waste in the selected period.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-left:7px solid #2563eb;
                border-radius:18px;
                padding:18px;
                margin-bottom:12px;
            ">
                <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                    Top Press Loss
                </div>
                <div style="font-size:14px;color:#334155;">
                    <b>{top_press_text}</b> generated <b>{top_press_waste:,.3f}(MT)</b> waste.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-left:7px solid #f97316;
                border-radius:18px;
                padding:18px;
                margin-bottom:12px;
            ">
                <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                    Start Type Focus
                </div>
                <div style="font-size:14px;color:#334155;">
                    <b>{top_start_text}</b> contributed <b>{top_start_waste:,.3f}(MT)</b> waste.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-left:7px solid #16a34a;
                border-radius:18px;
                padding:18px;
                margin-bottom:12px;
            ">
                <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                    Review Focus
                </div>
                <div style="font-size:14px;color:#334155;">
                    Management should review high-waste editions along with print order, GNP/SNP, start type, page load, and press-wise run count before deciding improvement action.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def run_edition_waste_analyzer():
    if "edition_view" not in st.session_state:
        st.session_state["edition_view"] = "input"

    if "edition_analysis_ready" not in st.session_state:
        st.session_state["edition_analysis_ready"] = False

    if st.session_state.get("edition_analysis_ready", False):
        df = st.session_state["edition_df"]
        plant_name = st.session_state["edition_plant_name"]
        min_date = st.session_state["edition_min_date"]
        max_date = st.session_state["edition_max_date"]

        if st.session_state["edition_view"] == "summary":
            render_summary_page(
                df,
                plant_name,
                st.session_state["edition_start_date"],
                st.session_state["edition_end_date"],
                min_date,
                max_date,
            )
            return

        if st.session_state["edition_view"] == "maintenance":
            render_maintenance_action_desk(df, min_date, max_date, plant_name)
            return

        if st.session_state["edition_view"] == "performance":
            render_performance_review_board(df, min_date, max_date, plant_name)
            return

    st.markdown("### Upload Edition Wise Wastage File")

    uploaded_file = st.file_uploader(
        "Upload Edition Wise Wastage Excel file",
        type=["xlsx"],
        key="edition_waste_upload",
    )

    if not uploaded_file:
        st.info("Upload edition-wise wastage tracker file to start analysis.")
        return

    xls = pd.ExcelFile(uploaded_file)

    available_sheets = [
        s for s in xls.sheet_names
        if str(s).strip().upper() not in ["MASTER", "SHEET1"]
    ]

    if not available_sheets:
        st.error("No valid plant sheet found in uploaded file.")
        return

    default_index = available_sheets.index("AIR") if "AIR" in available_sheets else 0

    sheet_name = st.selectbox(
        "Detected Plant / Select Plant Sheet",
        available_sheets,
        index=default_index,
    )

    df = read_edition_file(uploaded_file, sheet_name)

    if df.empty:
        st.error("No valid edition-wise data found in selected sheet.")
        return

    plant_name = sheet_name.upper()
    st.success(f"Plant detected: {plant_name}")

    min_date = df["Edition Date"].min().date()
    max_date = df["Edition Date"].max().date()

    st.markdown("### Select Date Range")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "From Date",
            min_date,
            min_value=min_date,
            max_value=max_date,
        )

    with col2:
        end_date = st.date_input(
            "To Date",
            max_date,
            min_value=min_date,
            max_value=max_date,
        )

    if start_date > end_date:
        st.error("From Date cannot be greater than To Date.")
        return

    run_analysis = st.button("Run Edition Wise Wastage Analysis")

    if run_analysis:
        st.session_state["edition_df"] = df
        st.session_state["edition_plant_name"] = plant_name
        st.session_state["edition_min_date"] = min_date
        st.session_state["edition_max_date"] = max_date
        st.session_state["edition_start_date"] = start_date
        st.session_state["edition_end_date"] = end_date
        st.session_state["edition_analysis_ready"] = True
        st.session_state["edition_view"] = "summary"
        st.rerun()

    st.info("Select date range and click 'Run Edition Wise Wastage Analysis' to view output.")
