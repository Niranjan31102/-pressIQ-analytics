import base64
import pandas as pd
import streamlit as st
from ui_theme import module_hero
from modules.avp_engine import process_report, finalize_calculations, machine_summary
from modules.avp_report import generate_management_png


def _css():
    st.markdown('''<style>
    .avp-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:8px 0 22px}.avp-step{padding:16px 18px;border-radius:18px;background:linear-gradient(145deg,#fff,#f4f8ff);border:1px solid #d8e3f3;box-shadow:0 10px 25px rgba(15,23,42,.06)}.avp-step.on{border-color:#38bdf8;box-shadow:0 12px 30px rgba(37,99,235,.15)}.avp-n{font-size:12px;font-weight:900;color:#2563eb}.avp-t{font-size:16px;font-weight:900;color:#0f172a;margin-top:4px}.avp-s{font-size:12px;color:#64748b;margin-top:3px}.avp-info{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}.avp-k{background:white;border:1px solid #dbe5f1;border-radius:16px;padding:14px;text-align:center;box-shadow:0 8px 20px rgba(15,23,42,.05)}.avp-kl{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:800}.avp-kv{font-size:22px;color:#0f172a;font-weight:950;margin-top:4px}.avp-title{font-size:18px;font-weight:950;color:#0f172a;margin:16px 0 8px}.avp-note{background:#fff7ed;border:1px solid #fed7aa;border-left:5px solid #f97316;border-radius:14px;padding:12px 14px;margin:10px 0;color:#9a3412;font-weight:700}.avp-ready{background:#ecfdf5;border:1px solid #a7f3d0;border-left:5px solid #10b981;border-radius:14px;padding:12px 14px;margin:10px 0;color:#065f46;font-weight:800}.avp-footer{text-align:center;color:#94a3b8;font-size:12px;margin:28px 0 8px}.stButton>button{min-height:48px}.avp-preview img{width:100%;border-radius:18px;box-shadow:0 18px 45px rgba(15,23,42,.12);border:1px solid #dbe5f1}@media(max-width:800px){.avp-steps,.avp-info{grid-template-columns:1fr 1fr}}
    </style>''',unsafe_allow_html=True)


def _init():
    defaults={'avp_stage':'upload','avp_raw':None,'avp_work':None,'avp_type':'Main','avp_png':None,'avp_reason_row':None}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v


def _steps():
    stage=st.session_state.avp_stage; order=['upload','review','report']; idx=order.index(stage)
    labels=[('01','Upload Report'),('02','Working Table'),('03','Final Report')]
    html='<div class="avp-steps">'
    for i,(n,t) in enumerate(labels):
        cls='avp-step on' if i==idx else 'avp-step'; status='Active' if i==idx else ('Complete' if i<idx else 'Pending')
        html+=f'<div class="{cls}"><div class="avp-n">{n}</div><div class="avp-t">{t}</div><div class="avp-s">{status}</div></div>'
    st.markdown(html+'</div>',unsafe_allow_html=True)


def _summary_cards(df):
    dates=pd.to_datetime(df['Edition Date'],errors='coerce').dropna(); date=dates.iloc[0].strftime('%d %b %Y') if not dates.empty else '—'
    main=int((df['_type']=='MAIN').sum()) if '_type' in df else 0; supp=int((df['_type']=='SUPPLEMENT').sum()) if '_type' in df else 0
    st.markdown(f'''<div class="avp-info"><div class="avp-k"><div class="avp-kl">Issue Date</div><div class="avp-kv">{date}</div></div><div class="avp-k"><div class="avp-kl">Main Editions</div><div class="avp-kv">{main}</div></div><div class="avp-k"><div class="avp-kl">Supplement</div><div class="avp-kv">{supp}</div></div><div class="avp-k"><div class="avp-kl">Total Editions</div><div class="avp-kv">{main+supp}</div></div></div>''',unsafe_allow_html=True)


