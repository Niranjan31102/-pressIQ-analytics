from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_MASTER_PATH = ROOT / 'backend_data' / 'product_master.xlsx'
PREDICTION_MASTER_PATH = ROOT / 'backend_data' / 'PressIQ_Prediction_Master_v1.xlsx'


def norm(v):
    if pd.isna(v): return ''
    return re.sub(r'\s+', ' ', str(v).strip()).upper()


def col(df, *names):
    cmap = {norm(c): c for c in df.columns}
    for n in names:
        if norm(n) in cmap: return cmap[norm(n)]
    return None


def num(v, default=0.0):
    x = pd.to_numeric(v, errors='coerce')
    return default if pd.isna(x) else float(x)


def load_product_master():
    if not PRODUCT_MASTER_PATH.exists():
        raise FileNotFoundError(f'Product Master not found: {PRODUCT_MASTER_PATH}')
    df = pd.read_excel(PRODUCT_MASTER_PATH, sheet_name='Product_Master')
    needed = ['Priority','Match Text','Display Code','Report Type','Status']
    miss = [c for c in needed if c not in df.columns]
    if miss: raise ValueError('Product Master missing columns: ' + ', '.join(miss))
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
    for _, r in rules.iterrows():
        if r['_match'] and r['_match'] in combined:
            code = str(r['Display Code']).strip()
            return code, 'Auto Matched', str(r['Match Text']).strip()
    fallback = str(product).strip() if not pd.isna(product) else str(edition).strip()
    return fallback or 'Unnamed Product', 'Review Required', 'Not Found in Product Master'


def _sheet_frames(path):
    if not path.exists(): raise FileNotFoundError(f'Prediction Master not found: {path}')
    return pd.read_excel(path, sheet_name=None)


def _find_rule_sheet(frames, required_groups):
    best = None; best_score = -1
    for name, df in frames.items():
        cols = {norm(c) for c in df.columns}
        score = 0
        for group in required_groups:
            if any(norm(x) in cols for x in group): score += 1
        if score > best_score:
            best = (name, df.copy()); best_score = score
    return best if best_score >= max(2, len(required_groups)-1) else (None, pd.DataFrame())


def load_prediction_rules():
    frames = _sheet_frames(PREDICTION_MASTER_PATH)
    _, base = _find_rule_sheet(frames, [
        ['Machine'], ['Min Pages','From Pages','Page From'], ['Max Pages','To Pages','Page To'],
        ['UV','UV Yes/No'], ['Predicted Waste','Base Waste','Waste']
    ])
    _, book = _find_rule_sheet(frames, [
        ['Book Count','No of Books','Books'], ['Additional Waste','Add Waste','Waste Addition','Waste']
    ])
    _, innovation = _find_rule_sheet(frames, [
        ['Innovation','Innovation Name','Specific Innovation'], ['Additional Waste','Add Waste','Waste Addition','Waste']
    ])
    if base.empty:
        raise ValueError('Could not identify Base Prediction Rules sheet in Prediction Master.')
    return {'base': base, 'book': book, 'innovation': innovation}


def _base_prediction(rules, machine, pages, uv, folder_symbol=''):
    df = rules['base'].copy()
    mc = col(df,'Machine','Machine Name')
    minc = col(df,'Min Pages','From Pages','Page From','Pages From')
    maxc = col(df,'Max Pages','To Pages','Page To','Pages To')
    uvc = col(df,'UV','UV Yes/No','UV Yes No')
    wc = col(df,'Predicted Waste','Base Waste','Waste','Waste Qty')
    fc = col(df,'Folder','Folder Type','Production Type','Symbol')
    if not all([mc,minc,maxc,wc]):
        raise ValueError('Base Prediction sheet must contain Machine, Min Pages, Max Pages and Predicted Waste.')
    m = df[df[mc].map(norm) == norm(machine)].copy()
    if uvc:
        wanted = 'YES' if norm(uv) in ['YES','Y','1','TRUE','UV'] else 'NO'
        m = m[m[uvc].map(norm).replace({'Y':'YES','N':'NO','TRUE':'YES','FALSE':'NO'}) == wanted]
    if fc and folder_symbol:
        exact = m[m[fc].map(norm) == norm(folder_symbol)]
        if not exact.empty: m = exact
    mins = pd.to_numeric(m[minc], errors='coerce'); maxs = pd.to_numeric(m[maxc], errors='coerce')
    hit = m[(mins <= pages) & (maxs >= pages)]
    if hit.empty: return None
    return int(round(num(hit.iloc[0][wc])))


