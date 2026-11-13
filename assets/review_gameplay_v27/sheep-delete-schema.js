return {caps:await scene.context.capabilities(),describe:await scene.context.describe('nodes.remove'),nodes:await scene.nodes.query({}, {limit:2000})};
