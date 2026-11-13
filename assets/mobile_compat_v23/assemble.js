const prefix='hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/';
const out=[];
for(const [name,file,x] of [['A原版马','6od1v15qufjsxrw2.glb',116],['B同马去动画保留骨骼','uyduwywgnj13xzsn.glb',120],['C参考项目骨骼模型','hkujqg8cp6kn0edi.glb',124]]){
 const r=await scene.assets.instantiateModel({resource:prefix+file,parent:null,name});
 await scene.transforms.set({nodes:[r.root],space:'world',value:{position:{x,y:80,z:93},scale:{x:2,y:2,z:2}}});out.push({name,root:r.root});
}
return out;