def _book_addition(rules, machine, book_count, uv):
    df = rules.get('book', pd.DataFrame())
    if df.empty or book_count <= 1: return 0
    bc = col(df,'Book Count','No of Books','Books')
    wc = col(df,'Additional Waste','Add Waste','Waste Addition','Waste')
    mc = col(df,'Machine','Machine Name'); uvc = col(df,'UV','UV Yes/No','UV Yes No')
    if not bc or not wc: return 0
    q = df[pd.to_numeric(df[bc], errors='coerce') == book_count].copy()
    if mc:
        specific = q[q[mc].map(norm) == norm(machine)]
        if not specific.empty: q = specific
    if uvc:
        wanted = 'YES' if norm(uv) in ['YES','Y','1','TRUE','UV'] else 'NO'
        specific = q[q[uvc].map(norm).replace({'Y':'YES','N':'NO'}) == wanted]
        if not specific.empty: q = specific
    return 0 if q.empty else int(round(num(q.iloc[0][wc])))


def _innovation_addition(rules, innovations, machine, uv):
    df = rules.get('innovation', pd.DataFrame())
    if df.empty or not innovations: return 0
    ic = col(df,'Innovation','Innovation Name','Specific Innovation')
    wc = col(df,'Additional Waste','Add Waste','Waste Addition','Waste')
    mc = col(df,'Machine','Machine Name'); uvc = col(df,'UV','UV Yes/No','UV Yes No')
    if not ic or not wc: return 0
    total = 0
    for inv in sorted({norm(x) for x in innovations if norm(x)}):
        q = df[df[ic].map(norm) == inv].copy()
        if mc:
            specific = q[q[mc].map(norm) == norm(machine)]
            if not specific.empty: q = specific
        if uvc:
            wanted = 'YES' if norm(uv) in ['YES','Y','1','TRUE','UV'] else 'NO'
            specific = q[q[uvc].map(norm).replace({'Y':'YES','N':'NO'}) == wanted]
            if not specific.empty: q = specific
        if not q.empty: total += int(round(num(q.iloc[0][wc])))
    return total


def _book_map(book_df):
    if book_df.empty: return {}
    rid = col(book_df,'RunID','Run ID','Run Id')
    typ = col(book_df,'Integrated/Pullout','Integrated / Pullout','Book Type','Type')
    if not rid or not typ: return {}
    out = {}
    for run, g in book_df.groupby(rid):
        types = g[typ].map(norm)
        pullouts = int(types.str.contains('PULLOUT', na=False).sum())
        out[norm(run)] = 1 + pullouts
    return out


def _innovation_map(inv_df):
    if inv_df.empty: return {}
    rid = col(inv_df,'RunID','Run ID','Run Id')
    ic = col(inv_df,'Specific Innovation','Innovation','Innovation Name')
    if not rid or not ic: return {}
    out = {}
    for run, g in inv_df.groupby(rid):
        out[norm(run)] = sorted({str(v).strip() for v in g[ic].dropna() if str(v).strip()})
    return out