def _upload():
    st.markdown('<div class="avp-title">Upload Production Report</div>',unsafe_allow_html=True)
    f=st.file_uploader('Upload Production Report',type=['xlsx','xls'],label_visibility='collapsed',key='avp_upload_v1')
    if f is None: return
    try:
        f.seek(0); general=pd.read_excel(f,sheet_name='General'); f.seek(0)
        type_col=next((c for c in general.columns if str(c).strip().upper().replace(' ','') in ['MAIN/SUPPLEMENT','MAINSUPPLEMENT']),None)
        date_col=next((c for c in general.columns if str(c).strip().upper() in ['ISSUE DATE','EDITION DATE']),None)
        preview=pd.DataFrame({'Edition Date':general[date_col] if date_col else pd.NaT,'_type':general[type_col].astype(str).str.strip().str.upper() if type_col else ''})
        _summary_cards(preview)
    except Exception as e:
        st.error(f'Unable to read report summary: {e}'); return
    st.markdown('<div class="avp-title">Select Production Type</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button(('✓  MAIN' if st.session_state.avp_type=='Main' else 'MAIN'),use_container_width=True,key='avp_main'): st.session_state.avp_type='Main'; st.rerun()
    with c2:
        if st.button(('✓  SUPPLEMENT' if st.session_state.avp_type=='Supplement' else 'SUPPLEMENT'),use_container_width=True,key='avp_supp'): st.session_state.avp_type='Supplement'; st.rerun()
    if st.button('Process Report',type='primary',use_container_width=True,key='avp_process'):
        try:
            with st.spinner('Processing report...'):
                f.seek(0); all_df=process_report(f); selected=all_df[all_df['Match Status'].notna()].copy(); selected=selected[selected.apply(lambda r: True,axis=1)]
                selected=selected[selected['Row ID'].isin(selected['Row ID'])]
                # filter by original report type through product master result set using General re-read index
                f.seek(0); g=pd.read_excel(f,sheet_name='General'); tc=next((c for c in g.columns if str(c).strip().upper().replace(' ','') in ['MAIN/SUPPLEMENT','MAINSUPPLEMENT']),None)
                if tc:
                    wanted=st.session_state.avp_type.upper(); valid=set(g[g[tc].astype(str).str.strip().str.upper()==wanted].index.astype(str)); selected=selected[selected['Row ID'].isin(valid)]
                if selected.empty: raise ValueError(f'No {st.session_state.avp_type} editions found.')
                st.session_state.avp_work=selected.reset_index(drop=True); st.session_state.avp_stage='review'; st.session_state.avp_png=None
            st.rerun()
        except Exception as e: st.error(str(e))


def _review():
    df=st.session_state.avp_work
    if df is None or df.empty: st.session_state.avp_stage='upload'; st.rerun()
    st.markdown('<div class="avp-title">Production Working Table</div>',unsafe_allow_html=True)
    manual=df[df['Manual Prediction Required']==True]
    if not manual.empty: st.markdown(f'<div class="avp-note">Manual prediction required for {len(manual)} edition(s) because the page count is outside configured Prediction Master ranges.</div>',unsafe_allow_html=True)
    # publication edits only for unmatched
    unmatched=df[df['Match Status']=='Review Required']
    if not unmatched.empty:
        st.warning(f'{len(unmatched)} publication(s) require review.')
        for i in unmatched.index:
            df.at[i,'Publication']=st.text_input(f"Publication — {df.at[i,'Product Name']}",value=str(df.at[i,'Publication']),key=f'avp_pub_{i}')
    if not manual.empty:
        st.markdown('**Manual Predicted Waste — only exception rows are editable**')
        for i in manual.index:
            val=st.number_input(f"{df.at[i,'Publication']} | {df.at[i,'Machine']} | {df.at[i,'Pages']} pages",min_value=0,value=int(df.at[i,'Predicted Waste']) if pd.notna(df.at[i,'Predicted Waste']) else 0,step=50,key=f'avp_manual_{i}')
            df.at[i,'Predicted Waste']=val if val>0 else pd.NA
    calc=finalize_calculations(df)
    view_cols=['Edition Date','Machine','Machine In-charge','Publication','PO','Predicted Waste','Predicted %','Actual Waste','Actual %','Extra Waste','Reason for Extra Waste']
    st.dataframe(calc[view_cols],use_container_width=True,hide_index=True,height=min(650,100+len(calc)*42))
    st.markdown('<div class="avp-title">Reason Editor</div>',unsafe_allow_html=True)
    needs=calc[calc['Extra Waste'].fillna(0)>0]
    if needs.empty: st.markdown('<div class="avp-ready">No extra-waste reason is required.</div>',unsafe_allow_html=True)
    else:
        options=list(needs.index); chosen=st.selectbox('Select edition to enter / edit reason',options,format_func=lambda i:f"{calc.at[i,'Publication']} • {calc.at[i,'Machine']} • Extra {int(calc.at[i,'Extra Waste']):,}")
        current='' if str(df.at[chosen,'Reason for Extra Waste']).upper() in ['NA','NAN'] else str(df.at[chosen,'Reason for Extra Waste'])
        reason=st.text_area('Reason for Extra Waste',value=current,height=150,key=f'avp_reason_{chosen}',placeholder='Enter complete operational reason. No practical word limit.')
        if st.button('Save Reason',key='avp_save_reason'):
            df.at[chosen,'Reason for Extra Waste']=reason.strip() or 'NA'; st.session_state.avp_work=df; st.success('Reason saved.')
    calc=finalize_calculations(df); missing_manual=calc['Predicted Waste'].isna().any(); missing_reason=((calc['Extra Waste'].fillna(0)>0)&(calc['Reason for Extra Waste'].astype(str).str.strip().str.upper().isin(['','NA','NAN']))).any()
    if missing_manual: st.warning('Complete all manual predicted-waste exceptions before generating the report.')
    elif missing_reason: st.warning('Enter reasons for all editions where Actual Waste is above Predicted Waste.')
    else: st.markdown('<div class="avp-ready">Working table complete. Ready to generate the management report.</div>',unsafe_allow_html=True)
    b1,b2=st.columns([1,2])
    with b1:
        if st.button('← Back to Upload',use_container_width=True): st.session_state.avp_stage='upload'; st.rerun()
    with b2:
        if st.button('Generate Final Report',type='primary',use_container_width=True,disabled=missing_manual or missing_reason):
            st.session_state.avp_work=df; st.session_state.avp_png=generate_management_png(df,st.session_state.avp_type); st.session_state.avp_stage='report'; st.rerun()


def _report():
    df=st.session_state.avp_work; png=st.session_state.avp_png
    if df is None: st.session_state.avp_stage='upload'; st.rerun()
    if png is None: png=generate_management_png(df,st.session_state.avp_type); st.session_state.avp_png=png
    st.markdown('<div class="avp-title">Final Management Report</div>',unsafe_allow_html=True)
    b64=base64.b64encode(png).decode(); st.markdown(f'<div class="avp-preview"><img src="data:image/png;base64,{b64}"></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1,1])
    with c1:
        if st.button('← Working Table',use_container_width=True): st.session_state.avp_stage='review'; st.rerun()
    with c2: st.download_button('Download PNG',data=png,file_name=f"PressIQ_Actual_vs_Predicted_{st.session_state.avp_type}.png",mime='image/png',use_container_width=True)
    with c3: st.link_button('Open WhatsApp Web','https://web.whatsapp.com/',use_container_width=True)


def run_actual_vs_predicted_waste():
    _init(); _css(); module_hero('Actual vs Predicted Waste','') ; _steps()
    if st.session_state.avp_stage=='upload': _upload()
    elif st.session_state.avp_stage=='review': _review()
    else: _report()
    st.markdown('<div class="avp-footer">Powered by PressIQ AI · Designed for Production Intelligence</div>',unsafe_allow_html=True)
