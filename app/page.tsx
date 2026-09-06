import {flushSync} from 'react-dom';
import {registerAtlasTools} from './agent-tools';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Activity,ArrowUpRight,Boxes,ChevronRight,Focus,Headphones,Info,Layers3,Pause,RotateCcw,RotateCw,Search,Sparkles,User,Volume2,VolumeX,Watch,X} from 'lucide-react';
import {GADGET_LIBRARY,type GadgetItem} from './gadgets-catalog';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {Slider} from '@/components/ui/slider';
import {Switch} from '@/components/ui/switch';
import {Sheet,SheetContent,SheetTitle,SheetDescription} from '@/components/ui/sheet';
import {Combobox,ComboboxInput,ComboboxContent,ComboboxList,ComboboxItem,ComboboxEmpty} from '@/components/ui/combobox';
import AnatomyScene from './scene';
import {resolveAssetUrl} from './asset-url';
import {DEFAULT_VISIBLE,SYSTEMS,EXPLANATIONS,explanation,type Atlas,type Concept,type SceneState,type SystemId,type View} from './anatomy';

const initial:SceneState={explode:0,visible:DEFAULT_VISIBLE,selected:[],isolate:false,view:'three-quarter',rotate:false,reset:0,sound:false};

export default function Home(){
 const detailTitle=useRef<HTMLHeadingElement>(null);
 const [modelId,setModelId]=useState<'earpods'|'human'|'chronograph'>('earpods');
 const [libraryOpen,setLibraryOpen]=useState(false);
 const [atlas,setAtlas]=useState<Atlas|null>(null),[state,setState]=useState(initial),[progress,setProgress]=useState(0),[error,setError]=useState(''),[panel,setPanel]=useState<'layers'|'search'|null>(null),[details,setDetails]=useState(false),[about,setAbout]=useState(false),[query,setQuery]=useState(''),[chosen,setChosen]=useState<Concept|null>(null);
 const currentGadget=useMemo(()=>GADGET_LIBRARY.find(g=>g.id===modelId)??GADGET_LIBRARY[0],[modelId]);

 useEffect(()=>{
  const abort=new AbortController();
  setProgress(0);setError('');setAtlas(null);setChosen(null);setDetails(false);
  const rawUrl=currentGadget.dataUrl??(modelId==='earpods'?'/models/earpods.json':modelId==='chronograph'?'/models/chronograph.json':'/models/atlas.json');
  const baseDataUrl=resolveAssetUrl(rawUrl);
  const targetUrl=baseDataUrl.includes('?')?baseDataUrl:`${baseDataUrl}?v=${Date.now()}`;
  fetch(targetUrl,{signal:abort.signal})
   .then(r=>{if(!r.ok)throw new Error('The 3D model catalogue could not be loaded.');return r.json();})
   .then(data=>{
    const a=data as Atlas;
    setAtlas(a);
    const vis=a.systems?a.systems.map(s=>s.id):DEFAULT_VISIBLE;
    setState(s=>({...initial,visible:vis}));
   })
   .catch(e=>{if(e.name!=='AbortError')setError(e.message);});
  return()=>abort.abort();
 },[modelId]);

 useEffect(()=>{
  const key=(e:KeyboardEvent)=>{
   if(e.key==='/'&&!(e.target instanceof HTMLInputElement)&&!(e.target instanceof HTMLTextAreaElement)){
    e.preventDefault();setPanel('search');setDetails(false);
   }
  };
  window.addEventListener('keydown',key);
  return()=>window.removeEventListener('keydown',key);
 },[]);

 const systemsList=useMemo(()=>atlas?.systems??SYSTEMS,[atlas]);
 const parts=useMemo(()=>new Map(atlas?.parts.map(p=>[p.id,p])),[atlas]);
 const counts=useMemo(()=>Object.fromEntries(systemsList.map(s=>[s.id,atlas?.parts.filter(p=>p.system===s.id).length??0])),[atlas,systemsList]);
 const activeSystems=systemsList.filter(s=>counts[s.id]>0);
 const selectedParts=state.selected.map(id=>parts.get(id)).filter(p=>!!p),selected=selectedParts[0],system=systemsList.find(s=>s.id===selected?.system);
 const visibleCount=atlas?.parts.filter(p=>state.isolate?state.selected.includes(p.id):state.visible.includes(p.system)||state.selected.includes(p.id)).length??0;

 const results=useMemo(()=>{
  if(!atlas)return[];
  const term=query.toLowerCase().trim();
  if(!term){
   const defaults=modelId==='earpods'
    ?['transducer','diaphragm','magnet','battery','h2','vent','stem','sensor']
    :modelId==='chronograph'
    ?['escapement','balance','rotor','column','barrel','bezel','hands','sapphire']
    :['heart','brain','liver','stomach','spleen','pancreas','urinary bladder','trachea'];
   return defaults.map(name=>atlas.concepts.find(c=>c.name.toLowerCase().includes(name))).filter((x):x is Concept=>!!x);
  }
  return atlas.concepts.filter(c=>c.name.toLowerCase().includes(term)||c.id.toLowerCase().includes(term)).sort((a,b)=>a.name.length-b.name.length).slice(0,80);
 },[atlas,query,modelId]);

 const choose=(c:Concept)=>{setChosen(c);setState(s=>({...s,selected:c.elements,isolate:false,rotate:false}));setDetails(true);setPanel(null);};
 useEffect(()=>{if(!atlas)return;return registerAtlasTools(atlas,c=>flushSync(()=>choose(c)));},[atlas]);
 const choosePart=(id:string)=>{const p=parts.get(id);if(!p)return;setChosen({id:p.conceptId,name:p.name,elements:[id]});setState(s=>({...s,selected:[id],isolate:false,rotate:false}));setDetails(true);setPanel(null);};
 const toggle=(id:SystemId)=>{setDetails(false);setState(s=>({...s,selected:[],isolate:false,visible:s.visible.includes(id)?s.visible.filter(x=>x!==id):[...s.visible,id]}));};
 const reset=()=>{
  const vis=atlas?.systems?atlas.systems.map(s=>s.id):DEFAULT_VISIBLE;
  setState(s=>({...initial,visible:vis,reset:s.reset+1}));setChosen(null);setDetails(false);setPanel(null);
 };
 const openPanel=(next:'layers'|'search')=>{setDetails(false);setPanel(p=>p===next?null:next);};

 return <main className="studio">
  {atlas&&<AnatomyScene key={modelId} atlas={atlas} state={{...state,inspectorOpen:details&&selectedParts.length>0}} onSelect={choosePart} onProgress={n=>{setProgress(n);if(n===100)setError('');}} onError={setError}/>}
  <div className="vignette"/>
  <header className="identity">
   <div className="eyebrow"><span className="status-dot"/> {currentGadget.subtitle}</div>
   <h1>{currentGadget.title}<Badge variant="outline" className="edition">{currentGadget.badge}</Badge></h1>
   <div className="identity-meta">{atlas?atlas.parts.length.toLocaleString():currentGadget.pieces.toLocaleString()} modeled pieces <span>·</span> {currentGadget.category} <span>·</span> {currentGadget.sourceLabel??'3D CAD'}</div>
   <div className="gadget-switcher-row">
    <div className="gadget-pills">
     <Button variant="ghost" className={`gadget-pill ${modelId==='earpods'?'active':''}`} onClick={()=>{if(modelId!=='earpods')setModelId('earpods');}} aria-label="Select AirPods Pro">
      <Headphones size={13}/><span>AirPods Pro</span>
     </Button>
     <Button variant="ghost" className={`gadget-pill ${modelId==='chronograph'?'active':''}`} onClick={()=>{if(modelId!=='chronograph')setModelId('chronograph');}} aria-label="Select Automatic Chronograph">
      <Watch size={13}/><span>Chronograph</span>
     </Button>
     <Button variant="ghost" className={`gadget-pill ${modelId==='human'?'active':''}`} onClick={()=>{if(modelId!=='human')setModelId('human');}} aria-label="Select Human Body Atlas">
      <User size={13}/><span>Human Body</span>
     </Button>
     <Button variant="ghost" className="gadget-pill browse-pill" onClick={()=>{setPanel(null);setDetails(false);setAbout(false);setLibraryOpen(true);}} aria-label="Browse all gadgets in library">
      <Boxes size={13}/><span>Library ({GADGET_LIBRARY.length}) ▾</span>
     </Button>
    </div>
   </div>
  </header>

  <nav className="top-actions" aria-label="Explorer panels">
   <Button variant="ghost" className={`library-nav-btn ${libraryOpen?'active':''}`} onClick={()=>{setPanel(null);setDetails(false);setAbout(false);setLibraryOpen(true);}} aria-label="Open Gadget Library">
    <Boxes size={18}/><span>Gadget Library</span><Badge variant="secondary" className="desktop-only small-badge">3 READY</Badge>
   </Button>
   <Button variant="ghost" className={panel==='search'?'active':''} onClick={()=>openPanel('search')} aria-label={modelId==='human'?'Find anatomy':'Find component'}>
    <Search size={18}/><span>{modelId==='human'?'Find a structure':'Find a component'}</span><kbd>/</kbd>
   </Button>
   <Button variant="ghost" className="icon-button" aria-label="About this model" onClick={()=>{setDetails(false);setPanel(null);setLibraryOpen(false);setAbout(true);}}>
    <Info size={18}/>
   </Button>
  </nav>

  <section className={`layers-panel glass ${panel==='layers'?'mobile-open':''}`} aria-label="Component layers">
   <div className="panel-heading"><span>Subsystems</span><Button variant="ghost" className="mobile-only icon-button" onClick={()=>setPanel(null)} aria-label="Close systems"><X size={18}/></Button><Badge variant="secondary" className="desktop-only small-number">{activeSystems.length}</Badge></div>
   <div className="layer-presets">
    <Button variant="ghost" aria-pressed={activeSystems.every(x=>state.visible.includes(x.id))} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:activeSystems.map(x=>x.id)}))}>All</Button>
    {modelId==='earpods'?(
     <>
      <Button variant="ghost" aria-pressed={state.visible.length===2&&state.visible.includes('transducer')&&state.visible.includes('magnetic_motor')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['transducer','magnetic_motor']}))}>Driver</Button>
      <Button variant="ghost" aria-pressed={state.visible.length===2&&state.visible.includes('enclosure')&&state.visible.includes('acoustics_vents')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['enclosure','acoustics_vents']}))}>Acoustics</Button>
      <Button variant="ghost" aria-pressed={state.visible.length===2&&state.visible.includes('computing_silicon')&&state.visible.includes('controls_stem')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['computing_silicon','controls_stem']}))}>Silicon & Stem</Button>
     </>
    ):modelId==='chronograph'?(
     <>
      <Button variant="ghost" aria-pressed={state.visible.length===4&&state.visible.includes('dial_face')&&state.visible.includes('dial_indices')&&state.visible.includes('hands_assembly')&&state.visible.includes('chrono_needle')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['dial_face','dial_indices','hands_assembly','chrono_needle']}))}>Dial & Hands</Button>
      <Button variant="ghost" aria-pressed={state.visible.length===3&&state.visible.includes('regulating_organ')&&state.visible.includes('gear_transmission')&&state.visible.includes('automatic_winding')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['regulating_organ','gear_transmission','automatic_winding']}))}>Escapement</Button>
      <Button variant="ghost" aria-pressed={state.visible.length===3&&state.visible.includes('case_exterior')&&state.visible.includes('tachymeter_bezel')&&state.visible.includes('sapphire_optics')} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['case_exterior','tachymeter_bezel','sapphire_optics']}))}>Case & Bezel</Button>
     </>
    ):(
     <>
      <Button variant="ghost" aria-pressed={state.visible.length===1&&state.visible[0]==='skeletal'} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['skeletal']}))}>Skeleton</Button>
      <Button variant="ghost" aria-pressed={state.visible.length===6&&['cardiac','respiratory','digestive','urinary','endocrine','reproductive'].every(id=>state.visible.includes(id as SystemId))} onClick={()=>setState(s=>({...s,selected:[],isolate:false,visible:['cardiac','respiratory','digestive','urinary','endocrine','reproductive']}))}>Organs</Button>
     </>
    )}
   </div>
   <div className="system-list">
    {activeSystems.map(s=><div className={`system-row ${state.visible.includes(s.id)?'enabled':''}`} key={s.id}>
     <Button variant="ghost" className="system-name" title={`Show only ${s.name.toLowerCase()}`} onClick={()=>setState(v=>({...v,visible:[s.id],isolate:false,selected:[]}))}>
      <span className="system-dot" style={{background:s.color}}/>{s.name}<span className="system-count">{counts[s.id]}</span>
     </Button>
     <Switch checked={state.visible.includes(s.id)} onCheckedChange={()=>toggle(s.id)} aria-label={`Show ${s.name.toLowerCase()}`} />
    </div>)}
   </div>
   <div className="panel-foot"><span>{visibleCount.toLocaleString()} {visibleCount===1?'piece':'pieces'} visible</span><Button variant="ghost" onClick={()=>setState(s=>({...s,visible:[],selected:[],isolate:false}))}>Hide all</Button></div>
  </section>

  {panel==='search'&&<section className="search-panel glass" aria-label="Find components">
   <div className="panel-heading"><span>{modelId==='earpods'?'Find a component':'Find a structure'}</span><Button variant="ghost" className="icon-button" onClick={()=>setPanel(null)} aria-label="Close search"><X size={18}/></Button></div>
   <Combobox<Concept> items={results} value={null} onValueChange={value=>{if(value)choose(value);}} inputValue={query} onInputValueChange={setQuery} itemToStringLabel={c=>c.name} filter={null} open onOpenChange={open=>{if(!open)setPanel(null);}}>
    <ComboboxInput autoFocus placeholder={modelId==='earpods'?'Diaphragm, voice coil, magnet, vent…':'Heart, femur, cranial nerve…'} aria-label="Search named components" showTrigger={false}/>
    <ComboboxContent className="anatomy-search-results">
     <ComboboxEmpty>No components match your search.</ComboboxEmpty>
     <ComboboxList>{(c:Concept)=><ComboboxItem key={c.id} value={c}><span className="search-result-name">{c.name}</span><span className="small-number">{c.elements.length} {c.elements.length===1?'piece':'pieces'}</span></ComboboxItem>}</ComboboxList>
    </ComboboxContent>
   </Combobox>
   <p className="search-note">{query?'Showing up to 80 matches. Refine your search to find specific components.':modelId==='earpods'?'Start with major transducer parts, or search any component.':'Start with a major organ, or search every named structure.'}</p>
  </section>}

  <nav className="view-controls glass" aria-label="Camera controls">
   {(['three-quarter','front','side','back'] as View[]).map((v,i)=><Button variant="ghost" key={v} className={state.view===v?'active':''} aria-pressed={state.view===v} disabled={state.explode>.8&&v!=='front'} onClick={()=>setState(s=>({...s,view:v,reset:s.reset+1,rotate:false}))} title={`${v} view`} aria-label={`${v} view`}><span>{['¾','F','S','B'][i]}</span></Button>)}
   <i/>
   <Button variant="ghost" disabled={state.explode>=.4} aria-label={state.rotate?'Pause rotation':'Rotate model'} title="Auto rotate" className={state.rotate?'active':''} onClick={()=>setState(s=>({...s,rotate:!s.rotate}))}>
    {state.rotate?<Pause size={17}/>:<RotateCw size={18}/>}
   </Button>
   <Button variant="ghost" aria-label="Reset view and layers" title="Reset" onClick={reset}><RotateCcw size={17}/></Button>
   {modelId==='chronograph'&&(
    <>
     <i/>
     <Button variant="ghost" className={state.sound?'active':''} aria-label={state.sound?'Mute mechanical ticking':'Unmute mechanical ticking (28,800 vph)'} title={state.sound?'Mute mechanical ticking':'Unmute mechanical ticking (28,800 vph)'} onClick={()=>setState(s=>({...s,sound:!s.sound}))}>
      {state.sound?<Volume2 size={17}/>:<VolumeX size={17}/>}
     </Button>
    </>
   )}
  </nav>

  <div className="scene-caption"><span className="caption-line"/><span>{state.isolate?(chosen?.name??'SELECTED COMPONENT'):state.explode>.95?'COMPONENT INVENTORY':state.explode>.05?'SEPARATED COMPONENTS':(modelId==='earpods'?'AIRPODS PRO (2ND GEN) · DECONSTRUCTED':modelId==='chronograph'?'AUTOMATIC CHRONOGRAPH · 28,800 VPH':'ADULT HUMAN · MALE')}</span><span className="caption-line"/></div>

  <div className="bottom-dock glass">
   <Button variant="ghost" className="mobile-only dock-layers" onClick={()=>openPanel('layers')} aria-label="Open subsystem layers"><Layers3 size={20}/><span>Subsystems</span></Button>
   <div className="explode-control">
    <div className="explode-label"><label id="explode-label">Explode components</label><output>{Math.round(state.explode*100)}<span>%</span></output></div>
    <Slider aria-labelledby="explode-label" min={0} max={100} step={1} value={[state.explode*100]} onValueChange={v=>setState(s=>({...s,explode:(Array.isArray(v)?v[0]:v)/100,view:(Array.isArray(v)?v[0]:v)>80?'front':s.view,rotate:false}))}/>
    <div className="slider-endpoints"><span>Assembled</span><span>Every piece</span></div>
   </div>
   <Button variant="ghost" className="dock-reset" onClick={reset} aria-label="Assemble and reset"><RotateCcw size={18}/><span>Reset</span></Button>
  </div>

  <footer className="studio-footer"><span>{state.explode>.8?'Drag to pan':'Drag to orbit'} <b>·</b> Pinch to zoom <b>·</b> Tap any part to inspect</span><Button variant="ghost" onClick={()=>{setDetails(false);setPanel(null);setAbout(true);}}>Engineering & credits <ArrowUpRight size={12}/></Button></footer>

  {progress<100&&!error&&<div className="loading glass" role="status"><Activity size={18}/><div><strong>Preparing 3D model</strong><span>{progress}% · Loading {atlas?.parts.length.toLocaleString()??'13'} components</span><div className="loading-track"><i style={{width:`${progress}%`}}/></div></div></div>}
  {error&&<div className="loading glass error" role="alert"><p>{error}</p><Button variant="ghost" onClick={()=>location.reload()}>Reload viewer</Button></div>}

  <Sheet open={details&&selectedParts.length>0} modal={false} disablePointerDismissal onOpenChange={setDetails}>
   <SheetContent initialFocus={detailTitle} className={`detail-sheet glass ${state.isolate?'is-isolated':''}`} showCloseButton={true}>
    <div className="detail-header">
     <div className="detail-accent" style={{background:system?.color}}/>
     <div className="eyebrow">{system?.name??'COMPONENT'}</div>
     <SheetTitle ref={detailTitle} tabIndex={-1} className="structure-title">{chosen?.name}</SheetTitle>
    </div>
    <div className="detail-scroll" key={`${chosen?.id}-${state.isolate}`}>
     <SheetDescription className="structure-description">{chosen&&selected?explanation(chosen.name,selected.system,atlas):''}</SheetDescription>
     {chosen&&!atlas?.explanations?.[chosen.name.toLowerCase()]&&!EXPLANATIONS[chosen.name.toLowerCase()]&&<span className="context-note">System overview · component identified from 3D assembly</span>}
     <div className="structure-meta">
      <span>Part ID<strong>{chosen?.id}</strong></span>
      <span>Included pieces<strong>{state.selected.length.toLocaleString()}</strong></span>
     </div>
     {selectedParts.length>1&&<div className="member-list">
      <h3>Included structures</h3>
      {selectedParts.slice(0,50).map(p=><Button variant="ghost" key={p.id} onClick={()=>choosePart(p.id)}><span>{p.name}</span><ChevronRight size={14}/></Button>)}
     </div>}
     <a className="source-link" href={modelId==='earpods'?'https://www.apple.com/airpods-pro/':'https://lifesciencedb.jp/bp3d/'} target="_blank" rel="noreferrer">
      {modelId==='earpods'?'View AirPods Pro 2 specifications':'View anatomical source'} <ArrowUpRight size={14}/>
     </a>
    </div>
    <div className="detail-actions">
     <Button className={`primary-action ${state.isolate?'active':''}`} onClick={()=>setState(s=>({...s,isolate:!s.isolate,explode:0}))}>
      <Focus size={18}/>{state.isolate?'Show surrounding assembly':'Isolate component'}<ChevronRight size={16}/>
     </Button>
     <Button variant="ghost" className="secondary-action" onClick={()=>{setState(s=>({...s,selected:[],isolate:false}));setDetails(false);}}>Clear selection</Button>
    </div>
   </SheetContent>
  </Sheet>

  <Sheet open={about} onOpenChange={setAbout}>
   <SheetContent className="about-sheet glass">
    <div className="eyebrow">ENGINEERING & ARCHITECTURE</div>
    <SheetTitle className="structure-title">{modelId==='earpods'?'Inside AirPods Pro (2nd Gen)':modelId==='chronograph'?'Precision Mechanical Chronograph':'A body, revealed.'}</SheetTitle>
    <SheetDescription>{modelId==='earpods'?'Computational audio, custom high-excursion transducers, and acoustic vents modeled from Apple engineering drawings.':modelId==='chronograph'?'28,800 vph Swiss high-beat escapement, 6-pillar column-wheel chronograph clutch, and 316L stainless steel case.':'Explore the adult male reference anatomy from BodyParts3D.'}</SheetDescription>
    {modelId==='earpods'?(
     <div className="about-copy">
      <p><strong>AirPods Pro (2nd Generation) · Hardware Architecture</strong><br/>13 modeled CAD components and 12 functional sub-assemblies.</p>
      <p>Modeled accurately after Apple's official Accessory Design Guidelines dimensional specifications, this deconstruction reveals the micro-engineering behind Active Noise Cancellation and Spatial Audio:</p>
      <h3>1. Custom High-Excursion Transducer</h3>
      <p>Apple's low-distortion dynamic driver features a stiff center dome for clean 20 kHz treble and a compliant roll-surround for high-amplitude low-frequency excursion down to 20 Hz.</p>
      <h3>2. Apple H2 Computational Audio Silicon</h3>
      <p>The custom H2 SiP processes incoming acoustic data 48,000 times per second, running real-time anti-noise algorithms, Adaptive Transparency, and personalized Spatial Audio head tracking.</p>
      <h3>3. Inward-Facing ANC Microphone & Adaptive EQ</h3>
      <p>An inward-facing microphone listens to sound waves inside your ear canal and dynamically calibrates the mid and low frequencies in real-time to match your unique ear geometry.</p>
      <h3>4. Acoustic Equalization Vents & Micro-Grilles</h3>
      <p>Laser-perforated acoustic micro-grilles on the outer housing equalize air pressure inside the ear canal to prevent the plugged-in pressure sensation typical of in-ear earbuds.</p>
      <h3>5. Touch & Force Sensor Stem</h3>
      <p>The shortened stem features an indented capacitive touch sensor supporting squeeze gestures for playback modes and smooth slide gestures for volume control.</p>
     </div>
    ):modelId==='chronograph'?(
     <div className="about-copy">
      <p><strong>High-Beat Automatic Column-Wheel Chronograph</strong><br/>19 modeled horological components, 10 functional subsystems, and 11,226 micro-machined triangles.</p>
      <p>Operating at 28,800 vibrations per hour (4 Hz / 8 beats per second), this mechanical deconstruction reveals the traditional micro-mechanics of high-complication Swiss horology:</p>
      <h3>1. Swiss High-Beat Escapement & Glucydur Balance</h3>
      <p>The Glucydur temperature-compensating balance wheel rapidly oscillates at 4 Hz, held under tension by an in-house Nivarox hairspring. Its synthetic ruby pallet lever rocks back and forth 8 times per second to impulse the club-tooth escape wheel.</p>
      <h3>2. Racing Scarlet Chronograph Sweeper Hand</h3>
      <p>A central racing red sweep seconds needle steps 8 times per second (480 crisp micro-steps per revolution), powered by a dedicated central chronograph wheel with instantaneous clutch engagement.</p>
      <h3>3. 6-Pillar Precision Column-Wheel Clutch</h3>
      <p>Precision column wheels represent the pinnacle of chronograph mechanisms, using micro-machined radial pillars and spring-loaded levers to command the crisp start, stop, and reset action of the pushers with velvety tactile feedback.</p>
      <h3>4. Tri-Compax Sub-Dial Dial Architecture</h3>
      <p>The sunburst obsidian dial features 3 recessed concentric registers: a continuous running small seconds counter at 9 o'clock, a 30-minute elapsed chronograph counter at 3 o'clock, and a 12-hour totalizer at 6 o'clock.</p>
      <h3>5. 316L Stainless Steel Case with Ergonomic Sculpted Lugs</h3>
      <p>The 41 mm case is machined from surgical-grade 316L stainless steel, featuring downward-sweeping curved lugs, integrated bracelet end-links, knurled screw-down winding crown, crown guards, and dual pump pushers.</p>
     </div>
    ):(
     <div className="about-copy">
      <p><strong>Male · BodyParts3D</strong><br/>2,234 individual meshes and 3,432 named concepts from an adult male reference anatomy.</p>
      <p>This reference does not contain every human structure or variation. Named concepts can contain multiple pieces; each source mesh is rendered once.</p>
      <h3>Source</h3>
      <p>BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.</p>
     </div>
    )}
   </SheetContent>
  </Sheet>

  <Sheet open={libraryOpen} onOpenChange={setLibraryOpen}>
   <SheetContent className="library-sheet glass">
    <div className="eyebrow"><Boxes size={14}/> GADGET DECONSTRUCTION STUDIO</div>
    <SheetTitle className="structure-title">Gadget & Model Library</SheetTitle>
    <SheetDescription>
     Select any device to explore its mechanical deconstruction, pull the explode slider to separate internal assemblies, and tap any part to inspect engineering details.
    </SheetDescription>
    <div className="library-catalog">
     {GADGET_LIBRARY.map(item => {
      const isCurrent = item.id === modelId;
      const isAvailable = item.status === 'ready';
      return (
       <div key={item.id} className={`gadget-card glass ${isCurrent ? 'active-gadget' : ''}`}>
        <div className="gadget-card-top">
         <div>
          <span className="gadget-card-category">{item.category}</span>
          <h3 className="gadget-card-title">{item.title}</h3>
         </div>
         <Badge variant={isCurrent ? 'default' : 'outline'} className="gadget-card-badge">
          {isCurrent ? 'ACTIVE' : item.badge}
         </Badge>
        </div>
        <p className="gadget-card-desc">{item.description}</p>
        <div className="gadget-card-foot">
         <div className="gadget-card-meta">
          <span><strong>{item.pieces.toLocaleString()}</strong> pieces</span>
          <span>·</span>
          <span><strong>{item.subsystems}</strong> subsystems</span>
         </div>
         {isAvailable ? (
          <Button
           size="sm"
           className={`load-gadget-btn ${isCurrent ? 'current' : ''}`}
           onClick={() => {
            if (!isCurrent && item.status === 'ready') {
             setModelId(item.id as 'earpods' | 'human' | 'chronograph');
            }
            setLibraryOpen(false);
           }}
          >
           {isCurrent ? 'Currently Viewing' : 'Load in Studio →'}
          </Button>
         ) : (
          <Badge variant="secondary" className="gadget-card-soon">Coming Soon</Badge>
         )}
        </div>
       </div>
      );
     })}
    </div>
   </SheetContent>
  </Sheet>
  </main>;
}
