const root='n155';
const specs=[{node:'n152',name:'DragonSword',angle:-36.87,grip:[-.008,.62,-.31]},
 {node:'n153',name:'DragonStaff',angle:90,grip:[-.009,.44,.01]},
 {node:'n154',name:'DragonBow',angle:0,grip:[-.028,.49,.09]}];
const result=[];
for(const s of specs){
 const wrapper=await scene.nodes.create({name:s.name,parent:root});
 await scene.nodes.update([s.node],{name:'Model'});
 await scene.nodes.reparent({nodes:[s.node],parent:wrapper,preserve:'local'});
 const rad=s.angle*Math.PI/180;
 await scene.transforms.set({nodes:[s.node],space:'local',value:{rotation:{x:Math.sin(rad/2),y:0,z:0,w:Math.cos(rad/2)}}});
 const grip=await scene.nodes.create({name:'Grip',parent:wrapper});
 await scene.transforms.set({nodes:[grip],space:'local',value:{position:{x:s.grip[0],y:Math.cos(rad)*s.grip[1]-Math.sin(rad)*s.grip[2],z:Math.sin(rad)*s.grip[1]+Math.cos(rad)*s.grip[2]}}});
 result.push({name:s.name,wrapper,grip});
}
return result;
