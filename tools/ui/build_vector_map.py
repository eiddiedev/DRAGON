#!/usr/bin/env python3
"""Offline vector map authoring. Does not read/write the live editor project.
Coastlines come from native height data; decorative forests are sparse regional symbols.
SVG is an inspection artifact. Runtime consumes generated Lua strokes, not an image.
"""
import json, math, struct, hashlib
from pathlib import Path
from xml.sax.saxutils import escape
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/ui_v2/vector'
OUT.mkdir(parents=True, exist_ok=True)
raw = (ROOT/'assets/terrain/native/heights.f32').read_bytes()
heights = struct.unpack('<66049f', raw)
strokes = []
def line(points, width=1.4, alpha=220):
    if len(points)>1:
        strokes.append({'points':[[round(x,2),round(y,2)] for x,y in points], 'width':width, 'alpha':alpha})
def wp(x,z): return (80+x*3.28125, 80+(256-z)*3.28125)
def circle(x,y,r,width=1.3,alpha=220):
    line([(x+math.cos(i*math.pi/12)*r,y+math.sin(i*math.pi/12)*r) for i in range(25)],width,alpha)
def contour(level,step=2):
    # Marching squares with interpolated crossings; join to paths before simplifying.
    segments=[]
    for z in range(0,256,step):
        for x in range(0,256,step):
            corners=[(x,z),(x+step,z),(x+step,z+step),(x,z+step)]
            vals=[heights[b*257+a]*256 for a,b in corners]
            hits=[]
            for i in range(4):
                j=(i+1)%4
                if (vals[i]>level)!=(vals[j]>level):
                    t=(level-vals[i])/(vals[j]-vals[i]);a,b=corners[i],corners[j]
                    hits.append((round(a[0]+(b[0]-a[0])*t,4),round(a[1]+(b[1]-a[1])*t,4)))
            for i in range(0,len(hits),2): segments.append((hits[i],hits[i+1]))
    graph={}
    for a,b in segments: graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
    paths=[]
    while graph:
        start=next((p for p,v in graph.items() if len(v)==1),next(iter(graph)))
        path=[start];p=start
        while p in graph:
            q=graph[p].pop()
            if not graph[p]: del graph[p]
            graph[q].remove(p)
            if not graph[q]: del graph[q]
            path.append(q);p=q
        if len(path)>6: paths.append(path)
    return paths

def simplify(points,tol=.65):
    if len(points)<3:return points
    a,b=points[0],points[-1];dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
    distances=[]
    for x,y in points[1:-1]:
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den)) if den else 0
        distances.append(math.hypot(x-a[0]-dx*t,y-a[1]-dy*t))
    d=max(distances)
    if d<=tol:return [a,b]
    i=distances.index(d)+1
    return simplify(points[:i+1],tol)[:-1]+simplify(points[i:],tol)

for level,width,alpha in [(26.6,2.0,245),(28.5,.8,100),(44,.8,65),(57,.8,65)]:
    for path in contour(level):line([wp(*p) for p in simplify(path)],width,alpha)
# Small, bounded atlas ornaments: no scene tree enumeration or per-tree UI nodes.
for x,z,s in [(33,178,13),(44,169,16),(52,184,11),(39,191,12),(68,199,14),
              (160,229,22),(178,219,17),(151,215,14),(169,201,12),(187,194,13)]:
    u,v=wp(x,z);line([(u-s,v),(u,v-s*1.45),(u+s,v)],1.5)
    line([(u,v-s*1.45),(u+s*.2,v-s*.5),(u-s*.1,v-s*.65)],1)
    for i in range(1,5):line([(u+s*i/5,v),(u+s*i/8,v-s*(1-i/5))],.8,140)
for x,z in [(46,122),(42,132),(50,138),(58,125),(64,135),(70,123),
            (192,178),(203,183),(211,172),(198,164),(205,154),(220,162)]:
    u,v=wp(x,z)
    line([(u-6,v),(u-4,v-5),(u-7,v-5),(u,v-16),(u+7,v-5),(u+4,v-5),(u+6,v),(u-6,v)],1,155)
    line([(u,v),(u,v+4)],1,155)
