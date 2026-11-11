-- Draft adapter for the existing Unity Canvas UI. No file/image loading.
-- Caller supplies map_geometry.lua table, existing Chinese Font and callbacks.
-- Mount once; update only time/player/quest labels. Not installed in main scene.
local M = {}
function M.worldToCanvas(data,x,z,size)
    local k=size/data.size
    return (data.margin+x*data.scale-data.size/2)*k,
        (data.size/2-data.margin-(data.worldSize-z)*data.scale)*k
end
function M.mount(parent,data,font,size,onSelect)
    local U=CS.UnityEngine
    local go=U.GameObject('DragonVectorMap')
    local rt=go:AddComponent(typeof(U.RectTransform));rt:SetParent(parent,false)
    rt.sizeDelta=U.Vector2(size,size)
    local vh=U.UI.VertexHelper();local n=0;local k=size/data.size
    local function vertex(x,y,color)
        vh:AddVert(U.Vector3((x-data.size/2)*k,(data.size/2-y)*k,0),color,U.Vector4(0,0,0,0))
    end
    local function quad(points,color)
        for _,p in ipairs(points) do vertex(p[1],p[2],color) end
        vh:AddTriangle(n,n+1,n+2);vh:AddTriangle(n,n+2,n+3);n=n+4
    end
    quad({{0,0},{0,1000},{1000,1000},{1000,0}},U.Color32(236,223,196,255))
    for _,s in ipairs(data.strokes) do
        for i=2,#s.points do
            local a,b=s.points[i-1],s.points[i]
            local dx,dy=b[1]-a[1],b[2]-a[2];local len=math.sqrt(dx*dx+dy*dy)
            if len>0 then
                local ox,oy=-dy/len*s.width/2,dx/len*s.width/2
                quad({{a[1]+ox,a[2]+oy},{b[1]+ox,b[2]+oy},
                      {b[1]-ox,b[2]-oy},{a[1]-ox,a[2]-oy}},U.Color32(52,38,26,s.alpha))
            end
        end
    end
    for _,p in ipairs(data.poi) do
        local l=p.label;local x,y,w,h=l[1],l[2],l[3],l[4]
        quad({{x,y},{x,y+h},{x+w,y+h},{x+w,y}},U.Color32(236,223,196,240))
    end
    local mesh=U.Mesh();mesh.name='MapInkBatch';vh:FillMesh(mesh);vh:Dispose()
    local cr=go:AddComponent(typeof(U.CanvasRenderer));cr.materialCount=1
    cr:SetMaterial(U.UI.Graphic.defaultGraphicMaterial,0)
    cr:SetTexture(U.Texture2D.whiteTexture);cr:SetMesh(mesh)
    local function text(name,value,x,y,w,h,fs)
        local node=U.GameObject(name);local r=node:AddComponent(typeof(U.RectTransform));r:SetParent(rt,false)
        r.sizeDelta=U.Vector2(w*k,h*k);r.anchoredPosition=U.Vector2((x-500)*k,(500-y)*k)
        local t=node:AddComponent(typeof(U.UI.Text));t.font=font;t.fontSize=math.floor(fs*k)
        t.text=value;t.color=U.Color(52/255,38/255,26/255,1)
        t.alignment=U.TextAnchor.MiddleCenter;t.raycastTarget=false
        return t,node
    end
    text('MapTitle','龍 眠 之 境',500,63,400,40,27)
    text('North','北',110,810,40,25,15)
    for _,p in ipairs(data.poi) do
        local l=p.label;local label,node=text(p.id,p.name,l[1]+l[3]/2,l[2]+l[4]/2,l[3],l[4],15)
        if onSelect then
            label.raycastTarget=true
            local button=node:AddComponent(typeof(U.UI.Button));button.targetGraphic=label
            local id=p.id;button.onClick:AddListener(function() onSelect(id) end)
        end
    end
    local clock=text('WorldClock','世界时刻 · 同步中',760,945,330,30,16)
    return {go=go,mesh=mesh,clock=clock,SetClock=function(value) clock.text=value or '世界时刻 · 同步中' end,
        Destroy=function() U.Object.Destroy(go);U.Object.Destroy(mesh) end}
end
return M
