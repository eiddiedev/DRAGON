const arm=await scene.nodes.create({name:'Armature',parent:'n2'});await scene.nodes.reparent({nodes:['n3','n4'],parent:arm,preserve:'world'});return arm;
