import subprocess,json,time
from pathlib import Path
C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';O=Path(__file__).parent
R=json.loads((O/'runtime.json').read_text())['data']['runtimeId'];tail=['--instance','55c37f10-22fb-496a-930a-07e79637a6cd','--runtime-id',R,'--json']
p=subprocess.Popen([C,'runtime','input','keys','W:3500',*tail],stdout=subprocess.PIPE,text=True)
time.sleep(.7)
code='local out={pos=tostring(self.transform.position)};for i=1,40 do local n,v=debug.getupvalue(Update,i);if not n then break end;if n=="speed" then out.speed=v elseif n=="play" then for j=1,10 do local nn,vv=debug.getupvalue(v,j);if nn=="lastClip" then out.clip=vv end end end end;return out'
a=[]
for i in range(3):
 q=subprocess.run([C,'runtime','lua','eval',code,'--script','horse_seat_v1.lua',*tail],capture_output=True,text=True);a.append(json.loads(q.stdout));time.sleep(.3)
print(json.dumps(a));(O/'horse-run-sampled.json').write_text(json.dumps(a));print(p.communicate()[0])
