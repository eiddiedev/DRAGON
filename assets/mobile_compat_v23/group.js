const root=await scene.nodes.create({name:'手机模型对照',parent:null});await scene.nodes.reparent({nodes:['n1','n2','n35'],parent:root,preserve:'world'});return root;
