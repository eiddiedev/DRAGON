"""Temporary inspection camera; never saved to scene or source."""
import sys
from castle_sample_runtime_cli import call,O
mode,label=sys.argv[1:]
shots={'wide':((136,96,110),(123,94,168),55),'entrance':((127,75.5,161),(127,77,168),70),'facade':((127,87,151),(127,86,168),80),'clock':((113,96,147),(117.5,94,168),58)}
if mode=='restore':
 call(['runtime','js','eval',"const U=CS.UnityEngine;const go=U.GameObject.Find('__castle_sample_inspection_camera');if(go)U.Object.Destroy(go);await awaitFrames(2);return !U.GameObject.Find('__castle_sample_inspection_camera');"],label+'.json')
else:
 p,t,f=shots[mode]
 code=f"const U=CS.UnityEngine;let go=U.GameObject.Find('__castle_sample_inspection_camera');if(!go)go=new U.GameObject('__castle_sample_inspection_camera');let c=go.GetComponent(puer.$typeof(U.Camera));if(!c)c=go.AddComponent(puer.$typeof(U.Camera));c.CopyFrom(U.Camera.main);c.depth=100;c.fieldOfView={f};c.nearClipPlane=.2;go.transform.position=new U.Vector3({','.join(map(str,p))});go.transform.LookAt(new U.Vector3({','.join(map(str,t))}));await awaitFrames(3);return true;"
 call(['runtime','js','eval',code],label+'-camera.json')
 call(['runtime','screenshot','--out',str(O/(label+'.png'))],label+'-screenshot.json')
