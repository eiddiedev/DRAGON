const U=CS.UnityEngine,a=CS.DouyinActorService.GetLocalActor();
const an=a.gameObject.GetComponentInChildren(puer.$typeof(U.Animator));
const rs=a.gameObject.GetComponentsInChildren(puer.$typeof(U.SkinnedMeshRenderer));
const vec=v=>({x:v.x,y:v.y,z:v.z});const quat=q=>({x:q.x,y:q.y,z:q.z,w:q.w});
const names=['Hips','Spine','Chest','UpperChest','Neck','Head','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm','LeftHand','RightHand','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg','LeftFoot','RightFoot'];
const bones={};for(const name of names){let b=an.GetBoneTransform(U.HumanBodyBones[name]);if(b)bones[name]={name:b.name,instanceId:b.GetInstanceID(),position:vec(a.gameObject.transform.InverseTransformPoint(b.position))};}
const skins=[];
for(let i=0;i<rs.Length;i++){let r=rs.get_Item(i),m=r.sharedMesh;if(!m)continue;let bs=r.bones,ps=m.bindposes,rest=[];
for(let j=0;j<bs.Length;j++){let b=bs.get_Item(j),p=ps.get_Item(j).inverse;let world=r.transform.TransformPoint(p.MultiplyPoint3x4(U.Vector3.zero));let rot=U.Quaternion.op_Multiply(U.Quaternion.Inverse(a.gameObject.transform.rotation),U.Quaternion.op_Multiply(r.transform.rotation,p.rotation));rest.push({name:b.name,instanceId:b.GetInstanceID(),position:vec(a.gameObject.transform.InverseTransformPoint(world)),rotation:quat(rot)});}
skins.push({name:r.name,bounds:r.bounds.ToString(),vertexCount:m.vertexCount,rest});}
return {position:vec(a.position),bones,skins};
