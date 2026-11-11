await scene.nodes.update(['n162'],{name:'ContractBook'});
await scene.nodes.reparent({nodes:['n162'],parent:'n155',preserve:'local'});
return {book:'n162'};
