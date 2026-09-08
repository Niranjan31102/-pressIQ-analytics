from io import BytesIO
import html as html_lib

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


def _build_summary(data):
    order = ["PRESS 1", "PRESS 3", "PRESS 4", "PRESS 5"]

    work = data.copy()
    work["_press"] = work["Machine"].astype(str).str.upper().str.strip()

    rows = []

    for press in order:
        group = work[work["_press"] == press]

        if group.empty:
            continue

        po = pd.to_numeric(
            group["PO"],
            errors="coerce",
        ).fillna(0).sum()

        pred = pd.to_numeric(
            group["Predicted Waste"],
            errors="coerce",
        ).sum(min_count=1)

        act = pd.to_numeric(
            group["Actual Waste"],
            errors="coerce",
        ).fillna(0).sum()

        rows.append(
            {
                "name": press.title(),
                "predicted": (
                    round(pred / po * 100, 2)
                    if po and pd.notna(pred)
                    else None
                ),
                "actual": (
                    round(act / po * 100, 2)
                    if po
                    else None
                ),
            }
        )

    total_po = pd.to_numeric(
        work["PO"],
        errors="coerce",
    ).fillna(0).sum()

    total_pred = pd.to_numeric(
        work["Predicted Waste"],
        errors="coerce",
    ).sum(min_count=1)

    total_act = pd.to_numeric(
        work["Actual Waste"],
        errors="coerce",
    ).fillna(0).sum()

    overall = {
        "predicted": (
            round(total_pred / total_po * 100, 2)
            if total_po and pd.notna(total_pred)
            else None
        ),
        "actual": (
            round(total_act / total_po * 100, 2)
            if total_po
            else None
        ),
    }

    return rows, overall


