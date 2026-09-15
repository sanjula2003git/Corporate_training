"""Run with Blender --background --python build_heart.py. Educational schematic."""
import bpy,math,json,random
import numpy as np
from mathutils import noise
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.35):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    p.inputs['Subsurface Weight'].default_value=.085
    p.inputs['Coat Weight'].default_value=.18
    p.inputs['Coat Roughness'].default_value=.28
    return m
wall=mat('Epicardium',(.38,.075,.085),.33)
rim=mat('Cut myocardium',(.52,.055,.085),.52)
blue=mat('Venous vessel tissue',(.35,.14,.15),.31)
red=mat('Arterial vessel tissue',(.50,.20,.18),.3)
gold=mat('Ivory valve leaflets',(.65,.43,.36),.34)
inner=mat('Endocardium',(.29,.035,.055),.46)
artery=mat('Coronary arteries',(.52,.022,.035),.29)
vein=mat('Coronary veins',(.055,.085,.24),.3)
fat=mat('Epicardial fat',(.65,.45,.28),.6)
parts={}
def group(id,center):
    o=bpy.data.objects.new(id,None);bpy.context.collection.objects.link(o);o.location=center;o['part_id']=id;parts[id]=o;return o
def mesh(name,verts,faces,material,parent=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material)
    if parent:o.parent=parent
    for p in me.polygons:p.use_smooth=True
    colors=me.color_attributes.new(name='Tissue',type='FLOAT_COLOR',domain='POINT')
    for v,d in zip(me.vertices,colors.data):
        q=v.co; n=noise.noise(q*13); fiber=math.sin(q.z*95+q.x*20+noise.noise(q*6)*5)
        f=max(.62,min(1.05,.88+.10*n+.045*fiber))
        d.color=(f,f*.96,f*.95,1)
    return o
def organic(id,t,a,r,inside):
    z=math.cos(t); st=math.sin(t)
    vent='ventricle' in id
    taper=(.78+.22*(z+1)/2) if vent else 1
    x=r[0]*st*math.cos(a)*taper
    y=r[1]*st*math.sin(a)*taper
    zz=r[2]*z
    if vent: x+=.15*(1-z)/2
    v=Vector((x,y,zz))
    relief=.004*noise.noise(v*25)+.007*noise.noise(v*7)
    if inside:relief+=.038*math.sin(t*22+a*5)*math.sin(a)**2+.018*math.sin(t*37-a*11)*math.sin(t)
    else:relief+=.003*math.sin(t*88+a*12)
    x*=1+relief+.022*math.sin(t*5+a*3);y*=1+relief+.028*math.sin(t*4-a*2)
    return (x,y,zz)

def bowl(id,c,r,thickness):
    parent=group(id,c);verts=[];faces=[];n=88;m=88
    # Back half of two ellipsoids, joined around their cut rim at y=0.
    for shrink in (0,thickness):
        rx,ry,rz=[v-shrink for v in r]
        for j in range(n+1):
            t=math.pi*j/n
            for k in range(m+1):
                a=math.pi*k/m
                verts.append(organic(id,t,a,(rx,ry,rz),shrink>0))
    count=(n+1)*(m+1)
    for layer in range(2):
        for j in range(n):
            for k in range(m):
                q=layer*count+j*(m+1)+k;f=(q,q+1,q+m+2,q+m+1);faces.append(f if layer==0 else tuple(reversed(f)))
    for j in range(n):
        for k in (0,m):
            a=j*(m+1)+k;b=(j+1)*(m+1)+k;faces.append((a,b,b+count,a+count))
    o=mesh(id+'_cutaway',verts,faces,wall,parent);o.data.materials.append(rim);o.data.materials.append(inner)
    for i,p in enumerate(o.data.polygons):p.material_index=0 if i<n*m else (2 if i<2*n*m else 1)
    # Front cover can be hidden in the app to expose the chambers.
    cv=[];cf=[]
    for j in range(n+1):
        t=math.pi*j/n
        for k in range(m+1):
            a=math.pi+math.pi*k/m;cv.append(organic(id,t,a,r,False))
    for j in range(n):
        for k in range(m):q=j*(m+1)+k;cf.append((q,q+1,q+m+2,q+m+1))
    cover=mesh(id+'_cover',cv,cf,wall,parent);cover['front_cover']=True
    for frame,scale in [(1,1),(10,.95 if 'atrium' in id else 1),(20,.94 if 'ventricle' in id else 1),(31,1),(40,1)]:
        parent.scale=(scale,1,scale);parent.keyframe_insert(data_path='scale',frame=frame)
    return parent
