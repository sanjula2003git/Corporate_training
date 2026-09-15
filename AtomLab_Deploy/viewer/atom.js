import {guides} from './guides.js';
import * as THREE from './three.mjs';
import {OrbitControls} from './controls.mjs';
const $=id=>document.getElementById(id),stage=$('stage');
const send=(type,data={})=>parent.postMessage({isStreamlitMessage:true,type,...data},'*');
const descriptions={
 proton:['Proton','Positive charge (+1), about 1 u, inside the nucleus. The number of protons identifies the element.'],
 neutron:['Neutron','Zero electric charge, about 1 u, inside the nucleus. Changing neutrons changes the isotope.'],
 electron:['Electron','Negative charge (−1), much lighter than a proton, outside the nucleus. Changing electrons changes the charge.'],
 nucleus:['Nucleus','The central region containing protons and usually neutrons. Almost all atomic mass is here.'],
 shell:['Electron shell','A simplified representation of an electron energy level. The ring is not a physical track.']};
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});}
catch{$('error').textContent='3D graphics are unavailable. Enable browser hardware acceleration or try another browser. You can still use the particle explanations.';}
let activeGuide='',stepIndex=0;
let current=null,selected='nucleus',spread=false,shellsVisible=true,moving=false,meshes=[],electronMeshes=[],last=performance.now();
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,1,.03,100);
const root=new THREE.Group(),shellGroup=new THREE.Group();scene.add(root,shellGroup);
scene.add(new THREE.HemisphereLight(0xd9f4ff,0x172032,2));
for(const [position,power] of [[[3,5,6],3],[[-4,0,2],2],[[0,2,-4],2]]){const light=new THREE.DirectionalLight(0xffffff,power);light.position.set(...position);scene.add(light);}
const materials={proton:new THREE.MeshStandardMaterial({color:0xf57568,roughness:.31,metalness:.12}),neutron:new THREE.MeshStandardMaterial({color:0xe5b85c,roughness:.38,metalness:.15}),electron:new THREE.MeshStandardMaterial({color:0x5bc9ff,emissive:0x13587d,emissiveIntensity:.55,roughness:.24})};
const nucleonGeometry=new THREE.SphereGeometry(.23,28,20),electronGeometry=new THREE.SphereGeometry(.115,20,16);
const ringMaterial=new THREE.LineBasicMaterial({color:0x507386,transparent:true,opacity:.65});
let controls;
if(renderer){renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;stage.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','Interactive atom: drag to rotate, scroll to zoom, click particles to select');controls=new OrbitControls(camera,renderer.domElement);controls.autoRotate=false;controls.enableDamping=false;controls.zoomSpeed=2.7;controls.zoomToCursor=true;controls.minDistance=.65;controls.maxDistance=22;controls.maxPolarAngle=Math.PI;}
function resize(){const w=stage.clientWidth,h=stage.clientHeight;if(renderer){renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}if(!document.fullscreenElement)send('streamlit:setFrameHeight',{height:document.body.scrollHeight+4});}
new ResizeObserver(resize).observe(stage);
function reset(){camera.position.set(.9,1.5,10.8);if(controls){controls.target.set(0,0,0);controls.update();}}
reset();
function select(id){if(!descriptions[id])return;selected=id;$('partTitle').textContent=descriptions[id][0];$('partText').textContent=descriptions[id][1];$('ask').textContent='💬 Ask about '+descriptions[id][0].toLowerCase();for(const b of document.querySelectorAll('[data-part]'))b.setAttribute('aria-pressed',String(b.dataset.part===id));for(const m of meshes)m.scale.setScalar(m.userData.part===id?1.12:1);}
document.querySelectorAll('[data-part]').forEach(b=>b.onclick=()=>select(b.dataset.part));
function rebuild(d){current=d;for(const o of [...root.children])root.remove(o);for(const o of [...shellGroup.children]){shellGroup.remove(o);o.geometry.dispose();}meshes=[];electronMeshes=[];
 const count=d.p+d.n,points=[];
 for(let x=-4;x<=4;x++)for(let y=-4;y<=4;y++)for(let z=-4;z<=4;z++)if((x+y+z)%2===0)points.push(new THREE.Vector3(x,y,z).multiplyScalar(.315));
 points.sort((a,b)=>a.lengthSq()-b.lengthSq());const chosen=points.slice(0,count),centre=new THREE.Vector3();chosen.forEach(p=>centre.add(p));centre.divideScalar(count);
 let assignedP=0;
 chosen.forEach((p,i)=>{const proton=Math.round((i+1)*d.p/count)>assignedP;if(proton)assignedP++;const kind=proton?'proton':'neutron',m=new THREE.Mesh(nucleonGeometry,materials[kind]);m.userData={part:kind,home:p.clone().sub(centre)};m.position.copy(m.userData.home).multiplyScalar(spread?1.8:1);root.add(m);meshes.push(m);});
 d.shells.forEach((population,k)=>{const radius=1.65+k*.58;const tilt=.32+k*.5;const q=new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt,k*.55,.08));const pts=Array.from({length:129},(_,i)=>new THREE.Vector3(Math.cos(i/128*Math.PI*2)*radius,Math.sin(i/128*Math.PI*2)*radius,0).applyQuaternion(q));const ring=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),ringMaterial);shellGroup.add(ring);
  for(let i=0;i<population;i++){const m=new THREE.Mesh(electronGeometry,materials.electron);m.userData={part:'electron',radius,angle:i/population*Math.PI*2+.25*k,q,shell:k};root.add(m);meshes.push(m);electronMeshes.push(m);}
 });
 placeElectrons(0);shellGroup.visible=shellsVisible;buildLabels();
 const charge=d.charge===0?'':(Math.abs(d.charge)===1?'':Math.abs(d.charge))+(d.charge>0?'+':'−');
 $('symbol').innerHTML='<sup>'+d.mass+'</sup><sub>'+d.p+'</sub> '+d.symbol+'<sup>'+charge+'</sup>';
 $('element').textContent=d.name+'-'+d.mass;
 $('counts').textContent=`${d.p} protons · ${d.n} neutrons · ${d.e} electrons`;
 const detail=document.createElement('div');detail.textContent=d.state+' · Charge '+(d.charge>0?'+':'')+d.charge;$('counts').append(detail);
 const levels=document.createElement('div');levels.textContent='Shell population: '+(d.shells.join(', ')||'no electrons');$('counts').append(levels);
 $('modelStatus').textContent='Count model only: this combination is not a prediction of stability or whether an ion exists.';select(selected);updateGuide();resize();
}
function placeElectrons(dt){for(const m of electronMeshes){const d=m.userData;if(moving)d.angle+=dt*.7/(d.shell+1);m.position.set(Math.cos(d.angle)*d.radius,Math.sin(d.angle)*d.radius,0).applyQuaternion(d.q);}}
function toggleSpread(){spread=!spread;for(const m of meshes)if(m.userData.home)m.position.copy(m.userData.home).multiplyScalar(spread?1.8:1);$('spread').textContent=spread?'Gather nucleus':'Spread nucleus';$('viewHint').textContent=spread?'Nucleus spread for counting · this is not nuclear fission':'Click a particle to learn about it';}
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
function hit(e){if(!renderer)return null;const r=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(mouse,camera);return ray.intersectObjects(meshes,false)[0]?.object;}
if(renderer){let down=null;
 renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
 renderer.domElement.addEventListener('click',e=>{if(down&&Math.hypot(e.clientX-down[0],e.clientY-down[1])<6){const m=hit(e);if(m)select(m.userData.part);}});
 renderer.domElement.addEventListener('dblclick',e=>{const m=hit(e);if(m&&m.userData.part!=='electron'){e.preventDefault();toggleSpread();}});
 renderer.domElement.addEventListener('pointermove',e=>{const m=hit(e);$('tooltip').hidden=!m;if(m){const r=stage.getBoundingClientRect();$('tooltip').textContent=descriptions[m.userData.part].join(' · ');$('tooltip').style.left=Math.max(0,Math.min(e.clientX-r.left+14,r.width-220))+'px';$('tooltip').style.top=Math.max(0,Math.min(e.clientY-r.top+14,r.height-100))+'px';}renderer.domElement.style.cursor=m?'pointer':'grab';});
 renderer.domElement.addEventListener('pointerleave',()=>{$('tooltip').hidden=true;});
}
$('spread').onclick=toggleSpread;
$('shells').onclick=()=>{shellsVisible=!shellsVisible;shellGroup.visible=shellsVisible;$('shells').textContent='Shells: '+(shellsVisible?'on':'off');$('shells').setAttribute('aria-pressed',String(shellsVisible));};
$('motion').onclick=()=>{moving=!moving;$('motion').textContent='Electron motion: '+(moving?'on':'off');$('motion').setAttribute('aria-pressed',String(moving));};
function zoom(factor){if(!controls)return;const offset=camera.position.clone().sub(controls.target);offset.setLength(THREE.MathUtils.clamp(offset.length()*factor,.65,22));camera.position.copy(controls.target).add(offset);controls.update();}
$('plus').onclick=()=>zoom(.75);$('minus').onclick=()=>zoom(1.3);$('reset').onclick=reset;
$('full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{$('error').textContent='This browser blocked fullscreen. You can still rotate and zoom here.';}};
document.addEventListener('fullscreenchange',()=>{$('full').textContent=document.fullscreenElement?'Exit full screen':'Full screen';resize();});
$('ask').onclick=()=>emitStudy(true,selected);
window.addEventListener('message',e=>{if(e.source!==parent||e.data.type!=='streamlit:render')return;const d=e.data.args.atom;if(d&&JSON.stringify(d)!==JSON.stringify(current))rebuild(d);});
let labelItems=[];
function buildLabels(){
 $('modelLabels').replaceChildren();$('labelLines').replaceChildren();labelItems=[];
 const add=(title,part,position,side,index,shell=-1)=>{
  const b=document.createElement('button');b.className='modelLabel';b.textContent=title;
  b.onclick=()=>{select(part);if(shell>=0){$('partTitle').textContent='KLMN'[shell]+' shell';$('partText').textContent=`Shell ${shell+1} contains ${current.shells[shell]} electrons in this model. `+(shell===current.shells.length-1?'This is the outermost occupied shell; its electrons are valence electrons.':'It is an inner shell.');}};
  const line=document.createElementNS('http://www.w3.org/2000/svg','line');$('labelLines').append(line);$('modelLabels').append(b);labelItems.push({b,line,position,side,index,shell});
 };
 for(const [i,part] of ['proton','neutron','electron'].entries()){
  const sample=meshes.filter(m=>m.userData.part===part).sort((a,b)=>b.position.z-a.position.z)[0];
  if(sample)add(descriptions[part][0],part,()=>sample.position.clone(),'left',i);
 }
 add('Nucleus','nucleus',()=>new THREE.Vector3(),'left',3);
 current.shells.forEach((count,k)=>{const ring=shellGroup.children[k],a=ring.geometry.attributes.position;add('KLMN'[k]+' shell · '+count+' e−'+(k===current.shells.length-1?' · outer':''),'shell',()=>new THREE.Vector3().fromBufferAttribute(a,12),'right',k,k);});
}
function updateLabels(){
 for(const item of labelItems){
  const v=item.position().project(camera),w=stage.clientWidth,h=stage.clientHeight;
  const visible=v.z>=-1&&v.z<=1&&(item.shell<0||shellsVisible);
  item.b.hidden=!visible;item.line.style.display=visible?'':'none';if(!visible)continue;
  const x=item.side==='left'?8:w-item.b.offsetWidth-8;
  const y=20+item.index*Math.min(58,(h-60)/4);item.b.style.left=x+'px';item.b.style.top=y+'px';
  item.line.setAttribute('x1',(v.x*.5+.5)*w);item.line.setAttribute('y1',(-v.y*.5+.5)*h);
  item.line.setAttribute('x2',item.side==='left'?x+item.b.offsetWidth:x);item.line.setAttribute('y2',y+item.b.offsetHeight/2);
 }
}
function atomData([p,n,e]){
 const elements=[['H','Hydrogen'],['He','Helium'],['Li','Lithium'],['Be','Beryllium'],['B','Boron'],['C','Carbon'],['N','Nitrogen'],['O','Oxygen'],['F','Fluorine'],['Ne','Neon'],['Na','Sodium'],['Mg','Magnesium'],['Al','Aluminium'],['Si','Silicon'],['P','Phosphorus'],['S','Sulfur'],['Cl','Chlorine'],['Ar','Argon'],['K','Potassium'],['Ca','Calcium']];
 const [symbol,name]=elements[p-1];let remaining=e;const shells=[];for(const cap of [2,8,8,2]){if(!remaining)break;const count=Math.min(cap,remaining);shells.push(count);remaining-=count;}
 return {p,n,e,symbol,name,mass:p+n,charge:p-e,shells,state:p===e?'Neutral atom':p>e?'Positive ion (cation)':'Negative ion (anion)'};
}
async function emitStudy(ask=false,part=''){
 if(ask&&document.fullscreenElement)await document.exitFullscreen();
 send('streamlit:setComponentValue',{value:{event_id:Date.now()+'-'+Math.random(),ask,part,topic:activeGuide,counts:current?{p:current.p,n:current.n,e:current.e}:null},dataType:'json'});
}
function updateGuide(){
 $('guideBody').hidden=!activeGuide;if(!activeGuide)return;
 const g=guides[activeGuide],step=g.steps[stepIndex];
 $('stepName').textContent=(stepIndex+1)+' / '+g.steps.length+' · '+step.label;
 const matches=current&&step.counts.every((v,i)=>v===current[['p','n','e'][i]]);
 $('guideText').textContent=matches?step.explanation:'You changed the atom counts. Reload this example to follow the lesson: '+step.label+'. Your current model remains available for free exploration.';
 $('guideQuestion').textContent='Think about it: '+g.question;
 $('prevStep').disabled=stepIndex===0;$('nextStep').disabled=stepIndex===g.steps.length-1;
 $('askConcept').textContent='💬 Ask about '+g.title.toLowerCase();
}
function showStep(){if(!activeGuide)return;const step=guides[activeGuide].steps[stepIndex];shellsVisible=true;shellGroup.visible=true;$('shells').textContent='Shells: on';$('shells').setAttribute('aria-pressed','true');rebuild(atomData(step.counts));select(step.focus);updateGuide();emitStudy();resize();}
for(const [id,g] of Object.entries(guides)){const o=document.createElement('option');o.value=id;o.textContent=g.title;$('concept').append(o);}
$('concept').onchange=()=>{activeGuide=$('concept').value;stepIndex=0;if(activeGuide)showStep();else{updateGuide();resize();}};
$('prevStep').onclick=()=>{if(stepIndex>0){stepIndex--;showStep();}};
$('nextStep').onclick=()=>{if(activeGuide&&stepIndex<guides[activeGuide].steps.length-1){stepIndex++;showStep();}};
$('showExample').onclick=showStep;$('askConcept').onclick=()=>emitStudy(true);

send('streamlit:componentReady',{apiVersion:1});select('nucleus');resize();
if(new URLSearchParams(location.search).has('preview'))rebuild({p:6,n:6,e:6,mass:12,charge:0,symbol:'C',name:'Carbon',shells:[2,4],state:'Neutral atom'});
function draw(now){requestAnimationFrame(draw);const dt=Math.min((now-last)/1000,.05);last=now;placeElectrons(dt);updateLabels();if(renderer)renderer.render(scene,camera);}requestAnimationFrame(draw);
