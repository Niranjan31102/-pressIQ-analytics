from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_MASTER_PATH = ROOT / 'backend_data' / 'product_master.xlsx'
PREDICTION_MASTER_PATH = ROOT / 'backend_data' / 'PressIQ_Prediction_Master_v1.xlsx'

def norm(value):
    if pd.isna(value): return ''
    return re.sub(r'\s+', ' ', str(value).strip()).upper()

def col(df, *names):
    cmap = {norm(c): c for c in df.columns}
    for name in names:
        if norm(name) in cmap: return cmap[norm(name)]
    return None

def num(value, default=0.0):
    n = pd.to_numeric(value, errors='coerce')
    return default if pd.isna(n) else float(n)

def normalize_yes_no(value):
    return 'YES' if norm(value) in {'YES','Y','1','TRUE','UV'} else 'NO'

def _tokens(value):
    return {token for token in re.findall(r'[A-Z0-9]+', norm(value)) if token}

def load_product_master():
    if not PRODUCT_MASTER_PATH.exists():
        raise FileNotFoundError(f'Product Master not found: {PRODUCT_MASTER_PATH}')
    df = pd.read_excel(PRODUCT_MASTER_PATH, sheet_name='Product_Master')
    required = ['Priority','Match Text','Display Code','Report Type','Status']
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError('Product Master missing columns: ' + ', '.join(missing))
    df = df.dropna(subset=['Match Text','Display Code']).copy()
    df['Priority'] = pd.to_numeric(df['Priority'], errors='coerce').fillna(9999)
    df['_match'] = df['Match Text'].map(norm)
    df['_type'] = df['Report Type'].map(norm)
    df['_status'] = df['Status'].map(norm)
    df = df[df['_status'].isin(['ACTIVE','YES','Y','TRUE','1'])]
    return df.sort_values('Priority').reset_index(drop=True)

def match_product(product, edition, report_type, master):
    combined = norm(f'{product} {edition}')
    rules = master[master['_type'] == norm(report_type)]
    for _, rule in rules.iterrows():
        if rule['_match'] and rule['_match'] in combined:
            return str(rule['Display Code']).strip(), 'Auto Matched', str(rule['Match Text']).strip()
    fallback = str(product).strip() if not pd.isna(product) else (str(edition).strip() if not pd.isna(edition) else '')
    return fallback or 'Unnamed Product', 'Review Required', 'Not Found in Product Master'

def load_prediction_rules():
    if not PREDICTION_MASTER_PATH.exists():
        raise FileNotFoundError(f'Prediction Master not found: {PREDICTION_MASTER_PATH}')
    xls = pd.ExcelFile(PREDICTION_MASTER_PATH)
    required_sheets = {'Base Prediction Rules','Additional Waste Rules'}
    missing = required_sheets - set(xls.sheet_names)
    if missing: raise ValueError('Prediction Master missing sheet(s): ' + ', '.join(sorted(missing)))
    base = pd.read_excel(PREDICTION_MASTER_PATH, sheet_name='Base Prediction Rules', header=2).dropna(how='all').dropna(axis=1, how='all')
    additional = pd.read_excel(PREDICTION_MASTER_PATH, sheet_name='Additional Waste Rules', header=2).dropna(how='all').dropna(axis=1, how='all')
    base_required = ['Production Type','Pages From','Pages To','UV (Yes/No)','Machine Family','Base Prediction (Copies)']
    missing = [c for c in base_required if c not in base.columns]
    if missing: raise ValueError('Base Prediction Rules missing columns: ' + ', '.join(missing))
    add_required = ['Rule Type','Parameter','UV (Yes/No)','Waste Addition (Copies)','Status']
    missing = [c for c in add_required if c not in additional.columns]
    if missing: raise ValueError('Additional Waste Rules missing columns: ' + ', '.join(missing))
    for c in ['Pages From','Pages To','Base Prediction (Copies)']:
        base[c] = pd.to_numeric(base[c], errors='coerce')
    base = base.dropna(subset=['Production Type','Pages From','Pages To','Machine Family','Base Prediction (Copies)']).copy()
    additional['Waste Addition (Copies)'] = pd.to_numeric(additional['Waste Addition (Copies)'], errors='coerce')
    additional['_status'] = additional['Status'].map(norm)
    additional = additional[additional['_status'].isin(['ACTIVE','YES','Y','TRUE','1'])].dropna(subset=['Rule Type','Parameter','Waste Addition (Copies)']).copy()
    innovation = additional[additional['Rule Type'].map(norm) == 'INNOVATION'].copy()
    return {'base': base.reset_index(drop=True), 'innovation': innovation.reset_index(drop=True)}