def _render_html(data, report_type):
    machines, overall = _build_summary(data)

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

    table_rows = []

    for _, row in data.iterrows():
        pred_pct = row.get("Predicted %")
        actual_pct = row.get("Actual %")
        actual_qty = row.get("Actual Waste")
        predicted_qty = row.get("Predicted Waste")

        if pd.notna(pred_pct) and pd.notna(actual_pct):
            if float(actual_pct) > float(pred_pct):
                actual_class = "bad"
            elif float(actual_pct) < float(pred_pct):
                actual_class = "good"
            else:
                actual_class = ""
        else:
            actual_class = ""

        if pd.notna(predicted_qty) and pd.notna(actual_qty):
            if float(actual_qty) > float(predicted_qty):
                extra_class = "bad"
            elif float(actual_qty) < float(predicted_qty):
                extra_class = "good"
            else:
                extra_class = ""
        else:
            extra_class = ""

        table_rows.append(
            f"""
            <tr>
                <td>
                    {
                        html_lib.escape(
                            pd.to_datetime(
                                row["Edition Date"]
                            ).strftime("%d/%m/%Y")
                            if pd.notna(row["Edition Date"])
                            else "—"
                        )
                    }
                </td>

                <td>
                    {html_lib.escape(str(row.get("Machine", "—")))}
                </td>

                <td>
                    {html_lib.escape(str(row.get("Machine In-charge", "—")))}
                </td>

                <td>
                    {html_lib.escape(str(row.get("Publication", "—")))}
                </td>

                <td>
                    {_fmt_int(row.get("PO"))}
                </td>

                <td>
                    {_fmt_int(row.get("Predicted Waste"))}
                </td>

                <td class="pred">
                    {_fmt_pct(row.get("Predicted %"))}
                </td>

                <td>
                    {_fmt_int(row.get("Actual Waste"))}
                </td>

                <td class="{actual_class}">
                    {_fmt_pct(row.get("Actual %"))}
                </td>

                <td class="{extra_class}">
                    {_fmt_int(row.get("Extra Waste"))}
                </td>

                <td class="reason">
                    {
                        html_lib.escape(
                            _safe_reason(
                                row.get(
                                    "Reason for Extra Waste",
                                    "NA",
                                )
                            )
                        )
                    }
                </td>
            </tr>
            """
        )

    def summary_metrics(kind):
        blocks = []

        for machine in machines:
            value = machine[kind]

            blocks.append(
                f"""
                <div class="metric">
                    <div class="metric-label">
                        {html_lib.escape(machine["name"])} %
                    </div>

                    <div class="metric-value {'pred' if kind == 'predicted' else 'actual'}">
                        {"—" if value is None else f"{value:.2f}%"}
                    </div>
                </div>
                """
            )

        return "".join(blocks)

    html_doc = f"""
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
          background: white;
        }}

        .header {{
          min-height: 138px;
          background: linear-gradient(90deg, #061a3f, #08275c);
          color: white;
          padding: 24px 34px 20px;
          display: grid;
          grid-template-columns: 260px 1fr 260px;
          align-items: center;
        }}

        .brand {{
          display: flex;
          align-items: center;
          gap: 16px;
        }}

        .piq {{
          font-size: 54px;
          line-height: 1;
          font-weight: 800;
          letter-spacing: -3px;
        }}

        .pressiq {{
          font-size: 22px;
          font-weight: 700;
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
          font-size: 16px;
          line-height: 1.2;
          font-weight: 800;
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
          line-height: 1.35;
          font-weight: 600;
          white-space: normal;
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

        .good {{
          color: #087a57;
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
          display: flex;
          align-items: stretch;
          min-height: 150px;
        }}

        .metrics {{
          display: grid;
          grid-template-columns: repeat({max(len(machines), 1)}, 1fr);
          flex: 1;
        }}

        .metric {{
          min-width: 0;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          padding: 18px 8px;
          border-right: 1px solid #e5e7eb;
        }}

        .metric-label {{
          font-size: 15px;
          line-height: 1.2;
          font-weight: 800;
          text-align: center;
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
          width: 170px;
          margin: 14px;
          border-radius: 14px;
          background: #061a3f;
          color: white;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 12px;
        }}

        .total-box.actual {{
          background: #075f46;
        }}

        .total-label {{
          font-size: 14px;
          font-weight: 800;
          text-align: center;
        }}

        .total-value {{
          margin-top: 10px;
          font-size: 34px;
          font-weight: 800;
        }}

        .w-date {{ width: 8%; }}
        .w-machine {{ width: 8%; }}
        .w-incharge {{ width: 11%; }}
        .w-pub {{ width: 8%; }}
        .w-po {{ width: 7%; }}
        .w-num {{ width: 7%; }}
        .w-extra {{ width: 8%; }}
        .w-reason {{ width: 29%; }}
      </style>
    </head>

    <body>
      <div class="report">

        <div class="header">
          <div class="brand">
            <div class="piq">PIQ</div>
            <div class="pressiq">PressIQ</div>
          </div>

          <div class="title">
            <h1>Actual vs Predicted Waste Report</h1>
            <div class="shift">
              {shift} &nbsp;•&nbsp; {issue_date}
            </div>
          </div>

          <div></div>
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
                <th rowspan="2">PRESS</th>
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
              {''.join(table_rows)}
            </tbody>
          </table>

          <div class="summary-grid">

            <div class="summary-card">
              <div class="summary-head">
                PREDICTED SUMMARY
              </div>

              <div class="summary-body">
                <div class="metrics">
                  {summary_metrics("predicted")}
                </div>

                <div class="total-box">
                  <div class="total-label">
                    TOTAL PREDICT
                  </div>

                  <div class="total-value">
                    {
                        "—"
                        if overall["predicted"] is None
                        else f"{overall['predicted']:.2f}%"
                    }
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-card">
              <div class="summary-head">
                ACTUAL SUMMARY
              </div>

              <div class="summary-body">
                <div class="metrics">
                  {summary_metrics("actual")}
                </div>

                <div class="total-box actual">
                  <div class="total-label">
                    TOTAL ACTUAL
                  </div>

                  <div class="total-value">
                    {
                        "—"
                        if overall["actual"] is None
                        else f"{overall['actual']:.2f}%"
                    }
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </body>
    </html>
    """

    return html_doc


def generate_management_png(df, report_type):
    if sync_playwright is None:
        raise RuntimeError(
            "Playwright is required. Add playwright to requirements.txt."
        )

    data = finalize_calculations(df).reset_index(drop=True)
    html_doc = _render_html(data, report_type)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                executable_path="/usr/bin/chromium",
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

        except Exception:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

        page = browser.new_page(
            viewport={
                "width": 1536,
                "height": 2200,
            },
            device_scale_factor=1,
        )

        page.set_content(
            html_doc,
            wait_until="networkidle",
        )

        png_bytes = page.locator(
            ".report"
        ).screenshot(
            type="png"
        )

        browser.close()

    image = Image.open(
        BytesIO(png_bytes)
    ).convert("RGB")

    out = BytesIO()

    image.save(
        out,
        format="PNG",
        optimize=True,
    )

    return out.getvalue()
