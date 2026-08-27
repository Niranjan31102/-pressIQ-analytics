import base64

import pandas as pd
import streamlit as st

from ui_theme import module_hero
from modules.avp_engine import process_report, finalize_calculations
from modules.avp_report import generate_management_png


def _css():
    st.markdown(
        """
        <style>
        .avp-steps {display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:8px 0 22px;}
        .avp-step {padding:16px 18px;border-radius:18px;background:linear-gradient(145deg,#ffffff,#f4f8ff);border:1px solid #d8e3f3;box-shadow:0 10px 25px rgba(15,23,42,.06);}
        .avp-step.on {border-color:#38bdf8;background:linear-gradient(145deg,#ffffff,#eef8ff);box-shadow:0 12px 30px rgba(37,99,235,.15);}
        .avp-n {font-size:12px;font-weight:900;color:#2563eb}.avp-t {font-size:16px;font-weight:900;color:#0f172a;margin-top:4px}.avp-s {font-size:12px;color:#64748b;margin-top:3px}
        .avp-info {display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}.avp-k {background:#fff;border:1px solid #dbe5f1;border-radius:16px;padding:14px;text-align:center;box-shadow:0 8px 20px rgba(15,23,42,.05)}
        .avp-kl {font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800}.avp-kv {font-size:22px;color:#0f172a;font-weight:950;margin-top:4px}
        .avp-title {font-size:18px;font-weight:950;color:#0f172a;margin:16px 0 8px}.avp-subtle {font-size:12px;color:#64748b;margin:-3px 0 12px}
        .avp-note {background:#fff7ed;border:1px solid #fed7aa;border-left:5px solid #f97316;border-radius:14px;padding:12px 14px;margin:10px 0;color:#9a3412;font-weight:700}
        .avp-ready {background:#ecfdf5;border:1px solid #a7f3d0;border-left:5px solid #10b981;border-radius:14px;padding:12px 14px;margin:10px 0;color:#065f46;font-weight:800}
        .avp-warning-soft {background:#fffbeb;border:1px solid #fde68a;border-left:5px solid #f59e0b;border-radius:14px;padding:12px 14px;margin:10px 0;color:#92400e;font-weight:700}
        .avp-editor-card {background:linear-gradient(145deg,#fff,#f8fbff);border:1px solid #dbe5f1;border-radius:18px;padding:16px 18px;margin:10px 0 14px;box-shadow:0 10px 25px rgba(15,23,42,.06)}
        .avp-editor-head {display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.avp-editor-pub {font-size:18px;font-weight:950;color:#0f172a}.avp-editor-machine {font-size:12px;font-weight:800;color:#2563eb;background:#eff6ff;border:1px solid #bfdbfe;border-radius:999px;padding:5px 10px}
        .avp-metrics {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}.avp-mini {border:1px solid #e2e8f0;border-radius:12px;padding:10px 12px;background:#fff}.avp-mini-label {color:#64748b;font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.06em}.avp-mini-value {color:#0f172a;font-size:17px;font-weight:950;margin-top:2px}
        .avp-footer {text-align:center;color:#94a3b8;font-size:12px;margin:28px 0 8px}.stButton>button {min-height:48px}.avp-preview img {width:100%;border-radius:18px;box-shadow:0 18px 45px rgba(15,23,42,.12);border:1px solid #dbe5f1}
        @media(max-width:800px){.avp-steps,.avp-info,.avp-metrics{grid-template-columns:1fr 1fr}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init():
    defaults = {
        "avp_stage": "upload",
        "avp_raw": None,
        "avp_work": None,
        "avp_type": None,
        "avp_png": None,
        "avp_reason_row": None,
        "avp_reason_loaded_row": None,
        "avp_reason_text": "",
        "avp_uploaded_signature": None,
        "avp_busy": None,
        "avp_just_saved_row": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _action_css():
    green_rules = []
    if st.session_state.get("avp_type") == "Main":
        green_rules.append(".st-key-avp_main button")
    if st.session_state.get("avp_type") == "Supplement":
        green_rules.append(".st-key-avp_supp button")
    if st.session_state.get("avp_busy") == "process":
        green_rules.append(".st-key-avp_process button")
    if st.session_state.get("avp_busy") == "generate":
        green_rules.append(".st-key-avp_generate button")
    saved_row = st.session_state.get("avp_just_saved_row")
    if saved_row is not None:
        green_rules.append(f".st-key-avp_save_reason_{saved_row} button")

    if green_rules:
        selectors = ",".join(green_rules)
        st.markdown(
            f"""
            <style>
            {selectors} {{
                background:#16a34a !important;
                border-color:#16a34a !important;
                color:white !important;
                box-shadow:0 8px 20px rgba(22,163,74,.22) !important;
            }}
            {selectors}:hover {{
                background:#15803d !important;
                border-color:#15803d !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


def _steps():
    stage = st.session_state.avp_stage
    order = ["upload","review","report"]
    current_index = order.index(stage)
    labels = [("01","Upload Report"),("02","Working Table"),("03","Final Report")]
    html = '<div class="avp-steps">'
    for index, (number, title) in enumerate(labels):
        css_class = "avp-step on" if index == current_index else "avp-step"
        status = "Active" if index == current_index else "Complete" if index < current_index else "Pending"
        html += f'<div class="{css_class}"><div class="avp-n">{number}</div><div class="avp-t">{title}</div><div class="avp-s">{status}</div></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _summary_cards(df):
    dates = pd.to_datetime(df["Edition Date"], errors="coerce").dropna()
    issue_date = dates.iloc[0].strftime("%d %b %Y") if not dates.empty else "—"
    main_count = int((df["_type"] == "MAIN").sum()) if "_type" in df else 0
    supplement_count = int((df["_type"] == "SUPPLEMENT").sum()) if "_type" in df else 0
    st.markdown(f'''<div class="avp-info"><div class="avp-k"><div class="avp-kl">Issue Date</div><div class="avp-kv">{issue_date}</div></div><div class="avp-k"><div class="avp-kl">Main Editions</div><div class="avp-kv">{main_count}</div></div><div class="avp-k"><div class="avp-kl">Supplement</div><div class="avp-kv">{supplement_count}</div></div><div class="avp-k"><div class="avp-kl">Total Editions</div><div class="avp-kv">{main_count + supplement_count}</div></div></div>''', unsafe_allow_html=True)


def _safe_reason(value):
    text = str(value).strip() if value is not None else ""
    return "NA" if text.upper() in {"", "NA", "NAN", "NONE"} else text


def _has_reason(value):
    return _safe_reason(value) != "NA"


def _report_ready_df(df):
    ready = df.copy()
    ready["Reason for Extra Waste"] = ready["Reason for Extra Waste"].apply(_safe_reason)
    return ready


def _upload():
    st.markdown('<div class="avp-title">Upload Production Report</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Production Report",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
        key="avp_upload_v1",
    )
    if uploaded_file is None:
        return

    signature = f"{uploaded_file.name}:{getattr(uploaded_file, 'size', '')}"
    if st.session_state.avp_uploaded_signature != signature:
        st.session_state.avp_uploaded_signature = signature
        st.session_state.avp_type = None
        st.session_state.avp_work = None
        st.session_state.avp_png = None
        st.session_state.avp_busy = None

    try:
        uploaded_file.seek(0)
        general = pd.read_excel(uploaded_file, sheet_name="General")
        uploaded_file.seek(0)
        type_col = next((c for c in general.columns if str(c).strip().upper().replace(" ", "") in ["MAIN/SUPPLEMENT", "MAINSUPPLEMENT"]), None)
        date_col = next((c for c in general.columns if str(c).strip().upper() in ["ISSUE DATE", "EDITION DATE"]), None)
        preview = pd.DataFrame({
            "Edition Date": general[date_col] if date_col else pd.NaT,
            "_type": general[type_col].astype(str).str.strip().str.upper() if type_col else "",
        })
        _summary_cards(preview)
    except Exception as error:
        st.error(f"Unable to read report summary: {error}")
        return

    st.markdown('<div class="avp-title">Select Production Type</div>', unsafe_allow_html=True)
    col_main, col_supplement = st.columns(2)

    with col_main:
        main_label = "✓  MAIN" if st.session_state.avp_type == "Main" else "MAIN"
        if st.button(main_label, use_container_width=True, key="avp_main"):
            st.session_state.avp_type = "Main"
            st.rerun()

    with col_supplement:
        supp_label = "✓  SUPPLEMENT" if st.session_state.avp_type == "Supplement" else "SUPPLEMENT"
        if st.button(supp_label, use_container_width=True, key="avp_supp"):
            st.session_state.avp_type = "Supplement"
            st.rerun()

    if st.session_state.avp_busy == "process":
        st.button("Processing Report...", use_container_width=True, key="avp_process", disabled=True)
        try:
            with st.spinner("Processing report..."):
                uploaded_file.seek(0)
                all_df = process_report(uploaded_file)
                selected = all_df.copy()
                uploaded_file.seek(0)
                general = pd.read_excel(uploaded_file, sheet_name="General")
                type_col = next((c for c in general.columns if str(c).strip().upper().replace(" ", "") in ["MAIN/SUPPLEMENT", "MAINSUPPLEMENT"]), None)
                if type_col:
                    wanted = st.session_state.avp_type.upper()
                    valid_rows = set(general[general[type_col].astype(str).str.strip().str.upper() == wanted].index.astype(str))
                    selected = selected[selected["Row ID"].isin(valid_rows)]
                if selected.empty:
                    raise ValueError(f"No {st.session_state.avp_type} editions found.")
                st.session_state.avp_work = selected.reset_index(drop=True)
                st.session_state.avp_stage = "review"
                st.session_state.avp_png = None
                st.session_state.avp_reason_row = None
                st.session_state.avp_reason_loaded_row = None
                st.session_state.avp_reason_text = ""
                st.session_state.avp_busy = None
                st.session_state.avp_just_saved_row = None
            st.rerun()
        except Exception as error:
            st.session_state.avp_busy = None
            st.error(str(error))
    else:
        if st.button(
            "Process Report",
            type="primary",
            use_container_width=True,
            key="avp_process",
            disabled=st.session_state.avp_type is None,
        ):
            st.session_state.avp_busy = "process"
            st.rerun()

def _display_working_table(calc):
    display = calc.copy()
    display["Edition Date"] = pd.to_datetime(display["Edition Date"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
    reason_added = display["Reason for Extra Waste"].apply(_has_reason)
    display["Reason"] = "NA"
    display.loc[(display["Extra Waste"].fillna(0) > 0) & ~reason_added, "Reason"] = "Add Reason"
    display.loc[(display["Extra Waste"].fillna(0) > 0) & reason_added, "Reason"] = "✓ Added"
    table = display[["Edition Date","Machine","Machine In-charge","Publication","PO","Predicted Waste","Predicted %","Actual Waste","Actual %","Extra Waste","Reason"]].copy()
    for column in ["PO","Predicted Waste","Actual Waste","Extra Waste"]:
        table[column] = pd.to_numeric(table[column], errors="coerce")
    def highlight_row(row):
        extra = pd.to_numeric(row.get("Extra Waste"), errors="coerce")
        return ["background-color: #fff7ed"] * len(row) if pd.notna(extra) and extra > 0 else [""] * len(row)
    styled = table.style.apply(highlight_row, axis=1).format({
        "PO":lambda v:"—" if pd.isna(v) else f"{int(v):,}","Predicted Waste":lambda v:"—" if pd.isna(v) else f"{int(v):,}","Predicted %":lambda v:"—" if pd.isna(v) else f"{v:.2f}%",
        "Actual Waste":lambda v:"—" if pd.isna(v) else f"{int(v):,}","Actual %":lambda v:"—" if pd.isna(v) else f"{v:.2f}%","Extra Waste":lambda v:"—" if pd.isna(v) else f"{int(v):,}",})
    st.dataframe(styled, use_container_width=True, hide_index=True, height=min(680,92+len(table)*42))


def _publication_exceptions(df):
    unmatched = df[df["Match Status"] == "Review Required"]
    if unmatched.empty: return
    st.markdown(f'<div class="avp-note">{len(unmatched)} publication(s) were not matched automatically. Only these publication values are editable.</div>', unsafe_allow_html=True)
    for index in unmatched.index:
        df.at[index,"Publication"] = st.text_input(f"Publication — {df.at[index,'Product Name']}", value=str(df.at[index,"Publication"]), key=f"avp_pub_{index}")


def _manual_prediction_exceptions(df):
    manual = df[df["Manual Prediction Required"] == True]
    if manual.empty: return
    st.markdown(f'<div class="avp-note">Manual predicted waste is required for {len(manual)} edition(s) because the page count is outside configured Prediction Master ranges.</div>', unsafe_allow_html=True)
    st.markdown("**Manual Predicted Waste — only exception rows are editable**")
    for index in manual.index:
        existing = df.at[index,"Predicted Waste"]; default_value = int(existing) if pd.notna(existing) else 0
        entered = st.number_input(f"{df.at[index,'Publication']} | {df.at[index,'Machine']} | {df.at[index,'Pages']} pages", min_value=0, value=default_value, step=50, key=f"avp_manual_{index}")
        df.at[index,"Predicted Waste"] = entered if entered > 0 else pd.NA


def _save_reason_callback(chosen):
    df = st.session_state.avp_work
    entered = str(st.session_state.get("avp_reason_text", "")).strip()
    df.at[chosen, "Reason for Extra Waste"] = entered or "NA"
    st.session_state.avp_work = df
    st.session_state.avp_reason_loaded_row = chosen
    st.session_state.avp_reason_text = ""
    st.session_state.avp_just_saved_row = chosen


def _clear_reason_callback(chosen):
    df = st.session_state.avp_work
    df.at[chosen, "Reason for Extra Waste"] = "NA"
    st.session_state.avp_work = df
    st.session_state.avp_reason_loaded_row = chosen
    st.session_state.avp_reason_text = ""
    st.session_state.avp_just_saved_row = None


def _reason_editor(df, calc):
    extra_rows = calc[calc["Extra Waste"].fillna(0) > 0]
    st.markdown('<div class="avp-title">Reason Editor</div>', unsafe_allow_html=True)
    st.markdown('<div class="avp-subtle">Select an edition with extra waste. A green tick shows editions where a reason has already been saved.</div>', unsafe_allow_html=True)
    if extra_rows.empty:
        st.markdown('<div class="avp-ready">No edition has extra waste above predicted waste.</div>', unsafe_allow_html=True)
        return

    options = list(extra_rows.index)
    if st.session_state.avp_reason_row not in options:
        st.session_state.avp_reason_row = options[0]

    def option_label(index):
        base = f"{calc.at[index,'Publication']} • {calc.at[index,'Machine']} • Extra {int(calc.at[index,'Extra Waste']):,}"
        return f"✅ {base}  (Extra waste reason has been added)" if _has_reason(df.at[index, "Reason for Extra Waste"]) else f"⚠️ {base}"

    chosen = st.selectbox(
        "Select edition to enter / edit reason",
        options,
        index=options.index(st.session_state.avp_reason_row),
        format_func=option_label,
        key="avp_reason_selector",
    )

    if chosen != st.session_state.avp_reason_row:
        st.session_state.avp_just_saved_row = None
    st.session_state.avp_reason_row = chosen

    if st.session_state.avp_reason_loaded_row != chosen:
        saved = _safe_reason(df.at[chosen, "Reason for Extra Waste"])
        st.session_state.avp_reason_text = "" if saved == "NA" else saved
        st.session_state.avp_reason_loaded_row = chosen
        st.session_state.avp_just_saved_row = None

    predicted = calc.at[chosen, "Predicted Waste"]
    actual = calc.at[chosen, "Actual Waste"]
    extra = calc.at[chosen, "Extra Waste"]
    po = calc.at[chosen, "PO"]

    st.markdown(
        f'''<div class="avp-editor-card"><div class="avp-editor-head"><div class="avp-editor-pub">{calc.at[chosen,'Publication']}</div><div class="avp-editor-machine">{calc.at[chosen,'Machine']}</div></div><div class="avp-metrics"><div class="avp-mini"><div class="avp-mini-label">PO</div><div class="avp-mini-value">{int(po):,}</div></div><div class="avp-mini"><div class="avp-mini-label">Predicted</div><div class="avp-mini-value">{'—' if pd.isna(predicted) else f'{int(predicted):,}'}</div></div><div class="avp-mini"><div class="avp-mini-label">Actual</div><div class="avp-mini-value">{int(actual):,}</div></div><div class="avp-mini"><div class="avp-mini-label">Extra</div><div class="avp-mini-value">{int(extra):,}</div></div></div></div>''',
        unsafe_allow_html=True,
    )

    st.text_area("Reason for Extra Waste", height=190, key="avp_reason_text", placeholder="Enter complete operational reason. No practical word limit.")
    save_col, clear_col, _ = st.columns([1, 1, 4])

    with save_col:
        label = "✓ Saved" if st.session_state.avp_just_saved_row == chosen else "Save Reason"
        st.button(label, key=f"avp_save_reason_{chosen}", on_click=_save_reason_callback, args=(chosen,))

    with clear_col:
        st.button("Clear Reason", key=f"avp_clear_reason_{chosen}", on_click=_clear_reason_callback, args=(chosen,))

def _review():
    df = st.session_state.avp_work
    if df is None or df.empty:
        st.session_state.avp_stage = "upload"
        st.rerun()

    st.markdown('<div class="avp-title">Production Working Table</div>', unsafe_allow_html=True)
    st.markdown('<div class="avp-subtle">Review calculated waste, handle only genuine exceptions, and record operational reasons where needed.</div>', unsafe_allow_html=True)
    _publication_exceptions(df)
    _manual_prediction_exceptions(df)
    st.session_state.avp_work = df

    calc = finalize_calculations(df)
    _display_working_table(calc)
    _reason_editor(df, calc)

    calc = finalize_calculations(st.session_state.avp_work)
    missing_manual = calc["Predicted Waste"].isna().any()
    missing_reason_count = int(((calc["Extra Waste"].fillna(0) > 0) & ~calc["Reason for Extra Waste"].apply(_has_reason)).sum())

    if missing_manual:
        st.markdown('<div class="avp-note">Complete all manual predicted-waste exception rows before generating the final report.</div>', unsafe_allow_html=True)
    elif missing_reason_count > 0:
        st.markdown(f'<div class="avp-warning-soft">{missing_reason_count} extra-waste edition(s) currently have no reason.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="avp-ready">Working table is ready for the management report.</div>', unsafe_allow_html=True)

    back_col, report_col = st.columns([1, 2])
    with back_col:
        if st.button("← Back to Upload", use_container_width=True):
            st.session_state.avp_stage = "upload"
            st.session_state.avp_busy = None
            st.rerun()

    with report_col:
        if st.session_state.avp_busy == "generate":
            st.button("Generating Final Report...", use_container_width=True, key="avp_generate", disabled=True)
            try:
                with st.spinner("Generating final management report..."):
                    ready_df = _report_ready_df(st.session_state.avp_work)
                    st.session_state.avp_work = ready_df
                    st.session_state.avp_png = generate_management_png(ready_df, st.session_state.avp_type)
                    st.session_state.avp_stage = "report"
                    st.session_state.avp_busy = None
                st.rerun()
            except Exception as error:
                st.session_state.avp_busy = None
                st.error(str(error))
        else:
            if st.button("Generate Final Report", type="primary", use_container_width=True, disabled=missing_manual, key="avp_generate"):
                st.session_state.avp_busy = "generate"
                st.session_state.avp_just_saved_row = None
                st.rerun()

def _report():
    df = st.session_state.avp_work
    png = st.session_state.avp_png

    if df is None:
        st.session_state.avp_stage = "upload"
        st.rerun()

    if png is None:
        ready_df = _report_ready_df(df)
        png = generate_management_png(ready_df, st.session_state.avp_type)
        st.session_state.avp_png = png

    st.markdown('<div class="avp-title">Final Management Report</div>', unsafe_allow_html=True)
    encoded = base64.b64encode(png).decode()
    st.markdown(f'<div class="avp-preview"><img src="data:image/png;base64,{encoded}"></div>', unsafe_allow_html=True)

    col_back, col_download, col_whatsapp = st.columns(3)
    with col_back:
        if st.button("← Working Table", use_container_width=True):
            st.session_state.avp_stage = "review"
            st.session_state.avp_png = None
            st.rerun()

    with col_download:
        st.download_button(
            "Download PNG",
            data=png,
            file_name=f"PressIQ_Actual_vs_Predicted_{st.session_state.avp_type}.png",
            mime="image/png",
            use_container_width=True,
        )

    with col_whatsapp:
        st.markdown(
            r'''
            <a class="avp-whatsapp" href="https://web.whatsapp.com/" target="_blank" rel="noopener noreferrer">
              <svg viewBox="0 0 32 32" aria-hidden="true">
                <path fill="currentColor" d="M16.04 3C9.42 3 4.05 8.26 4.05 14.75c0 2.27.66 4.39 1.8 6.18L4 28l7.3-1.88a12.2 12.2 0 0 0 4.74.95c6.62 0 11.99-5.26 11.99-11.75S22.66 3 16.04 3Zm0 21.9c-1.48 0-2.92-.39-4.18-1.12l-.3-.17-4.33 1.12 1.16-4.13-.2-.31a9.5 9.5 0 0 1-1.5-5.13c0-5.2 4.2-9.43 9.38-9.43 5.17 0 9.38 4.23 9.38 9.43 0 5.2-4.2 9.74-9.4 9.74Zm5.15-7.08c-.28-.14-1.67-.82-1.93-.91-.26-.1-.45-.14-.64.14-.19.28-.73.91-.9 1.1-.16.19-.33.21-.61.07-.28-.14-1.19-.44-2.27-1.4-.84-.75-1.4-1.67-1.57-1.95-.16-.28-.02-.43.12-.57.13-.13.28-.33.42-.49.14-.16.19-.28.28-.47.1-.19.05-.35-.02-.49-.07-.14-.64-1.54-.88-2.1-.23-.56-.47-.48-.64-.49h-.55c-.19 0-.49.07-.75.35-.26.28-.99.96-.99 2.35 0 1.38 1.02 2.72 1.16 2.91.14.19 2 3.03 4.85 4.25.68.29 1.21.46 1.62.59.68.21 1.3.18 1.79.11.55-.08 1.67-.68 1.91-1.34.24-.66.24-1.22.17-1.34-.07-.12-.26-.19-.54-.33Z"/>
              </svg>
              <span>Open WhatsApp Web</span>
            </a>
            <style>
              .avp-whatsapp{width:100%;min-height:48px;display:flex;align-items:center;justify-content:center;gap:9px;background:#25D366;color:white!important;text-decoration:none!important;border-radius:8px;font-weight:700;border:1px solid #1fb957;box-shadow:0 6px 16px rgba(37,211,102,.18)}
              .avp-whatsapp:hover{background:#1ebe5d;color:white!important}
              .avp-whatsapp svg{width:22px;height:22px;flex:0 0 22px}
            </style>
            ''',
            unsafe_allow_html=True,
        )

def run_actual_vs_predicted_waste():
    _init(); _css(); _action_css(); module_hero("Actual vs Predicted Waste", ""); _steps()
    if st.session_state.avp_stage == "upload": _upload()
    elif st.session_state.avp_stage == "review": _review()
    else: _report()
    st.markdown('<div class="avp-footer">Powered by PressIQ AI · Designed for Production Intelligence</div>', unsafe_allow_html=True)
