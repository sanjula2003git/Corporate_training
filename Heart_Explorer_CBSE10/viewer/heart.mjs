import * as THREE from './three.mjs';
import {OrbitControls} from './controls.mjs';
import {GLTFLoader} from './loader.mjs';
const $=id=>document.getElementById(id),stage=$('stage');
const send=(type,data={})=>parent.postMessage({isStreamlitMessage:true,type,...data},'*');
let parts=[],model=null,running=true,cutaway=true,labels=true,flow=false,bpm=72,selected='',phase=0,last=performance.now(),initialized=false,down=null;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,.01,150),renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;stage.prepend(renderer.domElement);renderer.domElement.tabIndex=0;renderer.domElement.setAttribute('role','img');renderer.domElement.setAttribute('aria-label','Interactive cutaway heart. Drag to rotate and scroll to zoom.');
scene.add(new THREE.HemisphereLight(0xe8f3ff,0x261c28,1.5));
for(const [pos,power,color] of [[[3,5,7],3,0xffe0df],[[-4,1,4],2,0xa3caff],[[2,4,-5],3,0xffb2bb]]){const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);}
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.autoRotate=false;controls.zoomSpeed=2.7;controls.minDistance=.5;controls.maxDistance=25;controls.zoomToCursor=true;
const groups=new Map(),meshes=[],covers=[],interiors=[],exteriors=[],leaflets=[],flaps=[],tags=new Map(),lines=new Map(),buttons=new Map();
const anchors={right_atrium:[-.58,-.2,.65],left_atrium:[.54,-.2,.7],right_ventricle:[-.48,-.25,-.43],left_ventricle:[.65,-.25,-.65],septum:[0,-.15,-.3],vena_cava:[-.92,.27,1.75],pulmonary_artery:[-1.2,.2,1.4],pulmonary_veins:[1.4,.28,.6],aorta:[.7,.28,2.03],tricuspid:[-.58,.01,.13],mitral:[.54,.08,.15],pulmonary_valve:[-.28,-.15,.18],aortic_valve:[.38,.20,.22]};
const vec=p=>new THREE.Vector3(p[0],p[2],-p[1]);
function reset(){camera.position.set(.45,.6,6.7);controls.target.set(0,.38,0);controls.update();}
reset();
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(!document.fullscreenElement)send('streamlit:setFrameHeight',{height:document.body.scrollHeight+4});}
new ResizeObserver(resize).observe(stage);
function sync(){
 $('beat').textContent=running?'⏸ Pause beat':'▶ Play beat';$('cut').textContent='Cutaway: '+(cutaway?'on':'off');$('labelsToggle').textContent='Labels: '+(labels?'on':'off');$('flow').textContent='Flow dots: '+(flow?'on':'off');$('bpm').textContent=bpm+' bpm';$('speed').value=bpm;
 for(const c of covers)c.visible=!cutaway;
 for(const c of interiors)c.visible=cutaway;
 for(const c of exteriors)c.visible=!cutaway;
 for(const [id,o] of groups)if(id==='septum'||id.includes('valve')||['tricuspid','mitral'].includes(id))o.visible=cutaway;
}
function emit(ask=false){send('streamlit:setComponentValue',{value:{event_id:Date.now()+'-'+Math.random(),part:selected,ask,running,cutaway,labels,bpm,flow},dataType:'json'});}
function choose(id){selected=id;const p=parts.find(p=>p.id===id);if(!p)return;$('partName').textContent=p.title;$('description').textContent=p.description;$('ask').disabled=false;for(const [k,t] of tags)t.classList.toggle('active',k===id);for(const [k,t] of buttons)t.classList.toggle('active',k===id);highlight(id);emit();}
function highlight(id){for(const m of meshes)for(const mat of(Array.isArray(m.material)?m.material:[m.material])){if(mat.emissive){mat.emissive.set(m.userData.part===id?0x481d30:0);mat.emissiveIntensity=.5;}}}
function hover(id){const p=parts.find(p=>p.id===id);$('tip').replaceChildren();if(p){const b=document.createElement('b');b.textContent=p.title;$('tip').append(b,document.createTextNode(p.description));}$('tip').style.display=p?'block':'none';highlight(id||selected);}
function populate(){
 if(tags.size)return;
 for(const p of parts){const b=document.createElement('button');b.textContent=p.title;b.onclick=()=>choose(p.id);b.onmouseenter=()=>hover(p.id);b.onmouseleave=()=>hover('');$('topics').append(b);buttons.set(p.id,b);
 const tag=b.cloneNode(true);tag.className='tag';tag.onclick=()=>choose(p.id);tag.onmouseenter=()=>hover(p.id);tag.onmouseleave=()=>hover('');$('labels').append(tag);tags.set(p.id,tag);
 const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('stroke','#e5b3c2');line.setAttribute('stroke-opacity','.45');$('leaders').append(line);lines.set(p.id,line);}
 resize();
}
$('beat').onclick=()=>{running=!running;sync();emit();};$('cut').onclick=()=>{cutaway=!cutaway;sync();emit();};$('labelsToggle').onclick=()=>{labels=!labels;sync();emit();};$('flow').onclick=()=>{flow=!flow;sync();emit();};$('speed').oninput=e=>{bpm=+e.target.value;$('bpm').textContent=bpm+' bpm';};$('speed').onchange=()=>emit();$('reset').onclick=reset;
$('full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{$('description').textContent='Fullscreen is unavailable in this browser. You can still zoom and rotate.';}};
document.addEventListener('fullscreenchange',()=>{$('full').textContent=document.fullscreenElement?'Exit full screen':'Full screen';resize();});
$('ask').onclick=()=>emit(true);
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
function visible(o){while(o){if(!o.visible)return false;o=o.parent;}return true;}
function pick(e){const r=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(mouse,camera);return ray.intersectObjects(meshes,false).find(x=>visible(x.object))?.object.userData.part;}
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(down&&Math.hypot(e.clientX-down[0],e.clientY-down[1])<5){const id=pick(e);if(id)choose(id);}down=null;});renderer.domElement.addEventListener('pointermove',e=>{if(!e.buttons)hover(pick(e));});renderer.domElement.addEventListener('pointerleave',()=>hover(''));
window.addEventListener('message',e=>{if(e.source!==parent||e.data.type!=='streamlit:render')return;parts=e.data.args.parts||[];if(!initialized){({running=true,cutaway=true,labels=true,bpm=72,flow=false}=e.data.args);initialized=true;}populate();sync();});
send('streamlit:componentReady',{apiVersion:1});resize();
new GLTFLoader().load('./heart.glb?v=20260915-tissue3',g=>{model=g.scene;scene.add(model);model.traverse(o=>{if(o.userData.part_id)groups.set(o.userData.part_id,o);if(o.userData.front_cover)covers.push(o);if(o.userData.internal_detail)interiors.push(o);if(o.userData.exterior_detail)exteriors.push(o);if(o.userData.valve_leaflet)leaflets.push(o);if(o.userData.valve_flap)flaps.push(o);if(o.isMesh){let p=o,id='';while(p){id=id||p.userData.part_id;p=p.parent;}o.userData.part=id;o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const mat of(Array.isArray(o.material)?o.material:[o.material]))mat.side=THREE.DoubleSide;meshes.push(o);}});model.updateMatrixWorld(true);for(const o of [...covers,...exteriors])model.attach(o);sync();$('loading').style.display='none';},undefined,()=>{$('loading').textContent='The model could not load. Ensure viewer/heart.glb is included in the deployment.';});
const routes=[{color:0x5aa8ff,points:[[-1.35,.1,1.9],[-1.3,.1,1.1],[-.7,-.14,.65],[-.65,-.14,-.55],[-.32,-.27,.04],[-.2,-.27,.95],[-.35,-.23,1.42],[-1.8,-.06,1.3]]},{color:0xff5a87,points:[[1.85,.15,.8],[1.1,.15,.8],[.63,-.15,.65],[.6,-.15,-.6],[.52,.19,.10],[.38,.23,1.4],[.66,.28,2.12],[1.32,.28,2.12],[1.52,.4,1.5],[1.5,.5,-1.3]]}];
const dots=[];for(const r of routes){const curve=new THREE.CatmullRomCurve3(r.points.map(vec));for(let i=0;i<8;i++){const o=new THREE.Mesh(new THREE.SphereGeometry(.045,10,8),new THREE.MeshBasicMaterial({color:r.color,depthTest:false}));o.renderOrder=5;scene.add(o);dots.push({o,curve,offset:i/8});}}
let flowTime=0;
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,.06);last=now;if(running){phase=(phase+dt*bpm/60)%1;flowTime+=dt*.12;}
 const atrial=phase>.18&&phase<.36?Math.sin((phase-.18)/.18*Math.PI):0,ventricular=phase>.4&&phase<.75?Math.sin((phase-.4)/.35*Math.PI):0;
 for(const [id,o] of groups){if(id.includes('atrium'))o.scale.setScalar(1-.025*atrial);if(id.includes('ventricle'))o.scale.setScalar(1-.035*ventricular);}
 if(model){model.scale.set(1-.014*ventricular,1-.022*ventricular,1+.01*ventricular);}
 for(const f of leaflets){let p=f.parent;while(p&&!p.userData.part_id)p=p.parent;const outlet=['pulmonary_valve','aortic_valve'].includes(p?.userData.part_id);const openness=outlet?ventricular:1-ventricular;const i=f.morphTargetDictionary?.Open;if(i!==undefined)f.morphTargetInfluences[i]=openness;}
 for(const f of flaps){let p=f.parent;while(p&&!p.userData.part_id)p=p.parent;const outlet=['pulmonary_valve','aortic_valve'].includes(p?.userData.part_id);const open=outlet?(phase>.43&&phase<.73):!(phase>.38&&phase<.78);f.rotation.z=(open?.65:.04)*(f.userData.flap_sign||1);}
 $('phase').textContent=(running?'':'PAUSED · ')+(phase<.18||phase>=.78?'Relaxation & filling':phase<.38?'Atria contract':phase<.78?'Ventricles contract':'Relaxation');
 for(const d of dots){d.o.visible=flow&&cutaway;d.o.position.copy(d.curve.getPoint((flowTime+d.offset)%1));}
 if(model){model.updateMatrixWorld(true);let left=0,right=0;for(const p of [...parts].sort((a,b)=>['aorta','vena_cava','pulmonary_artery','pulmonary_veins','right_atrium','left_atrium','tricuspid','aortic_valve','pulmonary_valve','mitral','septum','right_ventricle','left_ventricle'].indexOf(a.id)-['aorta','vena_cava','pulmonary_artery','pulmonary_veins','right_atrium','left_atrium','tricuspid','aortic_valve','pulmonary_valve','mitral','septum','right_ventricle','left_ventricle'].indexOf(b.id))){const tag=tags.get(p.id),line=lines.get(p.id);if(!tag)continue;const internal=['septum','tricuspid','mitral','pulmonary_valve','aortic_valve'].includes(p.id);const shown=labels&&(cutaway||!internal);tag.style.display=shown?'block':'none';line.style.display=shown?'block':'none';if(!shown)continue;const v=vec(anchors[p.id]).project(camera),side=['right_atrium','right_ventricle','vena_cava','pulmonary_artery','tricuspid','pulmonary_valve'].includes(p.id);const n=side?left++:right++,w=stage.clientWidth,px=side?10:w-(w<650?115:172),py=25+n*(stage.clientHeight-80)/7;tag.style.left=px+'px';tag.style.top=py+'px';line.setAttribute('x1',(v.x+1)*w/2);line.setAttribute('y1',(1-v.y)*stage.clientHeight/2);line.setAttribute('x2',side?px+tag.offsetWidth:px);line.setAttribute('y2',py+tag.offsetHeight/2);}}
 controls.update();renderer.render(scene,camera);
}
requestAnimationFrame(animate);
