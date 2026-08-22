from io import BytesIO
import textwrap
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from modules.avp_engine import finalize_calculations, machine_summary


def _font(size, bold=False):
    paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in paths:
        try:return ImageFont.truetype(p,size)
        except:pass
    return ImageFont.load_default()


def _txt(draw,xy,text,size=20,bold=False,fill='#0f172a',anchor=None):
    draw.text(xy,str(text),font=_font(size,bold),fill=fill,anchor=anchor)


def generate_management_png(df, report_type):
    d=finalize_calculations(df)
    summary,overall=machine_summary(d)
    rows=len(d); W=1900; header_h=180; table_head=86; row_h=92; summary_h=250; H=header_h+table_head+rows*row_h+summary_h+70
    im=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(im)
    navy='#071a3d'; blue='#0b2f63'; cyan='#22d3ee'; green='#059669'; red='#dc2626'; grid='#dbe3ee'; light='#f8fafc'
    dr.rounded_rectangle((0,0,W,header_h),radius=28,fill=navy)
    _txt(dr,(45,58),'PIQ',52,True,'white'); _txt(dr,(165,76),'PressIQ',25,True,'white')
    _txt(dr,(W//2,55),'Actual vs Predicted Waste Report',40,True,'white','ma')
    date='—'
    if 'Edition Date' in d and d['Edition Date'].notna().any(): date=pd.to_datetime(d['Edition Date'].dropna().iloc[0]).strftime('%d %B %Y')
    _txt(dr,(W//2,112),f'{report_type.upper()}  •  {date}',22,False,'#dbeafe','ma')
    p=overall['Predicted %']; a=overall['Actual %']; within=(p is not None and a is not None and a<=p)
    status='WITHIN TARGET' if within else 'ABOVE TARGET'; status_color='#34d399' if within else '#fb7185'
    _txt(dr,(W-330,52),'PERFORMANCE STATUS',18,True,'#cbd5e1','ma'); _txt(dr,(W-330,88),status,28,True,status_color,'ma')
    if p is not None and a is not None:_txt(dr,(W-330,128),f'Actual {a:.2f}%  vs  Predicted {p:.2f}%',18,False,'white','ma')

    cols=[('EDITION DATE',140),('MACHINE',190),('MACHINE IN-CHARGE',210),('PUBLICATION',150),('PO',130),('PRED QTY',130),('PRED %',115),('ACT QTY',130),('ACT %',115),('EXTRA',115),('REASON FOR EXTRA WASTE',475)]
    y=header_h+30; x=25
    for name,w in cols:
        dr.rectangle((x,y,x+w,y+table_head),fill=blue); _txt(dr,(x+w/2,y+table_head/2),name,15,True,'white','mm'); x+=w
    y+=table_head
    for i,(_,r) in enumerate(d.iterrows()):
        x=25; fill='white' if i%2==0 else light
        vals=[pd.to_datetime(r['Edition Date']).strftime('%d/%m/%Y') if pd.notna(r['Edition Date']) else '—',r['Machine'],r['Machine In-charge'],r['Publication'],f"{int(r['PO']):,}", '—' if pd.isna(r['Predicted Waste']) else f"{int(r['Predicted Waste']):,}", '—' if pd.isna(r['Predicted %']) else f"{r['Predicted %']:.2f}%",f"{int(r['Actual Waste']):,}",f"{r['Actual %']:.2f}%" if pd.notna(r['Actual %']) else '—','—' if pd.isna(r['Extra Waste']) else f"{int(r['Extra Waste']):,}",r['Reason for Extra Waste']]
        for j,((_,w),v) in enumerate(zip(cols,vals)):
            dr.rectangle((x,y,x+w,y+row_h),fill=fill,outline=grid,width=1)
            color=red if j in [8] and pd.notna(r['Predicted %']) and r['Actual %']>r['Predicted %'] else '#075985' if j in [6] else '#0f172a'
            if j==10:
                lines=textwrap.wrap(str(v),width=48)[:4]; block='\n'.join(lines); _txt(dr,(x+12,y+row_h/2),block,14,False,color,'lm')
            else:_txt(dr,(x+w/2,y+row_h/2),v,15,j in [5,6,7,8,9],color,'mm')
            x+=w
        y+=row_h
    sy=y+35; half=(W-75)//2
    for left,title,kind in [(25,'PREDICTED SUMMARY','pred'),(50+half,'ACTUAL SUMMARY','act')]:
        dr.rounded_rectangle((left,sy,left+half,sy+185),radius=18,fill='#f8fafc',outline=grid,width=2)
        dr.rounded_rectangle((left,sy,left+half,sy+50),radius=18,fill=blue); dr.rectangle((left,sy+32,left+half,sy+50),fill=blue)
        _txt(dr,(left+22,sy+25),title,18,True,'white','lm')
        machines=['Cromoman-C','Colorman-A','Colorman-B']; labels=['CROMO %','COL A %','COL B %']
        for k,(m,lbl) in enumerate(zip(machines,labels)):
            rec=summary[summary['Machine'].astype(str).str.upper()==m.upper()]
            val=None if rec.empty else rec.iloc[0]['Predicted %' if kind=='pred' else 'Actual %']
            cx=left+130+k*185; _txt(dr,(cx,sy+92),lbl,15,True,'#475569','ma'); _txt(dr,(cx,sy+130),'—' if pd.isna(val) else f'{val:.2f}%',26,True,'#2563eb' if kind=='pred' else green,'ma')
        total=overall['Predicted %' if kind=='pred' else 'Actual %']; bx=left+half-190
        dr.rounded_rectangle((bx,sy+65,bx+165,sy+165),radius=14,fill=navy if kind=='pred' else '#065f46')
        _txt(dr,(bx+82,sy+95),'TOTAL',15,True,'white','ma'); _txt(dr,(bx+82,sy+135),'—' if total is None else f'{total:.2f}%',28,True,'white','ma')
    out=BytesIO(); im.save(out,format='PNG',optimize=True); return out.getvalue()
