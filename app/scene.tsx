import {useEffect,useRef} from 'react';
import * as T from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {mergeGeometries} from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import {createExplosionLayout} from './explosion-layout';
import {decodeModelResponse} from './model-download';
import {PointerTap} from './pointer-tap';
import {resolveAssetUrl} from './asset-url';
import {SYSTEMS,type Atlas,type SceneState} from './anatomy';
interface Props {atlas:Atlas;state:SceneState;onSelect:(id:string)=>void;onProgress:(n:number)=>void;onError:(s:string)=>void}
export default function AnatomyScene({atlas,state,onSelect,onProgress,onError}:Props){
 const host=useRef<HTMLDivElement>(null),latest=useRef(state),select=useRef(onSelect);
 latest.current=state;select.current=onSelect;
 useEffect(()=>{
  const el=host.current!;let disposed=false,frame=0,dirty=true,ready=false,lastView='',lastReset=-1,lastIsolate='',layoutKey='',amount=0;
  let lastState:SceneState|null=null;
  const abort=new AbortController();
  let renderer:T.WebGLRenderer;
  try{renderer=new T.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});}catch{onError('This browser could not start the 3D viewer. Please try a browser with WebGL enabled.');return;}
  renderer.setPixelRatio(Math.min(devicePixelRatio,innerWidth<768?1.5:2));renderer.setClearColor('#f2f3f3');renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;el.appendChild(renderer.domElement);
  renderer.domElement.setAttribute('aria-label','Interactive human anatomy. Drag to orbit, pinch or scroll to zoom, and tap a structure to inspect it.');
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(34,1,.005,100),controls=new OrbitControls(camera,renderer.domElement);
  camera.position.set(1.4,1.05,3.6);controls.target.set(0,.85,0);controls.enableDamping=true;controls.dampingFactor=.085;controls.minDistance=.07;controls.maxDistance=40;controls.maxPolarAngle=Math.PI*.96;controls.addEventListener('change',()=>{dirty=true;});
  const pmrem=new T.PMREMGenerator(renderer),room=new RoomEnvironment(),env=pmrem.fromScene(room,.04);scene.environment=env.texture;room.dispose();pmrem.dispose();
  scene.add(new T.HemisphereLight(0xffffff,0xa7acb2,1.05));
  const key=new T.DirectionalLight(0xfffaf4,2.3);key.position.set(-2,4,3);scene.add(key);
  const rim=new T.DirectionalLight(0xe9f0ff,1.8);rim.position.set(2,2,-3);scene.add(rim);
  const ground=new T.Mesh(new T.CircleGeometry(30,96),new T.MeshStandardMaterial({color:0xd5d9dc,roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.y=-.019;scene.add(ground);
  const platform=new T.Mesh(new T.CylinderGeometry(.68,.7,.028,100),new T.MeshStandardMaterial({color:0xeeeeec,metalness:.12,roughness:.67}));platform.position.y=-.016;scene.add(platform);
  const ring=new T.Mesh(new T.RingGeometry(.63,.632,128),new T.MeshBasicMaterial({color:0x8c969f,transparent:true,opacity:.4,side:T.DoubleSide}));ring.rotation.x=-Math.PI/2;ring.position.y=.001;scene.add(ring);
  const innerRing=new T.Mesh(new T.RingGeometry(.55,.551,128),new T.MeshBasicMaterial({color:0xa4aeb8,transparent:true,opacity:.16,side:T.DoubleSide}));innerRing.rotation.x=-Math.PI/2;innerRing.position.y=.001;scene.add(innerRing);
  const width=T.MathUtils.ceilPowerOfTwo(atlas.parts.length),texHeight=2,data=new Float32Array(width*4*texHeight),partTexture=new T.DataTexture(data,width,texHeight,T.RGBAFormat,T.FloatType);partTexture.needsUpdate=true;
  const selectedData=new Uint8Array(width*4),selectionTexture=new T.DataTexture(selectedData,width,1);selectionTexture.needsUpdate=true;
  const modelPivot=new T.Group(),modelGroup=new T.Group();modelPivot.add(modelGroup);scene.add(modelPivot);
  const materials:T.Material[]=[],geometries:T.BufferGeometry[]=[],pickers:(T.Mesh|undefined)[]=[],centers=atlas.parts.map(p=>new T.Vector3().fromArray(p.bounds[0]).add(new T.Vector3().fromArray(p.bounds[1])).multiplyScalar(.5));
  const offsets:T.Vector3[]=[],bounds=atlas.parts.map(p=>new T.Box3(new T.Vector3().fromArray(p.bounds[0]),new T.Vector3().fromArray(p.bounds[1])));
  let packingWidth=1,packingHeight=1;
  const markerPositions=new Float32Array(atlas.parts.length*3),markerGeometry=new T.BufferGeometry();markerGeometry.setAttribute('position',new T.BufferAttribute(markerPositions,3));
  const markerMaterial=new T.PointsMaterial({color:0x64748b,size:5,sizeAttenuation:false,transparent:true,opacity:.72,depthTest:false});
  markerMaterial.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif (distance(gl_PointCoord, vec2(0.5)) > 0.5) discard;');};
  const markers=new T.Points(markerGeometry,markerMaterial);markers.frustumCulled=false;markers.renderOrder=10;markers.visible=false;modelGroup.add(markers);
  const hover=document.createElement('div');hover.className='part-hover';hover.setAttribute('role','tooltip');hover.hidden=true;el.appendChild(hover);
  type Target={index:number;x:number;y:number;left:number;right:number;top:number;bottom:number};let targets:Target[]=[];
  const projected=new T.Vector3();
  const findTarget=(x:number,y:number,radius:number)=>{
   let best=-1,score=Infinity;
   for(const t of targets){const dx=Math.max(t.left-x,0,x-t.right),dy=Math.max(t.top-y,0,y-t.bottom),distance=Math.hypot(dx,dy);if(distance>radius)continue;const candidate=distance+Math.hypot(t.x-x,t.y-y)*.025;if(candidate<score){score=candidate;best=t.index;}}
   return best;
  };
  const activeSystems=atlas.systems??SYSTEMS;
  const materialFor=(system:string)=>{
   const sysInfo=activeSystems.find(s=>s.id===system);
   const isMetallic=system==='transducer'||system==='magnetic_motor'||system==='controls_stem'||system==='case_exterior'||system==='gear_transmission'||system==='automatic_winding'||system==='regulating_organ'||system==='dial_indices'||system==='hands_assembly'||system==='skeletal';
   const isVents=system==='acoustics_vents';
   const isGlossy=system==='enclosure'||system==='dial_indication'||system==='dial_face'||system==='chrono_needle';
   const isBezel=system==='tachymeter_bezel';
   const isGlass=system==='sapphire_optics'||system==='silicone_optics';
   const m=new T.MeshStandardMaterial({
    color:sysInfo?.color??'#aebbb8',
    metalness:isGlass?.06:(isMetallic?.92:(isBezel?.35:(isVents?.15:(isGlossy?.08:.1)))),
    roughness:isGlass?.05:(isMetallic?.14:(isBezel?.18:(isVents?.82:(isGlossy?.15:.53)))),
    side:T.DoubleSide,
    transparent:system==='integumentary'||isGlass,
    opacity:system==='integumentary'?.1:(isGlass?.12:1),
    depthWrite:system!=='integumentary'&&!isGlass
   });
   m.onBeforeCompile=shader=>{
    shader.uniforms.partState={value:partTexture};shader.uniforms.selectionState={value:selectionTexture};shader.uniforms.stateWidth={value:width};
    shader.vertexShader='attribute float partIndex; uniform sampler2D partState; uniform sampler2D selectionState; uniform float stateWidth; varying float partVisible; varying float partSelected;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
vec2 stateUv = vec2((partIndex + 0.5) / stateWidth, 0.25);
vec4 state = texture2D(partState, stateUv);
vec2 animUv = vec2((partIndex + 0.5) / stateWidth, 0.75);
vec4 anim = texture2D(partState, animUv);
if (anim.w > 0.5) {
  float ca = cos(anim.z);
  float sa = sin(anim.z);
  vec2 rel = transformed.xy - anim.xy;
  transformed.xy = anim.xy + vec2(rel.x * ca - rel.y * sa, rel.x * sa + rel.y * ca);
  objectNormal.xy = vec2(objectNormal.x * ca - objectNormal.y * sa, objectNormal.x * sa + objectNormal.y * ca);
}
transformed += state.xyz;
partVisible = state.w;
partSelected = texture2D(selectionState, vec2((partIndex + 0.5) / stateWidth, 0.5)).r;`);
    shader.fragmentShader='varying float partVisible; varying float partSelected;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif (partVisible < 0.5) discard;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.42, 0.85, 0.78), partSelected * 0.75);');
   };materials.push(m);return m;
  };
  const mats=new Map(activeSystems.map(s=>[s.id,materialFor(s.id)]));
  let loaded=0;
  const loadChunk=async(ci:number)=>{
   const chunk=atlas.chunks[ci],compressed=!!chunk.gzip&&typeof DecompressionStream!=='undefined';
   const rawChunkUrl=compressed?chunk.gzip!:chunk.url;
   const targetUrl=resolveAssetUrl(rawChunkUrl);
   const url=targetUrl.includes('?')?targetUrl:`${targetUrl}?v=${Date.now()}`;
   const response=await fetch(url,{signal:abort.signal});const buffer=await decodeModelResponse(response,chunk.bytes,compressed);if(disposed)return;
   const groups=new Map<string,T.BufferGeometry[]>();
   atlas.parts.forEach((p,i)=>{
    if(p.chunk!==ci)return;
    const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(buffer,p.positions,p.vertexCount*3),3));
    g.setAttribute('normal',new T.BufferAttribute(new Int16Array(buffer,p.normals,p.vertexCount*3),3,true));g.setIndex(new T.BufferAttribute(new Uint32Array(buffer,p.indices,p.indexCount),1));
    g.boundingBox=bounds[i].clone();g.computeBoundingSphere();const pick=new T.Mesh(g);pick.visible=false;pick.matrixAutoUpdate=false;modelGroup.add(pick);pickers[i]=pick;geometries.push(g);
    g.setAttribute('partIndex',new T.BufferAttribute(new Float32Array(p.vertexCount).fill(i),1));
    const list=groups.get(p.system)??[];list.push(g);groups.set(p.system,list);
   });
   groups.forEach((gs,system)=>{const geometry=mergeGeometries(gs,false);if(!geometry)throw new Error('Could not assemble anatomy geometry.');geometries.push(geometry);const mesh=new T.Mesh(geometry,mats.get(system as never));mesh.renderOrder=system==='sapphire_optics'?10:1;mesh.frustumCulled=false;modelGroup.add(mesh);});
   lastState=null;loaded++;onProgress(Math.round(loaded/atlas.chunks.length*100));dirty=true;
  };
  (async()=>{try{let cursor=0;await Promise.all(Array.from({length:3},async()=>{while(cursor<atlas.chunks.length){const i=cursor++;await loadChunk(i);}}));if(!disposed){ready=true;dirty=true;}}catch(e){if(!disposed)onError(e instanceof Error?e.message:'Could not load the anatomy.');}})();

  const overallBox=new T.Box3();bounds.forEach(b=>overallBox.union(b));
  const modelCenter=overallBox.getCenter(new T.Vector3()),modelSize=overallBox.getSize(new T.Vector3());
  modelPivot.position.set(0,modelCenter.y,0);
  modelGroup.position.set(0,-modelCenter.y,0);
  ground.position.y=overallBox.min.y-.019;platform.position.y=overallBox.min.y-.016;ring.position.y=overallBox.min.y+.001;innerRing.position.y=overallBox.min.y+.001;

  interface AnimSpec {
   type: 'sweep_seconds' | 'sub_seconds' | 'minute' | 'hour' | 'balance' | 'pallet' | 'escape' | 'rotor';
   pivot: [number, number];
  }
  const animatedParts = new Map<number, AnimSpec>();
  atlas.parts.forEach((p, i) => {
   if (p.id === 'chrono_seconds_sweeper') {
    animatedParts.set(i, { type: 'sweep_seconds', pivot: [0.0, modelCenter.y] });
   } else if (p.id === 'chrono_sub_seconds') {
    animatedParts.set(i, { type: 'sub_seconds', pivot: [-0.076, modelCenter.y] });
   } else if (p.id === 'chrono_minute_hand') {
    animatedParts.set(i, { type: 'minute', pivot: [0.0, modelCenter.y] });
   } else if (p.id === 'chrono_hour_hand') {
    animatedParts.set(i, { type: 'hour', pivot: [0.0, modelCenter.y] });
   } else if (p.id === 'chrono_balance_assembly') {
    animatedParts.set(i, { type: 'balance', pivot: [0.0, modelCenter.y] });
   } else if (p.id === 'chrono_pallet_fork') {
    animatedParts.set(i, { type: 'pallet', pivot: [0.035, modelCenter.y + 0.035] });
   } else if (p.id === 'chrono_escapement_wheel') {
    animatedParts.set(i, { type: 'escape', pivot: [0.0, modelCenter.y] });
   } else if (p.id === 'chrono_oscillating_rotor') {
    animatedParts.set(i, { type: 'rotor', pivot: [0.0, modelCenter.y] });
   }
  });
  const hasAnimations = animatedParts.size > 0;

  let audioCtx: AudioContext | null = null;
  let ticBuffer: AudioBuffer | null = null;
  let tacBuffer: AudioBuffer | null = null;

  const initAudio = () => {
   if (audioCtx) return;
   try {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;
    audioCtx = new AudioContextClass();
    const rate = audioCtx.sampleRate;
    const len = Math.floor(rate * 0.024);
    ticBuffer = audioCtx.createBuffer(1, len, rate);
    tacBuffer = audioCtx.createBuffer(1, len, rate);
    const d1 = ticBuffer.getChannelData(0);
    const d2 = tacBuffer.getChannelData(0);

    for (let i = 0; i < len; i++) {
      const t = i / rate;
      const env = Math.exp(-t / 0.005);
      const click = (Math.random() * 2 - 1) * 0.15;
      d1[i] = env * (Math.sin(2 * Math.PI * 4400 * t) * 0.65 + Math.sin(2 * Math.PI * 7200 * t) * 0.2 + click);
      d2[i] = env * (Math.sin(2 * Math.PI * 3800 * t) * 0.65 + Math.sin(2 * Math.PI * 6400 * t) * 0.2 + click);
    }
   } catch {}
  };

  const playTick = (isTic: boolean) => {
   if (!audioCtx) initAudio();
   if (!audioCtx || !ticBuffer || !tacBuffer) return;
   if (audioCtx.state === 'suspended') {
     audioCtx.resume().catch(() => {});
   }
   if (audioCtx.state !== 'running') return;
   try {
     const src = audioCtx.createBufferSource();
     src.buffer = isTic ? ticBuffer : tacBuffer;
     const gain = audioCtx.createGain();
     gain.gain.value = 0.12;
     src.connect(gain);
     gain.connect(audioCtx.destination);
     src.start();
   } catch {}
  };

  let isDragging=false,startX=0,startY=0,rotY=0,rotX=0,targetRotY=0,targetRotX=0;

  const fit=(view:string,extent=0)=>{
   const aspect=camera.aspect,mobile=el.clientWidth<768;
   const baseDist=Math.max(1.7,Math.max(modelSize.x,modelSize.y,modelSize.z)*1.85);
   const normalDistance=mobile?Math.max(baseDist*1.2,1.8*el.clientHeight/Math.max(160,el.clientHeight-350)/(2*Math.tan(T.MathUtils.degToRad(camera.fov/2)))):baseDist;
   const reservedHeight=mobile?350:270;const availableAspect=Math.max(.35,(el.clientWidth-(mobile?40:340))/Math.max(160,el.clientHeight-reservedHeight));const atlasDistance=Math.max(packingHeight,packingWidth/availableAspect)/(2*Math.tan(T.MathUtils.degToRad(camera.fov/2)))*(el.clientHeight/Math.max(160,el.clientHeight-reservedHeight))*1.08;
   const distance=T.MathUtils.lerp(normalDistance,Math.max(.2,atlasDistance),extent);
   const direction=new T.Vector3(0,.05,1).normalize();
   controls.target.set(extent>.1&&el.clientWidth>767?-packingWidth*.12:0,modelCenter.y,0);
   camera.position.copy(controls.target).addScaledVector(direction,distance);
   controls.update();dirty=true;
  };
  const resize=()=>{layoutKey='';lastState=null;renderer.setPixelRatio(Math.min(devicePixelRatio,el.clientWidth<768||el.clientHeight<600?1.5:2));camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();renderer.setSize(el.clientWidth,el.clientHeight);fit(latest.current.view,amount);};const observer=new ResizeObserver(resize);observer.observe(el);
  const raycaster=new T.Raycaster(),pointer=new T.Vector2(),tap=new PointerTap(),hitPoint=new T.Vector3();
  const down=(e:PointerEvent)=>{
   if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume().catch(()=>{});
   hover.hidden=true;
   tap.down(e.pointerId,e.clientX,e.clientY,e.pointerType==='touch'?12:5);
   isDragging=true;startX=e.clientX;startY=e.clientY;
  };
  const move=(e:PointerEvent)=>{
   tap.move(e.pointerId,e.clientX,e.clientY);
   if(e.buttons&&amount<.8&&!latest.current.isolate){
    const dx=e.clientX-startX,dy=e.clientY-startY;
    startX=e.clientX;startY=e.clientY;
    targetRotY+=dx*0.007;
    targetRotX=Math.max(-0.4,Math.min(0.65,targetRotX+dy*0.007));
    dirty=true;
   }
   if(e.buttons||amount<.5||e.pointerType==='touch'){hover.hidden=true;return;}
   const rect=el.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top,index=findTarget(x,y,12);
   hover.hidden=index<0;renderer.domElement.style.cursor=index<0?'grab':'pointer';
   if(index>=0){
    hover.textContent=atlas.parts[index].name;
    hover.style.left=`${Math.max(8,Math.min(x+14,el.clientWidth-260))}px`;
    hover.style.top=`${Math.max(8,Math.min(y+18,el.clientHeight-55))}px`;
   }
  };
  const cancel=(e:PointerEvent)=>{isDragging=false;tap.cancel(e.pointerId);};
  const up=(e:PointerEvent)=>{
   isDragging=false;
   const validTap=tap.up(e.pointerId,e.clientX,e.clientY);if(!validTap||!ready)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);
   let nearest=Infinity,found=-1;const hasSolid=atlas.parts.some((p,i)=>p.system!=='integumentary'&&data[i*4+3]>.5);
   pickers.forEach((mesh,i)=>{
    if(!mesh||data[i*4+3]<.5||(hasSolid&&atlas.parts[i].system==='integumentary'))return;
    const hits=raycaster.intersectObject(mesh,false);
    if(hits[0]&&hits[0].distance<nearest){nearest=hits[0].distance;found=i;}
   });
   if(found<0&&amount>.45)found=findTarget(e.clientX-rect.left,e.clientY-rect.top,e.pointerType==='touch'?24:16);if(found>=0){hover.hidden=true;select.current(atlas.parts[found].id);}
  };
  renderer.domElement.addEventListener('pointerdown',down);renderer.domElement.addEventListener('pointermove',move);renderer.domElement.addEventListener('pointerup',up);renderer.domElement.addEventListener('pointercancel',cancel);
   const clock=new T.Clock();let lastExtent=-1,lastBeat=-1;
   const animate=()=>{
    if(disposed)return;frame=requestAnimationFrame(animate);const dt=Math.min(clock.getDelta(),.05),s=latest.current;
    const changed=lastState?.visible!==s.visible||lastState?.selected!==s.selected||lastState?.isolate!==s.isolate;
    const moving=Math.abs(amount-s.explode)>.0001;
    if(moving){amount=T.MathUtils.damp(amount,s.explode,8,dt);dirty=true;}
    if(changed||moving||lastExtent<0){
     const visible=new Set(s.visible),selection=new Set(s.selected);
     const visibleParts=atlas.parts.filter(p=>s.isolate?selection.has(p.id):visible.has(p.system)||selection.has(p.id));
     const nextLayoutKey=visibleParts.map(p=>p.id).join(',')+':'+camera.aspect.toFixed(3);
     if(nextLayoutKey!==layoutKey){const layout=createExplosionLayout(visibleParts,camera.aspect);packingWidth=layout.width;packingHeight=layout.height;atlas.parts.forEach((p,i)=>{const cell=layout.cells.get(p.id);offsets[i]=cell?new T.Vector3(cell.x,cell.y+modelCenter.y,0):centers[i].clone();});layoutKey=nextLayoutKey;if(amount>.05&&!s.isolate)fit(s.view,Math.max(0,(amount-.3)/.7));}

     atlas.parts.forEach((p,i)=>{
      const c=centers[i],destination=offsets[i];let dx=0,dy=0,dz=0;
      if(p.explodeOffset){
       const [ex,ey,ez]=p.explodeOffset;
       if(amount<=.45){const t=amount/.45;dx=ex*t;dy=ey*t;dz=ez*t;}
       else{const t=(amount-.45)/.55;dx=T.MathUtils.lerp(ex,destination.x-c.x,t);dy=T.MathUtils.lerp(ey,destination.y-c.y,t);dz=T.MathUtils.lerp(ez,-c.z,t);}
      }else{
       const group=activeSystems.findIndex(sys=>sys.id===p.system);
       const angle=(group>=0?group:0)/Math.max(1,activeSystems.length)*Math.PI*2;
       if(amount<=.45){const t=amount/.45;dx=Math.sin(angle)*t*.48;dy=(c.y-modelCenter.y)*t*.28;dz=Math.cos(angle)*t*.48;}
       else{const t=(amount-.45)/.55;dx=T.MathUtils.lerp(Math.sin(angle)*.48,destination.x-c.x,t);dy=T.MathUtils.lerp((c.y-modelCenter.y)*.28,destination.y-c.y,t);dz=T.MathUtils.lerp(Math.cos(angle)*.48,-c.z,t);}
      }
      const selected=selection.has(p.id);data.set([dx,dy,dz,(s.isolate?selected:visible.has(p.system)||selected)?1:0],i*4);selectedData[i*4]=selected?255:0;
      markerPositions.set(data[i*4+3]>.5?[c.x+dx,c.y+dy,c.z+dz]:[10000,10000,10000],i*3);const mesh=pickers[i];if(mesh){mesh.position.set(dx,dy,dz);mesh.updateMatrix();mesh.updateMatrixWorld(true);}
     });partTexture.needsUpdate=true;selectionTexture.needsUpdate=true;markerGeometry.attributes.position.needsUpdate=true;lastState=s;lastExtent=amount;dirty=true;
    }

    if(hasAnimations){
     const now=new Date();
     const ms=now.getMilliseconds();
     const sec=now.getSeconds()+ms/1000;
     const min=now.getMinutes()+sec/60;
     const hr=(now.getHours()%12)+min/60;
     const elapsed=clock.getElapsedTime();

     const currentBeat=Math.floor(sec*8);
     if(currentBeat!==lastBeat){
      lastBeat=currentBeat;
      if(s.sound){
       playTick(currentBeat%2===0);
      }
     }

     const sweepBeat=Math.floor(sec*8)/8;
     const sweepAngle=-(sweepBeat/60)*Math.PI*2;
     const subSecondsAngle=-(sec/60)*Math.PI*2;
     const minuteAngle=-(min/60)*Math.PI*2;
     const hourAngle=-(hr/12)*Math.PI*2;

     const balanceAngle=Math.sin(elapsed*4*Math.PI*2)*2.8;
     const palletAngle=Math.tanh(Math.sin(elapsed*4*Math.PI*2)*6)*0.12;
     const escapeAngle=-(currentBeat*(Math.PI/15));
     const rotorAngle=Math.sin(elapsed*1.8)*0.7+Math.sin(elapsed*0.8)*0.3;

     animatedParts.forEach((anim,i)=>{
      let ang=0;
      switch(anim.type){
       case 'sweep_seconds':ang=sweepAngle;break;
       case 'sub_seconds':ang=subSecondsAngle;break;
       case 'minute':ang=minuteAngle;break;
       case 'hour':ang=hourAngle;break;
       case 'balance':ang=balanceAngle;break;
       case 'pallet':ang=palletAngle;break;
       case 'escape':ang=escapeAngle;break;
       case 'rotor':ang=rotorAngle;break;
      }
      const row1Offset=(width*4)+(i*4);
      const px=anim.pivot[0];
      const py=anim.pivot[1];
      data[row1Offset]=px;
      data[row1Offset+1]=py;
      data[row1Offset+2]=ang;
      data[row1Offset+3]=1.0;

      const mesh=pickers[i];
      if(mesh){
       const dx=data[i*4];
       const dy=data[i*4+1];
       const dz=data[i*4+2];
       const ca=Math.cos(ang);
       const sa=Math.sin(ang);
       mesh.rotation.z=ang;
       mesh.position.set(
        px-(px*ca-py*sa)+dx,
        py-(px*sa+py*ca)+dy,
        dz
       );
       mesh.updateMatrix();
       mesh.updateMatrixWorld(true);
      }
     });
     partTexture.needsUpdate=true;
     dirty=true;
    }
   if(s.view!==lastView||s.reset!==lastReset){
    if(s.view==='front'){targetRotY=0;targetRotX=0;}
    else if(s.view==='side'){targetRotY=Math.PI/2;targetRotX=0;}
    else if(s.view==='back'){targetRotY=Math.PI;targetRotX=0;}
    else if(s.view==='three-quarter'){targetRotY=Math.PI/4;targetRotX=0.15;}
    fit(s.view,amount);lastView=s.view;lastReset=s.reset;dirty=true;
   }
   if(moving&&!s.isolate)fit(amount>.5?'front':s.view,Math.max(0,(amount-.3)/.7));
   const isolateKey=s.isolate?s.selected.join(',')+':'+s.reset+':'+s.inspectorOpen+':'+camera.aspect:'';
   if(isolateKey!==lastIsolate||(s.isolate&&moving)){
    if(s.isolate){const box=new T.Box3();atlas.parts.forEach((p,i)=>{if(s.selected.includes(p.id))box.union(bounds[i].clone().translate(new T.Vector3(data[i*4],data[i*4+1],data[i*4+2])));});
     if(!box.isEmpty()){const center=box.getCenter(new T.Vector3()),size=box.getSize(new T.Vector3());const w=el.clientWidth,h=el.clientHeight,mobile=w<768,landscape=w>h&&h<=600;let left=20,right=w-20,top=mobile?175:110,bottom=h-170;if(s.inspectorOpen){if(landscape){right=w-335;top=100;bottom=h-125;}else if(mobile){const sheet=document.querySelector('.detail-sheet')?.getBoundingClientRect(),header=document.querySelector('.identity')?.getBoundingClientRect();top=(header?.bottom??94)+16;bottom=(sheet?.top??h*.58-139)-16;}else{right=w-370;left=w>1100?285:25;}}const availableWidth=Math.max(150,right-left),availableHeight=Math.max(40,bottom-top);camera.setViewOffset(w,h,w/2-(left+right)/2,h/2-(top+bottom)/2,w,h);const distance=Math.max(.07,Math.max(size.y*h/availableHeight,size.x*w/availableWidth/camera.aspect,size.z)/(2*Math.tan(T.MathUtils.degToRad(camera.fov/2)))*1.35);controls.maxDistance=Math.max(40,distance*2);controls.target.copy(center);camera.position.copy(center).add(new T.Vector3(.2,.1,1).normalize().multiplyScalar(distance));controls.update();dirty=true;}
    }else if(lastIsolate){camera.clearViewOffset();fit(s.view,amount);}
    lastIsolate=isolateKey;
   }

   // Auto-rotate spins the object on the stationary turntable
   if(s.rotate&&!isDragging&&amount<.4&&!s.isolate){
    targetRotY+=dt*0.6;
    dirty=true;
   }
   // When exploding into 2D packing, smoothly align flat
   if(amount>.45){
    targetRotY=T.MathUtils.damp(targetRotY,0,8,dt);
    targetRotX=T.MathUtils.damp(targetRotX,0,8,dt);
   }
   if(Math.abs(rotY-targetRotY)>0.0001||Math.abs(rotX-targetRotX)>0.0001){
    rotY=T.MathUtils.damp(rotY,targetRotY,12,dt);
    rotX=T.MathUtils.damp(rotX,targetRotX,12,dt);
    dirty=true;
   }
   modelPivot.rotation.y=rotY;
   modelPivot.rotation.x=rotX;

   controls.enableRotate=s.isolate;
   controls.mouseButtons.LEFT=s.isolate?T.MOUSE.ROTATE:(amount<.8?T.MOUSE.ROTATE:T.MOUSE.PAN);
   controls.touches.ONE=s.isolate?T.TOUCH.ROTATE:(amount<.8?T.TOUCH.ROTATE:T.TOUCH.PAN);
   ground.visible=platform.visible=ring.visible=innerRing.visible=amount<.5&&!s.isolate;
   markers.visible=amount>.75;
   controls.update();

   if(dirty){
    renderer.render(scene,camera);
    targets=[];
    if(amount>.45){
     const hasSolid=atlas.parts.some((p,i)=>p.system!=='integumentary'&&data[i*4+3]>.5);
     atlas.parts.forEach((p,i)=>{
      if(data[i*4+3]<.5||(hasSolid&&p.system==='integumentary'))return;
      let left=Infinity,right=-Infinity,top=Infinity,bottom=-Infinity;
      for(let corner=0;corner<8;corner++){
       projected.set(p.bounds[(corner&1)?1:0][0]+data[i*4],p.bounds[(corner&2)?1:0][1]+data[i*4+1],p.bounds[(corner&4)?1:0][2]+data[i*4+2]).applyMatrix4(modelGroup.matrixWorld).project(camera);
       const x=(projected.x+1)*el.clientWidth/2,y=(1-projected.y)*el.clientHeight/2;
       left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
      }
      projected.copy(centers[i]).add(new T.Vector3(data[i*4],data[i*4+1],data[i*4+2])).applyMatrix4(modelGroup.matrixWorld).project(camera);
      if(projected.z< -1||projected.z>1)return;
      targets.push({index:i,x:(projected.x+1)*el.clientWidth/2,y:(1-projected.y)*el.clientHeight/2,left,right,top,bottom});
     });
    }
    dirty=false;
   }

  };animate();
  const contextLost=(e:Event)=>{e.preventDefault();onError('The 3D session was paused by your device. Reload to continue.');};renderer.domElement.addEventListener('webglcontextlost',contextLost);
  return()=>{disposed=true;abort.abort();cancelAnimationFrame(frame);observer.disconnect();controls.dispose();if(audioCtx){audioCtx.close().catch(()=>{});audioCtx=null;}geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());scene.traverse(o=>{if(o instanceof T.Mesh&&!geometries.includes(o.geometry)){o.geometry.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>m.dispose());}});env.dispose();partTexture.dispose();selectionTexture.dispose();markerGeometry.dispose();markerMaterial.dispose();hover.remove();renderer.dispose();renderer.domElement.remove();};
 },[atlas]);
 return <div className="scene" ref={host}/>;
}
