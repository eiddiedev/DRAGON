"""Temporary inspection camera; never saved to scene or source."""
import sys
from castle_smooth_runtime_cli import call,O
mode,label=sys.argv[1:]
shots={'hall':((127,75.1,170),(127,75.0,186),75),'library':((117.6,74.5,176),(117.3,74.5,181),78),'wide':((155,108,95),(127,100,178),57),'front':((130,100,110),(127,96,176),55),'right':((181,97,156),(130,93,178),60),'left':((77,96,154),(124,91,177),60),'back':((83,108,226),(127,99,180),60),'wall':((153,80,146),(131,77,160),65),'gate':((127,76,146),(127,77,160),62),'entrance':((127,75.5,161),(127,77,168),70),'facade':((127,87,151),(127,86,168),80),'clock':((113,96,147),(117.5,94,168),58)}
if mode=='restore':
 call(['runtime','js','eval',"const U=CS.UnityEngine;const go=U.GameObject.Find('__castle_smooth_inspection_camera');if(go)U.Object.Destroy(go);await awaitFrames(2);return !U.GameObject.Find('__castle_smooth_inspection_camera');"],label+'.json')
else:
 p,t,f=shots[mode]
 code=f"const U=CS.UnityEngine;let go=U.GameObject.Find('__castle_smooth_inspection_camera');if(!go)go=new U.GameObject('__castle_smooth_inspection_camera');let c=go.GetComponent(puer.$typeof(U.Camera));if(!c)c=go.AddComponent(puer.$typeof(U.Camera));c.CopyFrom(U.Camera.main);c.depth=100;c.fieldOfView={f};c.nearClipPlane=.2;go.transform.position=new U.Vector3({','.join(map(str,p))});go.transform.LookAt(new U.Vector3({','.join(map(str,t))}));await awaitFrames(3);return true;"
 call(['runtime','js','eval',code],label+'-camera.json')
 call(['runtime','screenshot','--out',str(O/(label+'.png'))],label+'-screenshot.json')