def _base_prediction(rules, machine, pages, uv, production_type):
    df = rules['base'].copy()
    machine_name = norm(machine)
    df = df[df['Machine Family'].map(norm) == machine_name].copy()
    if df.empty: return None
    # FINAL RULE: Cromoman-C machine identity overrides incorrect source production type.
    wanted_type = '>>' if machine_name == 'CROMOMAN-C' else str(production_type).strip()
    if wanted_type:
        df = df[df['Production Type'].astype(str).str.strip() == wanted_type].copy()
    if df.empty: return None
    wanted_uv = normalize_yes_no(uv)
    df = df[df['UV (Yes/No)'].map(normalize_yes_no) == wanted_uv].copy()
    if df.empty: return None
    p = num(pages, 0)
    hit = df[(df['Pages From'] <= p) & (df['Pages To'] >= p)]
    if hit.empty: return None
    return int(round(num(hit.iloc[0]['Base Prediction (Copies)'], 0)))

def _best_innovation_rule(rule_df, reported_innovation, uv):
    """Flexible innovation matching for changing shop-floor wording.

    Examples:
      Backend: French Window
      Report : French Window GNP (With SNP center)
      -> MATCH

      Backend: HD French Window
      Report : French Window GNP (With SNP center)
      -> FALLBACK MATCH on the stable phrase FRENCH WINDOW

      Backend: HD French Window
      Report : HD French Window GNP
      -> EXACT/MORE-SPECIFIC MATCH

    The engine first prefers the full backend phrase. If that is not present,
    it allows a fallback after removing known descriptive prefixes such as HD.
    This keeps the stable innovation name usable even when operators add or
    omit descriptive wording.
    """
    if rule_df.empty:
        return None

    report_tokens = _tokens(reported_innovation)
    if not report_tokens:
        return None

    wanted_uv = normalize_yes_no(uv)
    candidates = []

    # Descriptors that may be added/omitted by users without changing the
    # underlying innovation identity.
    optional_descriptors = {"HD"}

    for idx, rule in rule_df.iterrows():
        if normalize_yes_no(rule['UV (Yes/No)']) != wanted_uv:
            continue

        parameter = str(rule['Parameter']).strip()
        parameter_tokens = _tokens(parameter)
        if not parameter_tokens:
            continue

        # 1) Full phrase match gets highest priority.
        full_match = parameter_tokens.issubset(report_tokens)

        # 2) Stable/core phrase fallback. Example:
        #    HD FRENCH WINDOW -> FRENCH WINDOW
        core_tokens = parameter_tokens - optional_descriptors
        core_match = len(core_tokens) >= 2 and core_tokens.issubset(report_tokens)

        if not (full_match or core_match):
            continue

        # Exact/full phrase outranks fallback. Within the same class,
        # the more specific rule wins.
        candidates.append((
            1 if full_match else 0,
            len(parameter_tokens) if full_match else len(core_tokens),
            len(norm(parameter)),
            idx,
        ))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return rule_df.loc[candidates[0][3]]

