"""Generate original vector teaching diagrams; no downloaded images required."""
from pathlib import Path
from html import escape
from content import LESSONS
OUT=Path(__file__).parent/'assets'
def text(x,y,s,size=22,color='#eef4ff',anchor='middle'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="Arial,sans-serif">{escape(s)}</text>'
def box(x,y,w,h,label,color='#315a83'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{color}"/>'+text(x+w/2,y+h/2+7,label)
def arrow(x1,y1,x2,y2,color='#88bfff'):
    return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="5" fill="none" marker-end="url(#arrow)"/>'
def heart(highlight=''):
    s=''
    for x,y,name in [(270,145,'Right atrium'),(520,145,'Left atrium'),(270,275,'Right ventricle'),(520,275,'Left ventricle')]:
        s+=box(x,y,220,95,name,'#963f61' if x==520 else '#315a83')
    s+=f'<rect x="497" y="137" width="16" height="242" rx="8" fill="{"#f5cd72" if highlight=="septum" else "#c78091"}"/>'
    s+=arrow(380,244,380,269)+arrow(630,244,630,269,'#f69db4')
    s+=text(505,412,'Front view: the person’s right is on your left.',17,'#abc0d8')
    return s
def diagram(id):
    if id in ('pump','chambers','septum'):
        s=heart(id)
        if id=='pump':s+=text(505,100,'Muscle contracts → blood moves',27,'#f5cd72')
        if id=='septum':s+=text(505,105,'SEPTUM: a separating wall',26,'#f5cd72')
        return s
    if id=='vessels':
        return heart()+box(30,50,230,60,'Body veins')+arrow(220,112,290,143)+text(155,140,'Venae cavae',17)+box(770,60,230,60,'From lungs','#963f61')+arrow(800,125,700,145,'#f69db4')+text(862,153,'Pulmonary veins',17)+arrow(270,335,125,335)+text(140,375,'To lungs: pulmonary artery',16)+arrow(740,330,895,330,'#f69db4')+text(868,372,'To body: aorta',17)
    if id=='valves':
        s=box(60,145,230,115,'Atrium')+box(410,145,240,115,'Ventricle')+box(770,145,220,115,'Artery','#963f61')
        s+=arrow(300,200,398,200)+arrow(660,200,758,200)
        s+=text(350,300,'Inlet valve',20,'#f5cd72')+text(705,300,'Outlet valve',20,'#f5cd72')
        return s+text(525,385,'Open for forward flow • Close against backflow',25)
    if id=='walls':
        s=''
        for x,width,label in [(260,14,'Right ventricle'),(745,35,'Left ventricle')]:
            s+=f'<ellipse cx="{x}" cy="225" rx="135" ry="140" fill="#251a36" stroke="#db8297" stroke-width="{width}"/>'+text(x,225,label,22)+text(x,410,'Lower pressure → lungs' if x==260 else 'Higher pressure → body',21)
        return s+text(525,60,'Compare wall thickness, not just chamber size',23,'#f5cd72')
    if id=='beat':
        s=''
        for i,(a,b) in enumerate([('1 · Fill','Relaxed ventricles fill'),('2 · Atria contract','Filling is completed'),('3 · Ventricles contract','Blood is ejected')]):
            x=35+i*345;s+=box(x,150,300,95,a)+text(x+150,290,b,20)
            if i<2:s+=arrow(x+305,195,x+335,195)
        return s+text(525,385,'Ventricles relax → the cycle repeats',26,'#f5cd72')
    if id=='pathway':
        labels=['Body','Vena cava','Right atrium','Right ventricle','Pulmonary artery','Lungs','Pulmonary veins','Left atrium','Left ventricle','Aorta']
        s=''
        for i,label in enumerate(labels):
            x=20+(i%5)*208;y=110+(i//5)*190
            s+=box(x,y,192,80,label,'#315a83' if i<5 else '#963f61')+text(x+96,y-16,str(i+1),22,'#f5cd72')
            if i%5<4:s+=arrow(x+194,y+40,x+205,y+40)
        return s+text(525,445,'Continue 5 → 6 at the lungs, then 10 → 1 at the body.',18)
    if id=='double':
        return box(400,175,240,100,'HEART','#963f61')+box(400,35,240,65,'LUNGS')+box(400,350,240,65,'BODY')+arrow(430,170,430,110)+arrow(610,105,610,165,'#f69db4')+arrow(610,285,610,340,'#f69db4')+arrow(430,340,430,285)+text(200,115,'Pulmonary circuit',24)+text(815,350,'Systemic circuit',24)+text(525,455,'Two heart passages in one complete circuit',23,'#f5cd72')
    s=''
    for x,label,thick in [(180,'Artery',30),(525,'Vein',12),(870,'Capillary',3)]:
        s+=f'<circle cx="{x}" cy="200" r="95" fill="#14263d" stroke="#da829a" stroke-width="{thick}"/>'+text(x,207,label,24)+text(x,350,{'Artery':'Away from heart','Vein':'Towards heart','Capillary':'One-cell-thick wall'}[label],22)
    return s+text(525,430,'Simplified cross-sections • not to scale',18,'#abc0d8')
for l in LESSONS:
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="490" viewBox="0 0 1050 490"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#f5cd72"/></marker></defs><rect width="1050" height="490" rx="26" fill="#102139"/>'+diagram(l['id'])+'</svg>'
    (OUT/(l['id']+'.svg')).write_text(svg,encoding='utf-8')
print('Created 10 original teaching diagrams.')
