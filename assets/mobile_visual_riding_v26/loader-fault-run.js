const results=[];
for(let i=0;i<13;i++){
 results.push(await lua.eval(null,'local s=V26LoaderTest.state;local before=s.at;local done=V26LoaderTest.step();V26LoaderTest.step();return {at=s.at,onePerFrame=s.at<=before+1,done=done}',{global:true}));
 await awaitFrames(2);
}
return {steps:results,state:await lua.eval(null,'local s=V26LoaderTest.state;local out={status=s.status,errors=s.errors,encodedReleased=s.bytes==nil,images={}};for name,t in pairs(s.tex)do out.images[name]={width=t.width,height=t.height,readable=t.isReadable}end;return out',{global:true})};
