const U=CS.UnityEngine;
const root=U.GameObject.Find('DragonRPGControls');
const texts=root.GetComponentsInChildren(puer.$typeof(U.UI.Text),true);const result=[];
for(let i=0;i<texts.Length;i++){const t=texts.get_Item(i);result.push({name:t.name,text:t.text,font:t.font?.name,dynamic:t.font?.dynamic,material:t.material?.name,rect:t.rectTransform.rect.ToString(),scale:t.transform.lossyScale.ToString(),fontSize:t.fontSize,verts:t.cachedTextGenerator.vertexCount});}
return result;