bowl('right_atrium',(-.58,.04,.60),(.62,.52,.59),.065)
bowl('left_atrium',(.54,.12,.66),(.58,.55,.55),.065)
bowl('right_ventricle',(-.48,0,-.43),(.67,.65,1.02),.095)
bowl('left_ventricle',(.49,.08,-.51),(.72,.7,1.18),.20)
def tube(id,points,r,material,hollow=True,name=None):
    parent=parts.get(id) or group(id,(0,0,0))
    pts=[Vector(p) for p in points]; samples=[]
    for i in range(len(pts)-1):
        p0=pts[max(0,i-1)];p1=pts[i];p2=pts[i+1];p3=pts[min(len(pts)-1,i+2)]
        for j in range(12):
            t=j/12
            samples.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    samples.append(pts[-1]);vs=[];fs=[];N=28
    prev=None
    for i,p in enumerate(samples):
        tangent=(samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]).normalized()
        axis=Vector((0,1,0)) if abs(tangent.y)<.92 else Vector((1,0,0))
        u=tangent.cross(axis).normalized();v=tangent.cross(u).normalized()
        if prev is not None and u.dot(prev)<0:u=-u;v=-v
        prev=u
        for layer in range(2 if hollow else 1):
            rr=r*(1 if layer==0 else .76)*(1+.035*math.sin(i*.15)+.018*noise.noise(p*9))
            for j in range(N):
                angle=j*2*math.pi/N
                co=p+rr*(u*math.cos(angle)+v*math.sin(angle))-parent.location
                vs.append(tuple(co))
    stride=N*(2 if hollow else 1)
    for i in range(len(samples)-1):
        for layer in range(2 if hollow else 1):
            for j in range(N):
                a=i*stride+layer*N+j;b=i*stride+layer*N+(j+1)%N
                f=(a,b,b+stride,a+stride);fs.append(f if layer==0 else tuple(reversed(f)))
    if hollow:
        for i in [0,len(samples)-1]:
            for j in range(N):
                a=i*stride+j;b=i*stride+(j+1)%N;fs.append((a,b,b+N,a+N))
    o=mesh(name or id+'_vessel',vs,fs,material,parent)
    if hollow:
        o.data.materials.append(inner);o.data.materials.append(gold)
        for f in o.data.polygons:
            if f.index >=(len(samples)-1)*N*2:f.material_index=2
            elif (f.index//N)%2:f.material_index=1
    return o
tube('vena_cava',[(-.92,.27,1.90),(-.90,.3,1.15),(-.83,.32,.65)],.23,blue)
tube('vena_cava',[(-1.0,.39,-1.0),(-1.10,.40,-.1),(-.85,.35,.50)],.23,blue)
tube('aorta',[(.38,.20,.15),(.24,.18,1.05),(.34,.2,1.85),(.8,.28,2.03),(1.12,.42,1.70),(1.15,.64,.1)],.25,red)
for x in (.36,.60,.82):tube('aorta',[(x,.24,1.90),(x-.07,.24,2.38)],.10,red)
tube('pulmonary_artery',[(-.28,-.15,.08),(-.15,-.29,.78),(-.18,-.18,1.35),(-.72,.18,1.48),(-1.38,.3,1.34)],.22,blue)
tube('pulmonary_artery',[(-.18,-.18,1.35),(.4,.08,1.48),(1.48,.15,1.30)],.18,blue)
for z in (.45,.8):
    tube('pulmonary_veins',[(1.48,.28,z),(1.1,.28,z),(.75,.25,.65)],.115,red)
    tube('pulmonary_veins',[(-1.48,.6,z),(-.5,.65,z),(.5,.48,.68)],.10,red)
parent=group('septum',(0,.03,-.25));bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=24);o=bpy.context.object;o.name='Septum_wall';o.parent=parent;o.location=(0,0,0);o.scale=(.105,.44,1.23);o.data.materials.append(rim)
for p in o.data.polygons:p.use_smooth=True
for id,c,r in [('tricuspid',(-.58,.01,.13),.32),('mitral',(.54,.08,.15),.30),('pulmonary_valve',(-.28,-.15,.18),.17),('aortic_valve',(.38,.20,.22),.18)]:
    parent=group(id,c);parent['internal_detail']=True
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.023,major_segments=48,minor_segments=10)
    o=bpy.context.object;o.name=id+'_annulus';o.parent=parent;o.location=(0,0,0);o.data.materials.append(gold)
    for p in o.data.polygons:p.use_smooth=True
    count=2 if id=='mitral' else 3
    for k in range(count):
        vs=[];opened=[];fs=[];nr=10;na=16
        for j in range(nr+1):
            t=j/nr
            for h in range(na+1):
                a=2*math.pi*(k+h/na)/count
                rr=r*(.015+.985*t)
                z=-.06*math.sin(math.pi*t)-.07*(1-t)
                vs.append((rr*math.cos(a),rr*math.sin(a),z))
                ro=r*(.76+.24*t)
                opened.append((ro*math.cos(a),ro*math.sin(a),-.17*(1-t)))
        for j in range(nr):
            for h in range(na):
                q=j*(na+1)+h;fs.append((q,q+1,q+na+2,q+na+1))
        o=mesh(id+'_leaflet_'+str(k+1),vs,fs,gold,parent);o['valve_leaflet']=True
        o.shape_key_add(name='Basis');key=o.shape_key_add(name='Open')
        for d,co in zip(key.data,opened):d.co=co
        for frame,value in [(1,1),(15,1),(19,0),(30,0),(36,1),(40,1)]:
            key.value=(1-value) if 'valve' in id else value;key.keyframe_insert('value',frame=frame)
    if id in ['mitral','tricuspid']:
        vent='left_ventricle' if id=='mitral' else 'right_ventricle'
        for k in range(2):
            base=(c[0]+(-.16 if k==0 else .16),c[1]+.23,c[2]-.65)
            tip=(base[0],base[1]-.025,base[2]+.22)
            muscle=tube(vent,[base,tip],.048,wall,False,'Papillary_muscle');muscle['internal_detail']=True
            for j in range(7):
                a=(k*.5+j/14)*2*math.pi
                end=(c[0]+r*.6*math.cos(a),c[1]+r*.6*math.sin(a),c[2]-.07)
                cord=tube(id,[tip,((tip[0]+end[0])/2,(tip[1]+end[1])/2,(tip[2]+end[2])/2),end],.006,gold,False,'Chordae_tendineae');cord['internal_detail']=True

