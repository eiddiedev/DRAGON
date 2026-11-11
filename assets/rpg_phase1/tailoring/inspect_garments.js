const U=CS.UnityEngine,a=CS.DouyinActorService.GetLocalActor();const result={bones:{}};
for(const key of ['Hips','Chest','Head','LeftUpperArm'])result.bones[key]=a.GetBonePosition(U.HumanBodyBones[key]).ToString();
const all=U.Object.FindObjectsOfType(puer.$typeof(U.Renderer));result.parts=[];
for(let i=0;i<all.Length;i++){const r=all.get_Item(i);if(['ForestHood','TailoredCape1','WizardHat'].includes(r.gameObject.name)){let m=r.sharedMaterial;result.parts.push({name:r.gameObject.name,bounds:r.bounds.ToString(),shader:m.shader.name,props:['_Color','_BaseColor','_BaseColorFactor','_MainColor','_BaseTex','_BaseMap','_MainTex'].map(k=>[k,m.HasProperty(k)])});}}
return result;
