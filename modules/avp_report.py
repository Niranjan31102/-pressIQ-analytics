from io import BytesIO
import textwrap
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from modules.avp_engine import finalize_calculations

NAVY="#041A3D"; NAVY2="#0A2E63"; BLUE="#2563EB"; GREEN="#0A7A57"; RED="#E53935"
TEXT="#0F172A"; GRID="#DCE4EF"; ALT="#F8FAFC"; WHITE="#FFFFFF"

def _font(size,bold=False):
    paths=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try: return ImageFont.truetype(p,size)
        except Exception: pass
    return ImageFont.load_default()

def _txt(draw,xy,text,size=20,bold=False,fill=TEXT,anchor=None):
    draw.text(xy,str(text),font=_font(size,bold),fill=fill,anchor=anchor)

def _center(draw,box,text,size=18,bold=False,fill=TEXT,spacing=4):
    x1,y1,x2,y2=box; value=str(text); f=_font(size,bold)
    b=draw.multiline_textbbox((0,0),value,font=f,spacing=spacing,align="center")
    tw=b[2]-b[0]; th=b[3]-b[1]
    draw.multiline_text((x1+((x2-x1)-tw)/2,y1+((y2-y1)-th)/2),value,font=f,fill=fill,spacing=spacing,align="center")

def _left(draw,box,text,size=18,bold=False,fill=TEXT,spacing=4):
    x1,y1,x2,y2=box; value=str(text); f=_font(size,bold)
    b=draw.multiline_textbbox((0,0),value,font=f,spacing=spacing); th=b[3]-b[1]
    draw.multiline_text((x1+12,y1+max(8,((y2-y1)-th)/2)),value,font=f,fill=fill,spacing=spacing)

def _safe_reason(v):
    t="" if v is None else str(v).strip()
    return "NA" if t.upper() in {"","NA","NAN","NONE"} else t

def _fmt_int(v):
    return "—" if pd.isna(v) else f"{int(round(float(v))):,}"

def _fmt_pct(v):
    return "—" if pd.isna(v) else f"{float(v):.2f}%"

def _machine_bucket(row):
    dm=str(row.get("Machine","")).upper().strip()
    cm=str(row.get("Calc Machine","")).upper().strip()
    if "PRESS-4" in dm or "PRESS 4" in dm: return "PRESS-4 / COL B"
    if "CROMOMAN-C" in {dm,cm}: return "CROMO"
    if "COLORMAN-A" in {dm,cm}: return "COL A"
    if "COLORMAN-B" in {dm,cm}: return "COL B"
    return dm or cm or "OTHER"

def _summary(data):
    work=data.copy(); work["_bucket"]=work.apply(_machine_bucket,axis=1)
    order=["CROMO","COL A","COL B","PRESS-4 / COL B"]; machines=[]
    for bucket in order:
        g=work[work["_bucket"]==bucket]
        if g.empty: continue
        po=pd.to_numeric(g["PO"],errors="coerce").fillna(0).sum()
        pred=pd.to_numeric(g["Predicted Waste"],errors="coerce").sum(min_count=1)
        act=pd.to_numeric(g["Actual Waste"],errors="coerce").fillna(0).sum()
        machines.append({"name":bucket,"pred":round(pred/po*100,2) if po and pd.notna(pred) else None,"actual":round(act/po*100,2) if po else None})
    po=pd.to_numeric(work["PO"],errors="coerce").fillna(0).sum()
    pred=pd.to_numeric(work["Predicted Waste"],errors="coerce").sum(min_count=1)
    act=pd.to_numeric(work["Actual Waste"],errors="coerce").fillna(0).sum()
    return machines,{"pred":round(pred/po*100,2) if po and pd.notna(pred) else None,"actual":round(act/po*100,2) if po else None}

def _status_icon(draw,cx,cy,good):
    c="#22C58B" if good else "#FB7185"
    draw.ellipse((cx-31,cy-31,cx+31,cy+31),outline=c,width=5)
    if good:
        draw.line((cx-15,cy,cx-4,cy+11),fill=c,width=6); draw.line((cx-4,cy+11,cx+18,cy-14),fill=c,width=6)
    else:
        draw.line((cx-14,cy-14,cx+14,cy+14),fill=c,width=5); draw.line((cx+14,cy-14,cx-14,cy+14),fill=c,width=5)

