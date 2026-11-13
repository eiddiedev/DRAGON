// CANDIDATE ONLY. The installer must fill this map with handles returned by a
// fresh scene.nodes.query/get in the intended authoring WPrefab. Audit numeric
// ids in component-proposals.json are evidence, never SDK handles.
const HANDLE_BY_NAME = {"dragon_v8_live": "n13", "sheep_0": "n105", "sheep_1": "n130", "sheep_2": "n155", "sheep_3": "n180", "sheep_4": "n205", "sheep_5": "n230", "sheep_6": "n255", "sheep_7": "n280", "sheep_8": "n305"};
const names = ['dragon_v8_live', ...Array.from({length:9}, (_,i)=>`sheep_${i}`)];
for (const name of names) if (!HANDLE_BY_NAME[name]) throw new Error(`Missing fresh target handle: ${name}`);
const dragon = HANDLE_BY_NAME.dragon_v8_live;
const current = await scene.components.get({nodes:[dragon],type:'ugcAnimatorData'});
const anim = current.items.find(v=>v.node===dragon)?.values;
if (!anim?.animationSet?.controllers?.length) throw new Error('Expected existing dragon UGC animation config');
const nextSet = JSON.parse(JSON.stringify(anim.animationSet));
const idleAsset = anim.animationAssets?.find(a=>a.clips?.some(c=>c.animationName==='idle'));
if (!idleAsset) throw new Error('Verified lower-case idle clip is absent; do not guess a default');
nextSet.defaultClip='idle';nextSet.defaultAssetId=idleAsset.assetId;
let changedGraph=0;
for (const c of nextSet.controllers) {
 const graph=JSON.parse(c.json);
 const nodes=Object.values(graph.graph?.nodes||{});
 const idle=nodes.find(n=>n.name==='idle' && n.motion?.clipName==='idle');
 if (!idle) continue;
 const machine=graph.graph?.stateMachines?.[idle.stateMachine];
 if (!machine) throw new Error('Idle state machine missing');
 machine.defaultNode=idle.id;c.json=JSON.stringify(graph);changedGraph++;
}
if (changedGraph===0) throw new Error('No dragon controller idle state found');
// Query every sheep first so failed selection cannot leave a partially changed batch.
const sheep=[];
for (const name of names.slice(1)) {
 const h=HANDLE_BY_NAME[name];const q=await scene.components.get({nodes:[h],type:'physicsColliderData'});
 const p=q.items.find(v=>v.node===h)?.values;
 if (!p || !p.enableRigidBody) throw new Error(`Expected sheep rigid body: ${name}`);
 sheep.push(h);
}
await scene.components.set({nodes:[dragon],type:'ugcAnimatorData',values:{animationSet:nextSet}});
await scene.components.set({nodes:sheep,type:'physicsColliderData',values:{isKinematic:true,useGravity:false}});
return {dragon:await scene.components.get({nodes:[dragon],type:'ugcAnimatorData'}),sheep:await scene.components.get({nodes:sheep,type:'physicsColliderData'})};
