import bpy,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'viewer_realistic/heart.glb'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
corners=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=Vector(tuple(min(v[i] for v in corners) for i in range(3)));hi=Vector(tuple(max(v[i] for v in corners) for i in range(3)));c=(lo+hi)/2;size=max(hi-lo)
print('BOUNDS',list(lo),list(hi))
for o in objects:o.location-=c;o.scale*=4/size;o.location*=4/size
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world.color=(.05,.05,.05)
for pos,power in [((2,-5,5),650),((-3,-1,1),350),((1,4,3),700)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=4;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-8,1));s.camera=bpy.context.object;s.camera.data.type='ORTHO';s.camera.data.ortho_scale=4.8

s.camera.location=(0,-8,1);s.camera.rotation_euler=(-s.camera.location).to_track_quat('-Z','Y').to_euler()
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_distance=6
  area.spaces.active.shading.type='MATERIAL'
s.frame_start=1;s.frame_end=50;s.render.fps=60
for o in objects:
 base=o.scale.copy()
 for frame,factors in [(1,(1,1,1)),(12,(1,1,1)),(22,(.974,1.012,.982)),(34,(1,1,1)),(50,(1,1,1))]:
  o.scale=tuple(base[i]*factors[i] for i in range(3));o.keyframe_insert(data_path='scale',frame=frame)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Realistic_Heart.blend'))