def _innovation_addition(rules, innovations, uv):
    df = rules.get('innovation', pd.DataFrame())
    if df.empty or not innovations:
        return 0

    total = 0
    unique_reported = {str(v).strip() for v in innovations if str(v).strip()}

    for reported_innovation in unique_reported:
        matched_rule = _best_innovation_rule(df, reported_innovation, uv)
        if matched_rule is None:
            continue

        total += int(round(num(matched_rule['Waste Addition (Copies)'], 0)))

    return total

def _innovation_map(innovation_df):
    if innovation_df.empty: return {}
    run_col = col(innovation_df, 'RunID','Run ID','Run Id')
    inv_col = col(innovation_df, 'Specific Innovation','Innovation','Innovation Name')
    if run_col is None or inv_col is None: return {}
    result = {}
    for run_id, group in innovation_df.groupby(run_col):
        result[norm(run_id)] = sorted({str(v).strip() for v in group[inv_col].dropna() if str(v).strip()})
    return result

def _press_display(machine, folder):
    """Plant-head display naming, using Folder/Press first and machine fallback second."""
    folder_text = norm(folder)

    match = re.search(r'\bPRESS\s*[- ]?\s*(1|3|4|5)\b', folder_text)
    if match:
        return f"Press {match.group(1)}"

    compact = re.sub(r'[^A-Z0-9]', '', folder_text)
    compact_match = re.search(r'PRESS(1|3|4|5)', compact)
    if compact_match:
        return f"Press {compact_match.group(1)}"

    fallback = {
        'COLORMAN-A': 'Press 1',
        'COLORMAN-B': 'Press 3',
        'CROMOMAN-C': 'Press 5',
    }
    return fallback.get(norm(machine), str(machine).strip() or '—')


def process_report(uploaded_file):
    uploaded_file.seek(0)
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    general = sheets.get('General')
    if general is None: raise ValueError('Production Report must contain General sheet.')
    innovation = sheets.get('Innovation', sheets.get('Innovations', pd.DataFrame()))
    c_date = col(general,'Issue Date','Edition Date')
    c_product = col(general,'Products','Product Name','Product')
    c_edition = col(general,'Edition','Edition Name')
    c_type = col(general,'Main/Supplement','Main / Supplement','Main Supplement')
    c_machine = col(general,'Machine','Machine Name')
    c_po = col(general,'Print Order','PO','PrintOrder')
    c_waste = col(general,'Waste','Actual Waste','Total Waste')
    c_incharge = col(general,'Machine In-Charge','Machine Incharge','Machine In-charge')
    c_pages = col(general,'Sum of Pages','Pages','Total Pages')
    c_uv = col(general,'UV','UV Yes/No','UV Yes No')
    c_run = col(general,'RunID','Run ID','Run Id')
    c_folder = col(general,'Folder','Press','Folder/Press')
    c_prod_type = col(general,'Production Type')
    required = {'Issue Date':c_date,'Products':c_product,'Edition':c_edition,'Main/Supplement':c_type,'Machine':c_machine,'PO':c_po,'Waste':c_waste,'Sum of Pages':c_pages,'Production Type':c_prod_type}
    missing = [name for name,val in required.items() if val is None]
    if missing: raise ValueError('General sheet missing: ' + ', '.join(missing))
    product_master = load_product_master()
    prediction_rules = load_prediction_rules()
    innovations_by_run = _innovation_map(innovation)
    out = []
    for index, row in general.iterrows():
        product = row.get(c_product,'')
        edition = row.get(c_edition,'')
        if 'TRIAL' in norm(f'{product} {edition}'): continue
        report_type = norm(row.get(c_type,''))
        if report_type not in {'MAIN','SUPPLEMENT'}: continue
        machine = str(row.get(c_machine,'')).strip()
        pages = int(round(num(row.get(c_pages),0)))
        uv = row.get(c_uv,'NO') if c_uv else 'NO'
        run_id = norm(row.get(c_run,'')) if c_run else str(index)
        folder = str(row.get(c_folder,'')).strip() if c_folder else ''
        source_prod_type = str(row.get(c_prod_type,'')).strip()
        effective_prod_type = '>>' if norm(machine) == 'CROMOMAN-C' else source_prod_type
        display_machine = _press_display(machine, folder)
        publication_code, match_status, matched_text = match_product(product, edition, report_type.title(), product_master)
        innovations = innovations_by_run.get(run_id, [])
        base_prediction = _base_prediction(prediction_rules, machine, pages, uv, effective_prod_type)
        manual_required = base_prediction is None
        if manual_required:
            predicted_waste = None
            innovation_addition = 0
        else:
            innovation_addition = _innovation_addition(prediction_rules, innovations, uv)
            predicted_waste = base_prediction + innovation_addition
        po = num(row.get(c_po),0)
        actual_waste = num(row.get(c_waste),0)
        machine_incharge = str(row.get(c_incharge,'—')).strip() if c_incharge else '—'
        out.append({
            'Row ID': str(index),
            'RunID': run_id,
            'Edition Date': pd.to_datetime(row.get(c_date), errors='coerce'),
            'Report Type': report_type.title(),
            'Machine': display_machine,
            'Calc Machine': machine,
            'Folder': folder,
            'Machine In-charge': machine_incharge,
            'Product Name': str(product),
            'Edition': str(edition),
            'Publication': publication_code,
            'Match Status': match_status,
            'Matched Text': matched_text,
            'PO': int(round(po)),
            'Pages': pages,
            'Source Production Type': source_prod_type,
            'Production Type': effective_prod_type,
            'UV': str(uv),
            'Book Count': 1,
            'Innovations': ', '.join(innovations) if innovations else '—',
            'Base Prediction': base_prediction,
            'Book Addition': 0,
            'Innovation Addition': innovation_addition,
            'Predicted Waste': predicted_waste,
            'Manual Prediction Required': manual_required,
            'Actual Waste': int(round(actual_waste)),
            'Reason for Extra Waste': 'NA',
        })
    df = pd.DataFrame(out)
    if df.empty: raise ValueError('No Main/Supplement production rows found after Trial exclusion.')
    return df

