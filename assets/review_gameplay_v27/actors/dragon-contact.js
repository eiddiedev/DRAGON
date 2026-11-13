// Read-only runtime probe: saved dragon contacts/feet versus actual loaded colliders.
// It does not Play, move, enable, teleport, create or modify any scene object.
const U = CS.UnityEngine;
const vec = v => ({x:v.x,y:v.y,z:v.z});
const root = U.GameObject.Find('dragon_v8_live');
if (!root) return {build:'v27-dragon-contact',dragonFound:false,note:'Find returns active loaded objects only'};
const rootT = root.transform;
const wanted = ['contact_front.L','contact_front.R','contact_hind.L','contact_hind.R',
 'front_foot.L','front_foot.R','hind_foot.L','hind_foot.R'];
const nodes = root.GetComponentsInChildren(puer.$typeof(U.Transform),true);
const found = {};
for (let i=0;i<nodes.Length;i++) {const t=nodes.get_Item(i);if(wanted.includes(t.name))found[t.name]=t;}
function path(t) {const a=[];let steps=0;while(t && steps++<16){a.unshift(t.name);t=t.parent;}return a.join('/');}
function isDragon(t) {return t && (t===rootT || t.IsChildOf(rootT));}
function nearestPoint(p,b) {return {x:Math.max(b.min.x,Math.min(b.max.x,p.x)),y:Math.max(b.min.y,Math.min(b.max.y,p.y)),z:Math.max(b.min.z,Math.min(b.max.z,p.z))};}
function distance(a,b) {return Math.sqrt((a.x-b.x)**2+(a.y-b.y)**2+(a.z-b.z)**2);}
function boundsInfo(b) {return {min:vec(b.min),max:vec(b.max),center:vec(b.center),size:vec(b.size)};}
const contacts=[];
for (const name of wanted) {
 const t=found[name];if(!t){contacts.push({name,found:false});continue;}
 const p=t.position;
 // Cast begins above the contact so negative gap can expose embedded feet too.
 const origin=new U.Vector3(p.x,p.y+12,p.z);
 const castLength=180;
 const hits=U.Physics.RaycastAll(origin,U.Vector3.down,castLength,-1,U.QueryTriggerInteraction.Ignore);
 const surfaces=[];let excludedOwn=0;
 for(let i=0;i<hits.Length;i++) {
  const h=hits.get_Item(i), c=h.collider;
  if(!c || c.isTrigger || !c.enabled || !c.gameObject.activeInHierarchy)continue;
  if(isDragon(c.transform)){excludedOwn++;continue;}
  surfaces.push({name:c.gameObject.name,path:path(c.transform),point:vec(h.point),normal:vec(h.normal),
   rayDistance:h.distance,verticalGap:p.y-h.point.y,supportNormal:h.normal.y>=.25,
   onDragonPeak:c.gameObject.name==='dragon_peak'||path(c.transform).split('/').includes('dragon_peak')});
 }
 surfaces.sort((a,b)=>a.rayDistance-b.rayDistance);
 const support=surfaces.find(h=>h.supportNormal)||null;
 const peakSupport=surfaces.find(h=>h.onDragonPeak && h.supportNormal)||null;
 contacts.push({name,found:true,position:vec(p),origin:vec(origin),castLength,excludedOwn,
  support,peakSupport,hits:surfaces.slice(0,12),hitCount:surfaces.length,
  interpretation:'verticalGap > 0 = foot above collider; < 0 = below top surface; only loaded colliders are measured'});
}
const peak=U.GameObject.Find('dragon_peak');
let peakInfo={found:false};
if(peak){
 const rs=peak.GetComponentsInChildren(puer.$typeof(U.Renderer),true);
 const cs=peak.GetComponentsInChildren(puer.$typeof(U.Collider),true);
 const renderers=[],colliders=[];
 for(let i=0;i<rs.Length;i++){
  const r=rs.get_Item(i),b=r.bounds,q=nearestPoint(rootT.position,b);
  renderers.push({name:r.name,path:path(r.transform),enabled:r.enabled,active:r.gameObject.activeInHierarchy,
   bounds:boundsInfo(b),closestPointToDragon:q,distanceToDragon:distance(vec(rootT.position),q)});
 }
 for(let i=0;i<cs.Length;i++){
  const c=cs.get_Item(i);
  colliders.push({name:c.name,path:path(c.transform),enabled:c.enabled,isTrigger:c.isTrigger,
   active:c.gameObject.activeInHierarchy,bounds:boundsInfo(c.bounds)});
 }
 renderers.sort((a,b)=>a.distanceToDragon-b.distanceToDragon);
 peakInfo={found:true,position:vec(peak.transform.position),scale:vec(peak.transform.lossyScale),
  nearestRenderer:renderers[0]||null,renderers,colliders};
}
return {build:'v27-dragon-contact',dragonFound:true,frame:U.Time.frameCount,time:U.Time.realtimeSinceStartup,
 dragonPosition:vec(rootT.position),dragonRotation:{x:rootT.rotation.x,y:rootT.rotation.y,z:rootT.rotation.z,w:rootT.rotation.w},
 contacts,peak:peakInfo,limits:['No colliders are synthesized or enabled','A missing peak/collider can mean not streamed in','Foot bones and contact markers are reported separately; a foot joint is not necessarily the lowest mesh point']};