def _summary_icon(draw,cx,cy,kind):
    c=BLUE if kind=="pred" else GREEN; bg="#EFF6FF" if kind=="pred" else "#ECFDF5"
    draw.ellipse((cx-24,cy-24,cx+24,cy+24),fill=bg)
    if kind=="pred":
        for dx,dy in [(0,-13),(9,-9),(13,0),(9,9),(0,13),(-9,9),(-13,0),(-9,-9)]:
            draw.ellipse((cx+dx-3,cy+dy-3,cx+dx+3,cy+dy+3),fill=c)
    else:
        draw.polygon([(cx,cy-16),(cx-11,cy+4),(cx-7,cy+13),(cx,cy+17),(cx+7,cy+13),(cx+11,cy+4)],fill=c)

def generate_management_png(df,report_type):
    data=finalize_calculations(df).reset_index(drop=True); machines,overall=_summary(data)
    W=1650; M=28; HEADER_H=170; TABLE_GAP=28; GROUP_H=44; SUB_H=42
    columns=[("EDITION DATE",120),("MACHINE",135),("MACHINE\nIN-CHARGE",155),("PUBLICATION",105),("PO",95),("PRED QTY",95),("PRED %",85),("ACT QTY",95),("ACT %",85),("EXTRA\nWASTE",90),("REASON FOR EXTRA WASTE",537)]
    widths=[w for _,w in columns]
    wrapped=[]; heights=[]
    for _,r in data.iterrows():
        reason=_safe_reason(r.get("Reason for Extra Waste","NA"))
        lines=textwrap.wrap(reason,width=58,break_long_words=False,break_on_hyphens=False) or ["NA"]
        wrapped.append("\n".join(lines)); heights.append(72 if len(lines)==1 else max(82,28+len(lines)*22))
    SUMMARY_GAP=34; SUMMARY_H=215; BOTTOM=34; table_top=HEADER_H+TABLE_GAP
    H=table_top+GROUP_H+SUB_H+sum(heights)+SUMMARY_GAP+SUMMARY_H+BOTTOM
    im=Image.new("RGB",(W,H),WHITE); dr=ImageDraw.Draw(im)
    dr.rounded_rectangle((0,0,W,HEADER_H),radius=24,fill=NAVY)
    _txt(dr,(38,48),"PIQ",48,True,WHITE); _txt(dr,(140,68),"PressIQ Analytics",19,True,"#E2E8F0")
    _txt(dr,(W//2,47),"Actual vs Predicted Waste Report",35,True,WHITE,"ma")
    date="—"
    if "Edition Date" in data and data["Edition Date"].notna().any(): date=pd.to_datetime(data["Edition Date"].dropna().iloc[0]).strftime("%d %B %Y")
    label="MAIN SHIFT" if str(report_type).upper().strip()=="MAIN" else "SUPPLEMENT"
    pill_w=320; pill_h=44; px=W//2-pill_w//2; py=102
    dr.rounded_rectangle((px,py,px+pill_w,py+pill_h),radius=22,fill="#0B2858",outline="#315C95",width=2)
    _txt(dr,(W//2,py+pill_h/2),f"{label}    {date}",16,True,"#EAF2FF","mm")
    pred_total=overall["pred"]; actual_total=overall["actual"]; good=pred_total is not None and actual_total is not None and actual_total<=pred_total
    status="WITHIN TARGET" if good else "ABOVE TARGET"; status_color="#34D399" if good else "#FB7185"
    sx1=W-385; sy1=17; sx2=W-24; sy2=150
    dr.rounded_rectangle((sx1,sy1,sx2,sy2),radius=18,fill="#071B40",outline="#1E665C" if good else "#76334B",width=2)
    _status_icon(dr,sx1+57,sy1+66,good)
    _txt(dr,(sx1+110,sy1+25),"PERFORMANCE STATUS",13,True,"#CBD5E1"); _txt(dr,(sx1+110,sy1+55),status,22,True,status_color)
    if pred_total is not None and actual_total is not None:
        symbol="≤" if good else ">"
        _txt(dr,(sx1+110,sy1+98),f"Actual {actual_total:.2f}% {symbol} Predicted {pred_total:.2f}%",14,False,WHITE)
    y=table_top
    for idx in [0,1,2,3,4,9,10]:
        left=M+sum(widths[:idx]); w=widths[idx]
        dr.rectangle((left,y,left+w,y+GROUP_H+SUB_H),fill=NAVY2,outline="#496A98",width=1)
        _center(dr,(left,y,left+w,y+GROUP_H+SUB_H),columns[idx][0],13,True,WHITE)
    pred_left=M+sum(widths[:5]); pred_w=widths[5]+widths[6]
    dr.rectangle((pred_left,y,pred_left+pred_w,y+GROUP_H),fill=NAVY2,outline="#496A98",width=1); _txt(dr,(pred_left+pred_w/2,y+GROUP_H/2),"PREDICTED WASTE",13,True,WHITE,"mm")
    act_left=M+sum(widths[:7]); act_w=widths[7]+widths[8]
    dr.rectangle((act_left,y,act_left+act_w,y+GROUP_H),fill=NAVY2,outline="#496A98",width=1); _txt(dr,(act_left+act_w/2,y+GROUP_H/2),"ACTUAL WASTE",13,True,WHITE,"mm")
    for idx,label2 in [(5,"Qty"),(6,"%"),(7,"Qty"),(8,"%")]:
        left=M+sum(widths[:idx]); w=widths[idx]
        dr.rectangle((left,y+GROUP_H,left+w,y+GROUP_H+SUB_H),fill=NAVY2,outline="#496A98",width=1); _txt(dr,(left+w/2,y+GROUP_H+SUB_H/2),label2,13,True,WHITE,"mm")
    y+=GROUP_H+SUB_H
    for i,(_,r) in enumerate(data.iterrows()):
        row_h=heights[i]; fill=WHITE if i%2==0 else ALT
        edition_date=pd.to_datetime(r["Edition Date"]).strftime("%d/%m/%Y") if pd.notna(r["Edition Date"]) else "—"
        values=[edition_date,r.get("Machine","—"),r.get("Machine In-charge","—"),r.get("Publication","—"),_fmt_int(r.get("PO")),_fmt_int(r.get("Predicted Waste")),_fmt_pct(r.get("Predicted %")),_fmt_int(r.get("Actual Waste")),_fmt_pct(r.get("Actual %")),_fmt_int(r.get("Extra Waste")),wrapped[i]]
        x=M
        for j,((_,w),value) in enumerate(zip(columns,values)):
            dr.rectangle((x,y,x+w,y+row_h),fill=fill,outline=GRID,width=1)
            color=TEXT; bold=j in {5,6,7,8,9}
            if j==6: color=BLUE
            if j==8 and pd.notna(r.get("Predicted %")) and pd.notna(r.get("Actual %")) and float(r["Actual %"])>float(r["Predicted %"]): color=RED
            if j==9 and pd.notna(r.get("Extra Waste")) and float(r["Extra Waste"])>0: color=RED
            if j==10: _left(dr,(x,y,x+w,y+row_h),value,13,False,TEXT)
            else: _center(dr,(x,y,x+w,y+row_h),value,13,bold,color)
            x+=w
        y+=row_h
    y+=SUMMARY_GAP; gap=24; card_w=(W-2*M-gap)//2
    def draw_summary(left,title,kind):
        bottom=y+SUMMARY_H
        dr.rounded_rectangle((left,y,left+card_w,bottom),radius=18,fill=WHITE,outline=GRID,width=2)
        dr.rounded_rectangle((left,y,left+card_w,y+50),radius=18,fill=NAVY2); dr.rectangle((left,y+31,left+card_w,y+50),fill=NAVY2)
        _txt(dr,(left+22,y+25),title,15,True,WHITE,"lm")
        total_w=155; total_right=left+card_w-20; total_left=total_right-total_w
        metrics_left=left+12; metrics_right=total_left-14; metrics_w=metrics_right-metrics_left
        count=max(1,len(machines)); each=metrics_w/count
        for idx,m in enumerate(machines):
            cx=metrics_left+each*idx+each/2; _summary_icon(dr,cx,y+91,kind)
            name=m["name"]; label3="PRESS-4 /\nCOL B %" if name=="PRESS-4 / COL B" else f"{name} %"
            _center(dr,(cx-each/2,y+119,cx+each/2,y+159),label3,12,True,TEXT)
            val=m["pred"] if kind=="pred" else m["actual"]
            _txt(dr,(cx,y+185),"—" if val is None else f"{val:.2f}%",21,True,BLUE if kind=="pred" else GREEN,"ma")
        total_top=y+72; total_bottom=y+193
        dr.rounded_rectangle((total_left,total_top,total_right,total_bottom),radius=14,fill=NAVY if kind=="pred" else "#075F46")
        _txt(dr,((total_left+total_right)/2,total_top+31),"TOTAL PREDICT" if kind=="pred" else "TOTAL ACTUAL",11,True,WHITE,"ma")
        total_val=overall["pred"] if kind=="pred" else overall["actual"]
        _txt(dr,((total_left+total_right)/2,total_top+80),"—" if total_val is None else f"{total_val:.2f}%",28,True,WHITE,"ma")
    draw_summary(M,"PREDICTED SUMMARY","pred"); draw_summary(M+card_w+gap,"ACTUAL SUMMARY","actual")
    out=BytesIO(); im.save(out,format="PNG",optimize=True); return out.getvalue()