def finalize_calculations(df):
    output = df.copy()
    output['Predicted Waste'] = pd.to_numeric(output['Predicted Waste'], errors='coerce')
    output['PO'] = pd.to_numeric(output['PO'], errors='coerce').fillna(0)
    output['Actual Waste'] = pd.to_numeric(output['Actual Waste'], errors='coerce').fillna(0)
    output['Predicted %'] = (output['Predicted Waste'] / output['PO'].replace(0,pd.NA) * 100).round(2)
    output['Actual %'] = (output['Actual Waste'] / output['PO'].replace(0,pd.NA) * 100).round(2)
    output['Extra Waste'] = (output['Actual Waste'] - output['Predicted Waste']).clip(lower=0)
    output.loc[output['Extra Waste'].fillna(0) <= 0,'Reason for Extra Waste'] = 'NA'
    return output

def machine_summary(df):
    data = finalize_calculations(df)
    rows = []
    for machine, group in data.groupby('Machine'):
        total_po = group['PO'].sum()
        total_pred = group['Predicted Waste'].sum(min_count=1)
        total_actual = group['Actual Waste'].sum()
        rows.append({
            'Machine': machine,
            'Predicted %': round(total_pred/total_po*100,2) if total_po and pd.notna(total_pred) else None,
            'Actual %': round(total_actual/total_po*100,2) if total_po else None,
        })
    overall_po = data['PO'].sum()
    overall_pred = data['Predicted Waste'].sum(min_count=1)
    overall_actual = data['Actual Waste'].sum()
    overall = {
        'Predicted %': round(overall_pred/overall_po*100,2) if overall_po and pd.notna(overall_pred) else None,
        'Actual %': round(overall_actual/overall_po*100,2) if overall_po else None,
    }
    return pd.DataFrame(rows), overall