# Raised trabeculae line the ventricular walls, visible only in cutaway mode.
random.seed(7)
for id,c,r,thick in [('right_ventricle',(-.48,0,-.43),(.67,.65,1.02),.095),('left_ventricle',(.49,.08,-.51),(.72,.7,1.18),.20)]:
    ri=tuple(v-thick for v in r)
    for j in range(31):
        a=.18+j*2.78/31;ts=[.70+h*.1 for h in range(17)]
        points=[tuple(Vector(c)+Vector(organic(id,t,a+.11*math.sin(t*4+j),ri,True))) for t in ts]
        o=tube(id,points,.021+(j%4)*.004,inner,False,'Trabeculae');o['internal_detail']=True
    # Fine coronary branches follow the outside surface rather than floating in space.
    for side in range(3):
        a=math.pi+(.42 if id=='right_ventricle' else 2.4)+side*.12
        pts=[tuple(Vector(c)+Vector(organic(id,.55+h*.095,a+.08*math.sin(h*.3),tuple(v+.015 for v in r),False))) for h in range(23)]
        o=tube(id,pts,.021 if side==0 else .012,artery if side!=1 else vein,False,'Coronary_surface_vessel');o['exterior_detail']=True
        for h in (6,11,16):
            t=.55+h*.095
            branch=[tuple(Vector(c)+Vector(organic(id,t+k*.025,a+k*.045,tuple(v+.016 for v in r),False))) for k in range(8)]
            o=tube(id,branch,.007,artery,False,'Coronary_branch');o['exterior_detail']=True

