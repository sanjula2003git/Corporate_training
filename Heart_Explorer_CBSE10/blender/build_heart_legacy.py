"""Run with Blender --background --python build_heart.py. Educational schematic."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.35):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
wall=mat('Heart muscle • schematic',(0.57,.12,.23));rim=mat('Cut muscle surface',(.95,.42,.5));blue=mat('Oxygen-poor pathway',(.06,.34,.73));red=mat('Oxygen-rich pathway',(.9,.13,.26));gold=mat('Valve tissue',(.98,.78,.39));inner=mat('Inner muscle',(.34,.055,.12))
parts={}
def group(id,center):
    o=bpy.data.objects.new(id,None);bpy.context.collection.objects.link(o);o.location=center;o['part_id']=id;parts[id]=o;return o
def mesh(name,verts,faces,material,parent=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material)
    if parent:o.parent=parent
    for p in me.polygons:p.use_smooth=True
    return o
def bowl(id,c,r,thickness):
    parent=group(id,c);verts=[];faces=[];n=32;m=36
    # Back half of two ellipsoids, joined around their cut rim at y=0.
    for shrink in (0,thickness):
        rx,ry,rz=[v-shrink for v in r]
        for j in range(n+1):
            t=.012+(math.pi-.024)*j/n
            for k in range(m+1):
                a=math.pi*k/m
                verts.append((rx*math.sin(t)*math.cos(a),ry*math.sin(t)*math.sin(a),rz*math.cos(t)))
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
        t=.012+(math.pi-.024)*j/n
        for k in range(m+1):
            a=math.pi+math.pi*k/m;cv.append((r[0]*math.sin(t)*math.cos(a),r[1]*math.sin(t)*math.sin(a),r[2]*math.cos(t)))
    for j in range(n):
        for k in range(m):q=j*(m+1)+k;cf.append((q,q+1,q+m+2,q+m+1))
    cover=mesh(id+'_cover',cv,cf,wall,parent);cover['front_cover']=True
    for frame,scale in [(1,1),(10,.95 if 'atrium' in id else 1),(20,.94 if 'ventricle' in id else 1),(31,1),(40,1)]:
        parent.scale=(scale,1,scale);parent.keyframe_insert(data_path='scale',frame=frame)
    return parent
bowl('right_atrium',(-.65,0,.65),(.6,.5,.48),.065)
bowl('left_atrium',(.63,.04,.65),(.58,.5,.48),.065)
bowl('right_ventricle',(-.65,0,-.62),(.68,.6,.88),.095)
bowl('left_ventricle',(.60,.05,-.70),(.72,.64,1.03),.20)
def tube(id,points,r,material):
    parent=parts.get(id) or group(id,(0,0,0));curve=bpy.data.curves.new(id,'CURVE');curve.dimensions='3D';curve.resolution_u=16;curve.bevel_depth=r;curve.bevel_resolution=5;curve.use_fill_caps=True
    sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    obj=bpy.data.objects.new(id+'_vessel',curve);bpy.context.collection.objects.link(obj);obj.parent=parent;obj.data.materials.append(material)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.convert(target='MESH');obj.select_set(False)
    return obj
tube('vena_cava',[(-1.36,.20,1.9),(-1.32,.2,1.1),(-1.0,.2,.68)],.18,blue)
tube('vena_cava',[(-1.35,.25,-1.4),(-1.38,.25,-.1),(-1.08,.22,.55)],.18,blue)
tube('aorta',[(.53,.30,.05),(.38,.36,1.4),(.66,.38,2.12),(1.32,.4,2.12),(1.52,.5,1.5),(1.5,.63,-1.30)],.205,red)
for x in (.60,.89,1.17):tube('aorta',[(x,.38,2.10),(x-.08,.38,2.50)],.07,red)
tube('pulmonary_artery',[(-.32,-.23,-.05),(-.20,-.24,.95),(-.35,-.2,1.42),(-1.10,-.1,1.48),(-1.8,-.06,1.3)],.17,blue)
tube('pulmonary_artery',[(-.35,-.2,1.42),(.30,.15,1.52),(1.8,.2,1.35)],.15,blue)
for z in (.45,.8):
    tube('pulmonary_veins',[(1.86,.28,z),(1.1,.28,z),(.75,.25,.65)],.115,red)
    tube('pulmonary_veins',[(-1.86,.6,z),(-.5,.65,z),(.5,.48,.68)],.10,red)
parent=group('septum',(0,.03,-.25));bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=24);o=bpy.context.object;o.name='Septum_wall';o.parent=parent;o.location=(0,0,0);o.scale=(.105,.44,1.23);o.data.materials.append(rim)
for p in o.data.polygons:p.use_smooth=True
for id,c,r in [('tricuspid',(-.65,-.02,.14),.32),('mitral',(.63,-.02,.14),.30),('pulmonary_valve',(-.32,-.22,.06),.155),('aortic_valve',(.52,.23,.10),.18)]:
    parent=group(id,c)
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.025,major_segments=36,minor_segments=8)
    o=bpy.context.object;o.name=id+'_ring';o.parent=parent;o.location=(0,0,0);o.data.materials.append(gold)
    for sign in (-1,1):
        flap=mesh(id+'_flap_'+str(sign),[(0,-r,0),(0,r,0),(sign*r,0,0)],[(0,1,2)],gold,parent);flap['valve_flap']=True;flap['flap_sign']=sign
        sol=flap.modifiers.new('Thin flap','SOLIDIFY');sol.thickness=.018
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=40;scene.render.fps=48;scene.frame_set(1)
for o in bpy.data.objects:
    if o.type=='MESH':o.select_set(True)
    else:o.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'viewer'/'heart.glb'),export_format='GLB',export_extras=True,export_animations=True)
for o in bpy.data.objects:
    if o.get('front_cover'):o.hide_render=True;o.hide_set(True)
bpy.ops.object.camera_add(location=(4,-10,3.4));cam=bpy.context.object;direction=Vector((0,0,.35))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.8;scene.camera=cam
for loc,power,size in [((1,-5,6),900,5),((-4,-2,2),650,4),((1,4,5),1100,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.08,.08,.08);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'assets'/'heart-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender'/'CBSE_Heart.blend'));bpy.ops.render.render(write_still=True)
print('Heart GLB, Blender source and preview created.')
