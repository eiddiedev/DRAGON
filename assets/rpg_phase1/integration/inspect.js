const q=await scene.nodes.query({}, {limit:500,fields:['handle','name','parent','active']});
return {nodes:q,bindings:await scene.scripts.bindings(q.items.map(n=>n.handle))};