# A continuous outer envelope joins the four chambers into a single organ.
# The cutaway keeps the four individually selectable internal chamber walls.
for o in list(bpy.data.objects):
    if o.get('front_cover') or o.get('exterior_detail'):bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.endswith('_cutaway'):o['internal_detail']=True

def envelope(t,a,offset=0):
    z=math.cos(t);st=math.sin(t)
    width=(1.26+offset)*st*(.87+.20*z)
    x=width*math.cos(a)+.12*(1-z)
    y=(.73+offset)*st*math.sin(a)+.09
    zz=.12+1.48*z
    p=Vector((x,y,zz));d=.008*noise.noise(p*11)+.003*math.sin(t*80+a*15)
    return (x*(1+d),y*(1+d),zz)

verts={k:[] for k in ['right_atrium','left_atrium','right_ventricle','left_ventricle']};faces={k:[] for k in verts}
nt=100;na=144
for i in range(nt):
    for j in range(na):
        t=(i+.5)*math.pi/nt;a=(j+.5)*2*math.pi/na
        c=envelope(t,a);side='right' if c[0]<.12 else 'left';region='atrium' if c[2]>.72 else 'ventricle';id=side+'_'+region
        # Separate patches share exactly matching boundary positions.
        q=len(verts[id]);center=parts[id].location
        verts[id].extend([tuple(Vector(envelope(tt,aa))-center) for tt,aa in [(i*math.pi/nt,j*2*math.pi/na),((i+1)*math.pi/nt,j*2*math.pi/na),((i+1)*math.pi/nt,(j+1)*2*math.pi/na),(i*math.pi/nt,(j+1)*2*math.pi/na)]])
        faces[id].append((q,q+1,q+2,q+3))
for id in verts:
    o=mesh(id+'_cover',verts[id],faces[id],wall,parts[id]);o['front_cover']=True
    # Weld patch vertices and recalculate normals for a continuous smooth surface.
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

for side,a0 in [('front',4.72),('back',1.6)]:
    for k in range(2):
        coords=[envelope(.74+i*.068,a0+.20*math.sin(i*.13)+k*.055,.019) for i in range(29)]
        o=tube('left_ventricle',coords,.025 if k==0 else .017,artery if k==0 else vein,False,'Coronary_'+side);o['exterior_detail']=True
        for n in (3,8,14,19,24):
            for direction in [-1,1]:
                coords=[envelope(.74+n*.068+i*.015,a0+.2*math.sin(n*.13)+k*.055+direction*(i*.06+.035*math.sin(i*.65+n)),.020) for i in range(7+n%5)]
                o=tube('left_ventricle',coords,.010 if k==0 else .007,artery if k==0 else vein,False,'Coronary_branch');o['exterior_detail']=True
# Coronary groove around the base.
coords=[envelope(.82,math.pi+j*math.pi/50,.018) for j in range(51)]
o=tube('right_atrium',coords,.028,artery,False,'Coronary_base');o['exterior_detail']=True

# Embedded PBR tissue maps: mottled albedo, fibrous microrelief and wetness.
N=768
Y,X=np.mgrid[0:N,0:N].astype(np.float32)/N
rng=np.random.default_rng(41)
def field(freq,terms=12):
 out=np.zeros((N,N),np.float32)
 for _ in range(terms):
  ax=int(rng.integers(1,freq+1));ay=int(rng.integers(1,freq+1));phase=rng.random()*math.tau
  out+=np.sin(math.tau*(X*ax+Y*ay)+phase)
 return out/math.sqrt(terms)