# Wheat region uses a handful of stalks, not the grass instances.
for x,z in [(108,40),(115,36),(122,43),(128,34),(136,39),(118,29),(108,31)]:
    u,v=wp(x,z);line([(u,v+6),(u,v-7)],.9,150)
    for dy in [-5,0,5]:
        line([(u-3,v+dy-4),(u,v+dy),(u+3,v+dy-4)],.9,150)
poi=json.loads((ROOT/'docs/ui/poi.json').read_text())
poi.extend([{'id':'wheat','name':'麦金原野','x':121,'z':39},
            {'id':'stable','name':'马厩','x':146,'z':46.5},
            {'id':'ghost_challenge','name':'幽灵挑战','x':157,'z':27,'provisional':True}])
for p in poi:
    x,y=wp(p['x'],p['z']);circle(x,y,3,1.4)
    if p.get('major'):circle(x,y,5.5,.8)
    # Architectural glyphs for navigation, rendered as batched ink strokes.
    if p['id'] in ['castle','village','stable','witch','lighthouse']:
        line([(x-10,y-10),(x-10,y-24),(x,y-32),(x+10,y-24),(x+10,y-10),(x-10,y-10)],1.4)
        line([(x-3,y-10),(x-3,y-18),(x+3,y-18),(x+3,y-10)],1)
        if p['id']=='castle':
            for d in [-17,17]:line([(x+d-4,y-10),(x+d-4,y-34),(x+d,y-42),(x+d+4,y-34),(x+d+4,y-10)],1.2)
# Small cartographic silhouettes; all share the same ink batch.
for p in poi:
    x,y=wp(p['x'],p['z'])
    if p['id']=='windmill':
        line([(x-5,y-9),(x-3,y-29),(x+3,y-29),(x+5,y-9),(x-5,y-9)],1.2)
        for dx,dy in [(-12,-12),(12,-12),(12,12),(-12,12)]:
            line([(x,y-25),(x+dx,y-25+dy),(x+dx*.65-dy*.2,y-25+dy*.65+dx*.2),(x,y-25)],1)
    elif p['id']=='mushroom':
        for dx,dy,r in [(-9,-15,7),(3,-23,10),(14,-12,5)]:
            line([(x+dx+math.cos(a*math.pi/12)*r,y+dy-math.sin(a*math.pi/12)*r*.6) for a in range(13)],1.2)
            line([(x+dx-r,y+dy),(x+dx+r,y+dy)],1)
            line([(x+dx-1,y+dy),(x+dx-1,y+dy+7),(x+dx+2,y+dy+7),(x+dx+2,y+dy)],1)
    elif p['id']=='bridge':
        line([(x-16,y-9),(x-12,y-16),(x+12,y-16),(x+16,y-9)],1.6)
        for dx in range(-12,13,6):line([(x+dx,y-16),(x+dx,y-11)],.8)
    elif p['id']=='camp':
        line([(x-12,y-10),(x,y-28),(x+14,y-10),(x-12,y-10),(x+2,y-26),(x+5,y-10)],1.2)
    elif p['id']=='glow_tree':
        for dx,dy,r in [(-7,-23,8),(6,-24,9),(0,-32,8)]:circle(x+dx,y+dy,r,1,190)
        line([(x-2,y-9),(x-2,y-20),(x-8,y-25),(x,y-19),(x+6,y-27),(x+2,y-19),(x+2,y-9)],1.2)
    elif p['id']=='harbor':
        line([(x-14,y-15),(x-7,y-9),(x+10,y-9),(x+17,y-15),(x-14,y-15)],1.2)
        line([(x,y-15),(x,y-35),(x+12,y-18),(x,y-18)],1.2)
    elif p['id']=='ghost_challenge':
        circle(x,y-23,12,1,200)
        line([(x-6,y-20),(x-4,y-30),(x,y-33),(x+4,y-30),(x+6,y-20),(x+2,y-23),(x,y-19),(x-3,y-23),(x-6,y-20)],1.1)
