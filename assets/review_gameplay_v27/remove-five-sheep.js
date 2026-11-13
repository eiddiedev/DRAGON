const rows=await scene.nodes.query({}, {limit:2000});
const removeNames=['sheep_1','sheep_4','sheep_6','sheep_7','sheep_8'];
const ids=removeNames.map(name=>{const a=rows.items.filter(n=>n.name===name);if(a.length!==1)throw new Error('Expected one '+name);return a[0].handle;});
await scene.nodes.remove({nodes:ids});
const after=await scene.nodes.query({}, {limit:2000});
return {removed:removeNames,remaining:after.items.filter(n=>/^sheep_\d+$/.test(n.name)).map(n=>n.name)};
