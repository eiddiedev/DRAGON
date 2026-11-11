for(const [node,name]of [['n163','TripoMage'],['n183','TripoRanger'],['n203','TripoWarrior']]){
 await scene.nodes.update([node],{name});await scene.nodes.reparent({nodes:[node],parent:'n155',preserve:'local'});
}
await scene.nodes.remove({nodes:['n1']});
return await scene.document.validate();