# Compass and fine double border.
for margin in [27,33]:line([(margin,margin),(1000-margin,margin),(1000-margin,1000-margin),(margin,1000-margin),(margin,margin)],.8,140)
circle(110,868,29,.8,170)
for angle in [0,math.pi/2,math.pi,math.pi*1.5]:
    dx,dy=math.sin(angle),-math.cos(angle)
    line([(110-dy*5,868+dx*5),(110+dx*39,868+dy*39),(110+dy*5,868-dx*5),(110-dy*5,868+dx*5)],1.1)
# Label placement minimizes collisions and stays inside the map. Leader lines preserve exact locations.
occupied=[]
for p in sorted(poi,key=lambda p:p['z'],reverse=True):
    x,y=wp(p['x'],p['z']);w=len(p['name'])*15+12;h=24
    choices=[]
    for radius in [10,29,49,70]:
        for dx,dy in [(radius,-12),(-w-radius,-12),(-w/2,radius),(-w/2,-radius-h)]:
            bx,by=x+dx,y+dy
            overlap=sum(max(0,min(bx+w,b+w2)-max(bx,b))*max(0,min(by+h,c+h2)-max(by,c)) for b,c,w2,h2 in occupied)
            overflow=max(0,48-bx)+max(0,bx+w-952)+max(0,48-by)+max(0,by+h-925)
            choices.append((overlap+overflow*100+radius*.3,bx,by))
    _,bx,by=min(choices);occupied.append((bx,by,w,h));p.update(label=[round(bx,2),round(by,2),w,h])
    end=(max(bx,min(x,bx+w)),max(by,min(y,by+h)))
    line([(x,y),end],.65,100)
data={'size':1000,'worldSize':256,'margin':80,'scale':3.28125,'strokes':strokes,'poi':poi,
      'terrainSha256':hashlib.sha256(raw).hexdigest(),'forestSymbols':12}
(OUT/'map_geometry.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
def lua(v):
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if isinstance(v,dict):return '{'+','.join('['+lua(k)+']='+lua(val) for k,val in v.items())+'}'
    if isinstance(v,list):return '{'+','.join(map(lua,v))+'}'
    return str(v)
(OUT/'map_geometry.lua').write_text('-- Generated offline by tools/ui/build_vector_map.py\nreturn '+lua(data)+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">','<rect width="1000" height="1000" fill="#ecdfc4"/>']
for s in strokes:
    pts=' '.join(f'{x},{y}' for x,y in s['points'])
    svg.append(f'<polyline points="{pts}" fill="none" stroke="#34261a" stroke-width="{s["width"]}" opacity="{s["alpha"]/255:.3f}" stroke-linejoin="round"/>')
for p in poi:
    x,y,w,h=p['label'];svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ecdfc4" fill-opacity=".93"/><text x="{x+w/2}" y="{y+17}" text-anchor="middle" font-family="LXGW WenKai,STKaiti,serif" font-size="15" fill="#34261a">{escape(p["name"])}</text>')
svg+=['<text x="500" y="73" text-anchor="middle" font-family="STKaiti,serif" font-size="27" fill="#34261a">龍 眠 之 境</text>','<text x="110" y="817" text-anchor="middle" font-size="15">北</text>','</svg>']
(OUT/'map_preview.svg').write_text('\n'.join(svg))
segments=sum(len(s['points'])-1 for s in strokes)
assert segments*4<60000, 'Split into batches before exceeding mesh 16-bit indices'
assert len({p['id'] for p in poi})==len(poi)
print(json.dumps({'strokes':len(strokes),'lineSegments':segments,'meshVertices':segments*4,'forestSymbols':12,'poi':len(poi),'luaBytes':(OUT/'map_geometry.lua').stat().st_size}))
