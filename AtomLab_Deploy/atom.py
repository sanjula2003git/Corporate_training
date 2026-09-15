"""Restricted first-20-elements school model; not a stability simulator."""
ELEMENTS = [
 ('H','Hydrogen'),('He','Helium'),('Li','Lithium'),('Be','Beryllium'),('B','Boron'),
 ('C','Carbon'),('N','Nitrogen'),('O','Oxygen'),('F','Fluorine'),('Ne','Neon'),
 ('Na','Sodium'),('Mg','Magnesium'),('Al','Aluminium'),('Si','Silicon'),('P','Phosphorus'),
 ('S','Sulfur'),('Cl','Chlorine'),('Ar','Argon'),('K','Potassium'),('Ca','Calcium')]
PRESETS = {
 'Hydrogen-1':(1,0,1),'Helium-4':(2,2,2),'Carbon-12':(6,6,6),
 'Carbon-13':(6,7,6),'Carbon-14':(6,8,6),'Nitrogen-14':(7,7,7),
 'Oxygen-16':(8,8,8),'Sodium-23':(11,12,11),'Sodium ion Na⁺':(11,12,10),
 'Chloride ion Cl⁻':(17,18,18),'Calcium-40':(20,20,20)}

def describe(p,n,e):
    if any(type(x) is not int for x in (p,n,e)) or not (1<=p<=20 and 0<=n<=24 and 0<=e<=20):
        raise ValueError('Use 1–20 protons, 0–24 neutrons and 0–20 electrons.')
    symbol,name=ELEMENTS[p-1]
    remaining=e; shells=[]
    for capacity in (2,8,8,2):
        if not remaining:break
        count=min(capacity,remaining);shells.append(count);remaining-=count
    q=p-e
    return dict(p=p,n=n,e=e,symbol=symbol,name=name,mass=p+n,charge=q,shells=shells,
                state='Neutral atom' if q==0 else ('Positive ion (cation)' if q>0 else 'Negative ion (anion)'))