coarse=field(5);medium=field(22);fine=field(100);warp=.16*np.sin(math.tau*Y*3)+.05*medium
fibers=np.sin(math.tau*(X*53+Y*9)+warp*5)
pores=field(210)
def image(name,rgb,linear=False):
 im=bpy.data.images.new(name,width=N,height=N)
 if linear:im.colorspace_settings.name='Non-Color'
 rgba=np.ones((N,N,4),np.float32);rgba[:,:,:3]=np.clip(rgb,0,1)
 im.pixels.foreach_set(rgba.ravel());im.pack();return im
for material,base,variation,roughness in [
 (wall,(.43,.16,.155),.12,.38),(rim,(.49,.12,.13),.10,.40),
 (inner,(.40,.105,.115),.09,.33),(red,(.62,.30,.27),.12,.30),
 (blue,(.48,.235,.245),.11,.32),(gold,(.77,.57,.46),.065,.36)]:
 skin=.50*coarse+.25*medium+.10*fine+.055*fibers
 rgb=np.stack([base[k]+variation*skin*(1 if k==0 else .60) for k in range(3)],axis=-1)
 # Sparse darker connective streaks remain subtle, rather than painted vessel tubes.
 streak=np.power(np.maximum(0,np.sin(math.tau*(X*11+Y*4)+medium*.6)),22)
 rgb-=streak[:,:,None]*np.array([.035,.025,.021])
 albedo=image(material.name+' • tissue colour',rgb)
 height=.12*medium+.055*fine+.018*fibers+.022*pores
 dy,dx=np.gradient(height);strength=2.8 if material!=gold else 1.6
 normal=np.stack([-dx*strength,-dy*strength,np.ones_like(X)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
 norm=image(material.name+' • fibres',normal*.5+.5,True)
 rough=np.clip(roughness+.045*coarse+.025*fine,.20,.56)
 wet=image(material.name+' • roughness',np.stack([rough,rough,rough],axis=-1),True)
 nodes=material.node_tree.nodes;links=material.node_tree.links;p=nodes.get('Principled BSDF')
 color=nodes.new('ShaderNodeTexImage');color.image=albedo;links.new(color.outputs['Color'],p.inputs['Base Color'])
 tex=nodes.new('ShaderNodeTexImage');tex.image=norm
 bump=nodes.new('ShaderNodeNormalMap');bump.inputs['Strength'].default_value=.22
 links.new(tex.outputs['Color'],bump.inputs['Color']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
 tex=nodes.new('ShaderNodeTexImage');tex.image=wet;links.new(tex.outputs['Color'],p.inputs['Roughness'])
 p.inputs['Coat Weight'].default_value=.25;p.inputs['Coat Roughness'].default_value=.26
 p.inputs['Subsurface Weight'].default_value=.12

for o in bpy.data.objects:
    if o.type!='MESH' or not len(o.data.vertices):continue
    uv=o.data.uv_layers.new(name='TissueUV')
    for loop in o.data.loops:
        co=o.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=(math.atan2(co.y,co.x)/(2*math.pi)+.5,co.z*.3+.5)

scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=40;scene.render.fps=48;scene.frame_set(1)
for o in bpy.data.objects:
    if o.type=='MESH':o.select_set(True)
    else:o.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'viewer_realistic'/'teaching-heart.glb'),export_format='GLB',export_extras=True,export_animations=True,export_morph=True,export_apply=False,export_vertex_color='ACTIVE')
for o in bpy.data.objects:
    if o.get('front_cover') or o.get('exterior_detail'):o.hide_render=True;o.hide_set(True)
bpy.ops.object.camera_add(location=(2.6,-10,2.4));cam=bpy.context.object;direction=Vector((0,0,.35))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.8;scene.camera=cam
for loc,power,size in [((1,-5,6),650,5),((-4,-2,2),380,4),((1,4,5),850,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.018,.025,.045);scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'assets'/'heart-interior-lifelike.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'Lifelike_Interior.blend'));bpy.ops.render.render(write_still=True)

print('Textured interior GLB, Blender source and preview created.')
