"""Generate original, local SVG lesson illustrations without network dependencies."""
from pathlib import Path
from math import sin, cos, pi
from html import escape
from content import LESSONS
OUT=Path(__file__).resolve().parent/'assets';OUT.mkdir(exist_ok=True)
INK='#eaf4fc';MUTED='#9eb7cb';P='#f78679';N='#e7bf6c';E='#6dcbff';GREEN='#8ae0c9'
def text(x,y,t,size=23,color=INK,anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="Segoe UI,Arial,sans-serif">{escape(str(t))}</text>'
def ball(x,y,r,kind,label=True):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#{kind})"/>'+ (text(x,y+r*.34,{'p':'+','n':'0','e':'−'}[kind],r, '#102137','middle') if label else '')
def line(x,y,a,b,color=MUTED):return f'<path d="M{x} {y} L{a} {b}" stroke="{color}" stroke-width="2" fill="none"/>'
def atom(x,y,p,n,e,r=120):
    result=''
    remaining=e
    shell_labels=[]
    for k,cap in enumerate((2,8,8,2)):
        if remaining<=0:break
        count=min(cap,remaining);remaining-=count;rr=r*(.68+.32*k)
        shell_labels.append((k,count,rr))
        result+=f'<circle cx="{x}" cy="{y}" r="{rr}" fill="none" stroke="#395b72" stroke-width="2"/>'
        for j in range(count):
            a=2*pi*j/count+.35*k
            result+=ball(x+rr*cos(a),y+rr*sin(a),10,'e')
    count=p+n
    for i in range(count):
        a=i*2.39996;rr=8*(i**.5)
        result+=ball(x+rr*cos(a),y+rr*sin(a),11,'p' if i<p else 'n')
    # Name each ring at a distinct point, using a leader to the actual shell.
    for k,count,rr in shell_labels:
        a=-pi/2-.45+k*.45
        ax=x+rr*cos(a);ay=y+rr*sin(a)
        tx=x-130+k*105;ty=max(140,y-r*1.32-22)
        result+=line(ax,ay,tx,ty+6,GREEN)+text(tx,ty,f"{'KLMN'[k]} shell",16,GREEN,'middle')
    outer=max([v[2] for v in shell_labels],default=45)
    result+=line(x,y+35,x,y+outer+24)+text(x,y+outer+43,'Nucleus',17,INK,'middle')
    return result
def lines(x,y,items,color=INK,size=23,gap=36):return ''.join(text(x,y+i*gap,s,size,color) for i,s in enumerate(items))
def compare(left,right,caption):
    return atom(275,255,*left[:3],110)+atom(805,255,*right[:3],110)+text(275,430,left[3],27,INK,'middle')+text(805,430,right[3],27,INK,'middle')+text(540,495,caption,22,GREEN,'middle')
for l in LESSONS:
    id=l['id'];body=''
    if id=='atom':
        body=ball(360,275,69,'e',False)+ball(515,240,88,'p',False)+ball(655,310,69,'e',False)
        body+=line(320,230,235,185)+text(120,174,'Hydrogen atom',21,E)+line(550,182,710,162)+text(710,156,'Oxygen atom',21,P)+line(690,345,820,370)+text(805,400,'Hydrogen atom',21,E)
        body+=text(360,285,'H',36,INK,'middle')+text(515,252,'O',44,INK,'middle')+text(655,320,'H',36,INK,'middle')
        body+=text(540,425,'One water molecule · H₂O',30,INK,'middle')+text(540,472,'2 hydrogen atoms + 1 oxygen atom',23,GREEN,'middle')
    elif id=='structure':
        body=atom(370,285,2,2,2,175)+line(380,275,655,225)+lines(680,220,['Nucleus','2 protons + 2 neutrons'],gap=33)
        body+=line(250,270,190,405)+text(70,444,'Electrons outside',24,E)+text(700,370,'Helium-4',30,GREEN)
    elif id in ('proton','neutron','electron'):
        kind={'proton':'p','neutron':'n','electron':'e'}[id];colour={'p':P,'n':N,'e':E}[kind]
        body=line(290,420,290,451,colour)+text(290,480,id.title(),24,colour,'middle')+ball(290,300,120,kind)+lines(515,228,{'p':['PROTON','Charge: +1','Approximate mass: 1 u','Location: nucleus','Defines the element'], 'n':['NEUTRON','Charge: 0','Approximate mass: 1 u','Location: nucleus','Distinguishes isotopes'], 'e':['ELECTRON','Charge: −1','Mass: about 1/1836 of a proton','Location: outside the nucleus','Changes affect electric charge']}[kind],colour,gap=48)
    elif id=='atomic_number':
        body=atom(285,290,8,8,8,132)+text(665,265,'8',105,GREEN,'middle')+text(785,265,'O',105,INK,'middle')
        body+=lines(545,340,['Z = 8 protons','Oxygen, even if neutrons','or electrons change.'])
    elif id=='mass_number':
        body=ball(195,250,55,'p')+text(195,350,'8 protons',26,P,'middle')+text(350,263,'+',44)+ball(520,250,55,'n')+text(520,350,'10 neutrons',26,N,'middle')+text(665,263,'=',44)+text(825,280,'18',90,GREEN,'middle')+text(825,350,'Mass number A',26,INK,'middle')+text(540,475,'A = Z + N       N = A − Z',30,INK,'middle')
    elif id=='counting':
        body=text(195,285,'23',43,GREEN)+text(195,358,'11',43,E)+text(275,342,'Na',105)+text(425,270,'+',45,P)
        body+=line(235,269,485,197,GREEN)+text(360,178,'A: mass number',19,GREEN)+line(234,350,455,413,E)+text(310,440,'Z: atomic number',19,E)+line(445,255,500,153,P)+text(465,142,'Ion charge',19,P)
        body+=lines(560,215,['Protons = 11','Neutrons = 23 − 11 = 12','Electrons = 11 − 1 = 10'],gap=68)+text(540,482,'Read A and Z first. Then account for charge.',24,GREEN,'middle')
    elif id=='isotopes':body=compare((6,6,6,'Carbon-12: 6 p + 6 n'),(6,8,6,'Carbon-14: 6 p + 8 n'),'Same proton number · different neutron number')
    elif id=='isobars':body=compare((6,8,6,'Carbon-14: 6 p + 8 n'),(7,7,7,'Nitrogen-14: 7 p + 7 n'),'Same mass number 14 · different elements')
    elif id=='shells':
        body=atom(300,290,11,12,11,115)+lines(610,220,['Sodium: 2, 8, 1','K shell: 2 electrons','L shell: 8 electrons','M shell: 1 electron','One valence electron'],gap=49)
    elif id=='ions':body=compare((11,12,11,'Na: 11 p, 11 e'),(11,12,10,'Na⁺: 11 p, 10 e'),'Lose one electron → charge becomes +1')
    else:
        for x,kind,label,desc in [(220,'p','Protons','Element identity'),(540,'n','Neutrons','Isotope identity'),(860,'e','Electrons','Charge balance')]:
            body+=ball(x,245,68,kind)+text(x,365,label,30,INK,'middle')+text(x,410,desc,23,GREEN,'middle')
        body+=text(540,491,'Z = p        A = p + n        charge = p − e',28,INK,'middle')
    defs=''.join(f'<radialGradient id="{k}" cx="30%" cy="25%"><stop stop-color="#ffffff" stop-opacity=".95"/><stop offset=".38" stop-color="{c}"/><stop offset="1" stop-color="{c}" stop-opacity=".65"/></radialGradient>' for k,c in [('p',P),('n',N),('e',E)])
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="650" viewBox="0 0 1080 650" role="img" aria-labelledby="title desc"><title id="title">{escape(l["title"])}</title><desc id="desc">{escape(l["example"])}</desc><defs>{defs}<radialGradient id="bg"><stop stop-color="#213b50"/><stop offset="1" stop-color="#101e30"/></radialGradient></defs><rect width="1080" height="650" rx="24" fill="url(#bg)"/>'+text(45,55,'ATOMLAB / '+l['title'].upper(),19,GREEN)+text(45,90,l['subtitle'],23,MUTED)+body+((''.join(ball(x,580,15,k)+text(x+25,586,label,18,c) for x,k,label,c in [(75,'p','Proton (+)',P),(320,'n','Neutron (0)',N),(590,'e','Electron (−)',E)])+text(75,626,'Rings show electron shells; the central cluster is the nucleus.',18,MUTED)) if id!='atom' else text(75,593,'H = hydrogen atom     O = oxygen atom     H₂O = water molecule',22,GREEN))+text(1030,635,'Illustrative • not to scale',13,MUTED,'end')+'</svg>'
    (OUT/(id+'.svg')).write_text(svg,encoding='utf-8')
print('Created 13 original lesson illustrations.')