def process_report(uploaded_file):
    uploaded_file.seek(0)
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    general = sheets.get('General')
    if general is None:
        raise ValueError('Production Report must contain General sheet.')
    book = sheets.get('Book Wise Details', pd.DataFrame())
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
    required = {'Issue Date':c_date,'Products':c_product,'Edition':c_edition,'Main/Supplement':c_type,'Machine':c_machine,'PO':c_po,'Waste':c_waste,'Sum of Pages':c_pages}
    missing = [k for k,v in required.items() if v is None]
    if missing: raise ValueError('General sheet missing: ' + ', '.join(missing))

    master = load_product_master(); rules = load_prediction_rules()
    books = _book_map(book); innovations = _innovation_map(innovation)
    rows=[]
    for idx,r in general.iterrows():
        product=r.get(c_product,''); edition=r.get(c_edition,''); combined=norm(f'{product} {edition}')
        if 'TRIAL' in combined: continue
        report_type = norm(r.get(c_type,''))
        if report_type not in ['MAIN','SUPPLEMENT']: continue
        machine=str(r.get(c_machine,'')).strip(); pages=int(round(num(r.get(c_pages),0)))
        uv=r.get(c_uv,'NO') if c_uv else 'NO'; run=norm(r.get(c_run,'')) if c_run else str(idx)
        folder=str(r.get(c_folder,'')).strip() if c_folder else ''
        display_machine = 'Press-4 / Colorman-B' if norm(folder).replace(' ','') in ['PRESS4','PRESS-4'] else machine
        code,status,matched = match_product(product,edition,report_type.title(),master)
        book_count=books.get(run,1); invs=innovations.get(run,[])
        base=_base_prediction(rules,machine,pages,uv,folder)
        manual = base is None
        predicted = None if manual else base + _book_addition(rules,machine,book_count,uv) + _innovation_addition(rules,invs,machine,uv)
        po=num(r.get(c_po),0); actual=num(r.get(c_waste),0)
        rows.append({
            'Row ID':str(idx),'RunID':run,'Edition Date':pd.to_datetime(r.get(c_date),errors='coerce'),
            'Machine':display_machine,'Calc Machine':machine,'Machine In-charge':str(r.get(c_incharge,'—')).strip() if c_incharge else '—',
            'Product Name':str(product),'Edition':str(edition),'Publication':code,'Match Status':status,'Matched Text':matched,
            'PO':int(round(po)),'Pages':pages,'UV':str(uv),'Book Count':book_count,'Innovations':', '.join(invs) if invs else '—',
            'Predicted Waste':predicted,'Manual Prediction Required':manual,'Actual Waste':int(round(actual)),
            'Reason for Extra Waste':'NA'
        })
    df=pd.DataFrame(rows)
    if df.empty: raise ValueError('No Main/Supplement production rows found after Trial exclusion.')
    return df


def finalize_calculations(df):
    out=df.copy()
    out['Predicted Waste']=pd.to_numeric(out['Predicted Waste'],errors='coerce')
    out['PO']=pd.to_numeric(out['PO'],errors='coerce').fillna(0)
    out['Actual Waste']=pd.to_numeric(out['Actual Waste'],errors='coerce').fillna(0)
    out['Predicted %']=(out['Predicted Waste']/out['PO'].replace(0,pd.NA)*100).round(2)
    out['Actual %']=(out['Actual Waste']/out['PO'].replace(0,pd.NA)*100).round(2)
    out['Extra Waste']=(out['Actual Waste']-out['Predicted Waste']).clip(lower=0)
    out.loc[out['Extra Waste'].fillna(0)<=0,'Reason for Extra Waste']='NA'
    return out


def machine_summary(df):
    d=finalize_calculations(df)
    rows=[]
    for machine,g in d.groupby('Calc Machine'):
        po=g['PO'].sum(); pred=g['Predicted Waste'].sum(min_count=1); act=g['Actual Waste'].sum()
        rows.append({'Machine':machine,'Predicted %':round(pred/po*100,2) if po and pd.notna(pred) else None,'Actual %':round(act/po*100,2) if po else None})
    po=d['PO'].sum(); pred=d['Predicted Waste'].sum(min_count=1); act=d['Actual Waste'].sum()
    overall={'Predicted %':round(pred/po*100,2) if po and pd.notna(pred) else None,'Actual %':round(act/po*100,2) if po else None}
    return pd.DataFrame(rows), overall
