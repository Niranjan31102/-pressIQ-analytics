from io import BytesIO
import pandas as pd
from PIL import Image
from modules.avp_engine import finalize_calculations

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


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


def _machine_bucket(row):
    display_machine = str(row.get("Machine", "")).upper().strip()
    calc_machine = str(row.get("Calc Machine", "")).upper().strip()

    if "PRESS-4" in display_machine or "PRESS 4" in display_machine:
        return "PRESS-4 / COL B"
    if display_machine == "CROMOMAN-C" or calc_machine == "CROMOMAN-C":
        return "CROMO"
    if display_machine == "COLORMAN-A" or calc_machine == "COLORMAN-A":
        return "COL A"
    if display_machine == "COLORMAN-B" or calc_machine == "COLORMAN-B":
        return "COL B"

    return display_machine or calc_machine or "OTHER"


def _build_summary(data):
    work = data.copy()
    work["_summary_machine"] = work.apply(_machine_bucket, axis=1)

    order = ["CROMO", "COL A", "COL B", "PRESS-4 / COL B"]
    machines = []

    for name in order:
        group = work[work["_summary_machine"] == name]
        if group.empty:
            continue

        po = pd.to_numeric(group["PO"], errors="coerce").fillna(0).sum()
        pred = pd.to_numeric(group["Predicted Waste"], errors="coerce").sum(min_count=1)
        act = pd.to_numeric(group["Actual Waste"], errors="coerce").fillna(0).sum()

        machines.append(
            {
                "name": name,
                "predicted": round(pred / po * 100, 2) if po and pd.notna(pred) else None,
                "actual": round(act / po * 100, 2) if po else None,
            }
        )

    total_po = pd.to_numeric(work["PO"], errors="coerce").fillna(0).sum()
    total_pred = pd.to_numeric(work["Predicted Waste"], errors="coerce").sum(min_count=1)
    total_act = pd.to_numeric(work["Actual Waste"], errors="coerce").fillna(0).sum()

    overall = {
        "predicted": round(total_pred / total_po * 100, 2)
        if total_po and pd.notna(total_pred)
        else None,
        "actual": round(total_act / total_po * 100, 2)
        if total_po
        else None,
    }

    return machines, overall


