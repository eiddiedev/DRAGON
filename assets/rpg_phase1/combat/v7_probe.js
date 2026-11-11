const U=CS.UnityEngine;const result={listenerVolume:U.AudioListener.volume,listenerPause:U.AudioListener.pause,audio:[],bones:[]};
for(let frame=0;frame<30;frame++){
 await awaitFrames(1);
 const sources=U.Resources.FindObjectsOfTypeAll(puer.$typeof(U.AudioSource));
 for(let i=0;i<sources.Length;i++){const s=sources.get_Item(i);if(s.name.startsWith('CombatVoice')&&s.isPlaying)result.audio.push({frame,name:s.name,volume:s.volume,mute:s.mute,playing:s.isPlaying});}
 const all=U.Resources.FindObjectsOfTypeAll(puer.$typeof(U.Transform));
 for(let i=0;i<all.Length;i++){const t=all.get_Item(i);if(t.name!=='UpperArm_R')continue;let p=t.parent,owner=null;while(p){if(p.name.startsWith('BattleShadow_')){owner=p.name;break;}p=p.parent;}if(owner)result.bones.push({frame,owner,euler:t.localEulerAngles.ToString()});}
}
return result;