def _render_html(data, report_type):
    machines, overall = _build_summary(data)

    issue_date = "—"
    if "Edition Date" in data.columns and data["Edition Date"].notna().any():
        issue_date = pd.to_datetime(data["Edition Date"].dropna().iloc[0]).strftime("%d %B %Y")

    shift = "MAIN SHIFT" if str(report_type).strip().upper() == "MAIN" else "SUPPLEMENT"

    rows = []
    for _, r in data.iterrows():
        pred_pct = r.get("Predicted %")
        act_pct = r.get("Actual %")
        extra = r.get("Extra Waste")

        act_class = "bad" if pd.notna(pred_pct) and pd.notna(act_pct) and float(act_pct) > float(pred_pct) else ""
        extra_class = "bad" if pd.notna(extra) and float(extra) > 0 else ""

        rows.append(
            f"""
            <tr>
                <td>{pd.to_datetime(r['Edition Date']).strftime('%d/%m/%Y') if pd.notna(r['Edition Date']) else '—'}</td>
                <td>{r.get('Machine','—')}</td>
                <td>{r.get('Machine In-charge','—')}</td>
                <td>{r.get('Publication','—')}</td>
                <td>{_fmt_int(r.get('PO'))}</td>
                <td>{_fmt_int(r.get('Predicted Waste'))}</td>
                <td class="pred">{_fmt_pct(r.get('Predicted %'))}</td>
                <td>{_fmt_int(r.get('Actual Waste'))}</td>
                <td class="{act_class}">{_fmt_pct(r.get('Actual %'))}</td>
                <td class="{extra_class}">{_fmt_int(r.get('Extra Waste'))}</td>
                <td class="reason">{_safe_reason(r.get('Reason for Extra Waste','NA'))}</td>
            </tr>
            """
        )

    pred_metrics = []
    act_metrics = []

    for m in machines:
        label = "PRESS-4 / COL B %" if m["name"] == "PRESS-4 / COL B" else f"{m['name']} %"
        pred_metrics.append(
            f"""
            <div class="metric">
                <div class="metric-label">{label}</div>
                <div class="metric-value pred">{'—' if m['predicted'] is None else f"{m['predicted']:.2f}%"} </div>
            </div>
            """
        )
        act_metrics.append(
            f"""
            <div class="metric">
                <div class="metric-label">{label}</div>
                <div class="metric-value actual">{'—' if m['actual'] is None else f"{m['actual']:.2f}%"} </div>
            </div>
            """
        )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        * {{
          box-sizing: border-box;
          font-family: Arial, Helvetica, sans-serif;
        }}
        body {{
          margin: 0;
          background: white;
          color: #0f172a;
        }}
        .report {{
          width: 1536px;
          padding: 0;
          background: white;
        }}
        .header {{
          background: linear-gradient(90deg,#061a3f,#08275c);
          color: white;
          padding: 24px 34px 20px;
          display: grid;
          grid-template-columns: 260px 1fr 260px;
          align-items: center;
          min-height: 138px;
        }}
        .brand {{
          display: flex;
          align-items: center;
          gap: 16px;
          font-weight: 700;
          font-size: 22px;
        }}
        .piq {{
          font-size: 54px;
          font-weight: 800;
          letter-spacing: -3px;
        }}
        .title {{
          text-align: center;
        }}
        .title h1 {{
          margin: 0;
          font-size: 40px;
          line-height: 1.1;
          font-weight: 800;
        }}
        .shift {{
          margin-top: 15px;
          font-size: 18px;
          font-weight: 700;
          color: #dbeafe;
        }}
        .header-spacer {{
          min-height: 1px;
        }}
        .content {{
          padding: 26px 28px 22px;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
        }}
        th {{
          background: #0b2f63;
          color: white;
          border: 1px solid #4e6f9d;
          font-weight: 800;
          font-size: 16px;
          line-height: 1.2;
          padding: 12px 8px;
          text-align: center;
          vertical-align: middle;
        }}
        td {{
          border: 1px solid #d8e1ec;
          padding: 14px 10px;
          font-size: 16px;
          line-height: 1.3;
          font-weight: 700;
          text-align: center;
          vertical-align: middle;
          background: white;
        }}
        tbody tr:nth-child(even) td {{
          background: #f8fafc;
        }}
        td.reason {{
          text-align: left;
          font-size: 16px;
          font-weight: 600;
          white-space: normal;
          word-break: normal;
          overflow-wrap: anywhere;
        }}
        .pred {{
          color: #1565d8;
          font-weight: 800;
        }}
        .bad {{
          color: #e53935;
          font-weight: 800;
        }}
        .summary-grid {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 22px;
          margin-top: 28px;
        }}
        .summary-card {{
          border: 1px solid #d8e1ec;
          border-radius: 16px;
          overflow: hidden;
          background: white;
        }}
        .summary-head {{
          background: #0b2f63;
          color: white;
          padding: 14px 18px;
          font-size: 18px;
          font-weight: 800;
        }}
        .summary-body {{
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 1fr 170px;
          align-items: stretch;
          min-height: 150px;
        }}
        .metric {{
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 18px 8px;
          border-right: 1px solid #e5e7eb;
        }}
        .metric-label {{
          font-size: 15px;
          font-weight: 800;
          text-align: center;
          line-height: 1.2;
        }}
        .metric-value {{
          margin-top: 12px;
          font-size: 30px;
          font-weight: 800;
        }}
        .metric-value.actual {{
          color: #087a57;
        }}
        .total-box {{
          margin: 14px;
          border-radius: 14px;
          background: #061a3f;
          color: white;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          padding: 12px;
        }}
        .total-box.actual {{
          background: #075f46;
        }}
        .total-label {{
          font-size: 14px;
          font-weight: 800;
        }}
        .total-value {{
          margin-top: 10px;
          font-size: 34px;
          font-weight: 800;
        }}
        .w-date {{ width: 8%; }}
        .w-machine {{ width: 9%; }}
        .w-incharge {{ width: 11%; }}
        .w-pub {{ width: 8%; }}
        .w-po {{ width: 7%; }}
        .w-num {{ width: 7%; }}
        .w-extra {{ width: 8%; }}
        .w-reason {{ width: 28%; }}
      </style>
    </head>
    <body>
      <div class="report">
        <div class="header">
          <div class="brand">
            <div class="piq">PIQ</div>
            <div>PressIQ</div>
          </div>
          <div class="title">
            <h1>Actual vs Predicted Waste Report</h1>
            <div class="shift">{shift} &nbsp;•&nbsp; {issue_date}</div>
          </div>
          <div class="header-spacer"></div>
        </div>

        <div class="content">
          <table>
            <colgroup>
              <col class="w-date">
              <col class="w-machine">
              <col class="w-incharge">
              <col class="w-pub">
              <col class="w-po">
              <col class="w-num">
              <col class="w-num">
              <col class="w-num">
              <col class="w-num">
              <col class="w-extra">
              <col class="w-reason">
            </colgroup>
            <thead>
              <tr>
                <th rowspan="2">EDITION DATE</th>
                <th rowspan="2">MACHINE</th>
                <th rowspan="2">MACHINE<br>IN-CHARGE</th>
                <th rowspan="2">PUBLICATION</th>
                <th rowspan="2">PO</th>
                <th colspan="2">PREDICTED WASTE</th>
                <th colspan="2">ACTUAL WASTE</th>
                <th rowspan="2">EXTRA WASTE<br>(Qty)</th>
                <th rowspan="2">REASON FOR EXTRA WASTE</th>
              </tr>
              <tr>
                <th>Qty</th>
                <th>%</th>
                <th>Qty</th>
                <th>%</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows)}
            </tbody>
          </table>

          <div class="summary-grid">
            <div class="summary-card">
              <div class="summary-head">PREDICTED SUMMARY</div>
              <div class="summary-body">
                {''.join(pred_metrics)}
                <div class="total-box">
                  <div class="total-label">TOTAL PREDICT</div>
                  <div class="total-value">{'—' if overall['predicted'] is None else f"{overall['predicted']:.2f}%"} </div>
                </div>
              </div>
            </div>

            <div class="summary-card">
              <div class="summary-head">ACTUAL SUMMARY</div>
              <div class="summary-body">
                {''.join(act_metrics)}
                <div class="total-box actual">
                  <div class="total-label">TOTAL ACTUAL</div>
                  <div class="total-value">{'—' if overall['actual'] is None else f"{overall['actual']:.2f}%"} </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    return html


def generate_management_png(df, report_type):
    if sync_playwright is None:
        raise RuntimeError(
            "Playwright is required for the final HTML/CSS report renderer. "
            "Add 'playwright' to requirements.txt and run browser installation in deployment."
        )

    data = finalize_calculations(df).reset_index(drop=True)
    html = _render_html(data, report_type)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"],
        )

        page = browser.new_page(
            viewport={
                "width": 1536,
                "height": 2200,
            },
            device_scale_factor=1,
        )

        page.set_content(
            html,
            wait_until="networkidle",
        )

        report = page.locator(".report")

        png_bytes = report.screenshot(
            type="png"
        )

        browser.close()

    # Normalize image through PIL to ensure a clean PNG payload.
    image = Image.open(BytesIO(png_bytes)).convert("RGB")
    out = BytesIO()
    image.save(out, format="PNG", optimize=True)

    return out.getvalue()
