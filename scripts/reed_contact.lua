-- Two-stage skin bending: roots stay planted; actor pushes stems away then they recover.
UI.reeds={names=__REED_NAMES__,items={},next=0,tick=0}
function UI.updateReeds(actor)
    local f=UI.reeds
    if f.next<#f.names then
        for _=1,5 do
            f.next=f.next+1
            local name=f.names[f.next]
            if not name then break end
            local go=GameObject.Find(name)
            if go then
                local an=go:GetComponentInChildren(typeof(UnityEngine.Animation),true)
                if an then an:Stop();an.enabled=false end
                if name:match('^golden_geometry_') then
                    local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
                    local tone=(tonumber(name:match('(%d+)$')) or 0)%4
                    f.geometryMats=f.geometryMats or {}
                    for ri=0,rs.Length-1 do
                        if not f.geometryMats[tone] then
                            local sh=UnityEngine.Shader.Find('Universal Render Pipeline/Lit')
                            local m=sh and UnityEngine.Material(sh) or UnityEngine.Material(rs[ri].sharedMaterial)
                            local c=UnityEngine.Color(.58+tone*.035,.43+tone*.03,.21+tone*.023,1)
                            for _,key in ipairs({'_BaseColor','_Color'}) do if m:HasProperty(key) then m:SetColor(key,c) end end
                            m:SetFloat('_Cull',0);m:SetFloat('_Smoothness',.1)
                            f.geometryMats[tone]=m
                        end
                        rs[ri].sharedMaterial=f.geometryMats[tone]
                    end
                end
                if not name:match('^golden_geometry_') then
                -- The editor replaces imported glTF cutout materials with its opaque shader.
                -- Preserve the atlas and explicitly restore alpha clipping for runtime foliage.
                local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
                for ri=0,rs.Length-1 do
                    local src=rs[ri].sharedMaterial
                    local tex=nil
                    for _,key in ipairs({'_BaseTex','_BaseMap','_MainTex'}) do
                        if src:HasProperty(key) then tex=src:GetTexture(key);if tex then break end end
                    end
                    if not f.material and tex then
                        local sh=UnityEngine.Shader.Find('Universal Render Pipeline/Lit')
                        if not sh then sh=UnityEngine.Shader.Find('Legacy Shaders/Transparent/Cutout/Diffuse') end
                        if sh then
                            local m=UnityEngine.Material(sh)
                            for _,key in ipairs({'_BaseMap','_MainTex'}) do if m:HasProperty(key) then m:SetTexture(key,tex) end end
                            for _,key in ipairs({'_BaseColor','_Color'}) do if m:HasProperty(key) then m:SetColor(key,UnityEngine.Color(1,1,1,1)) end end
                            m:SetFloat('_AlphaClip',1);m:SetFloat('_Cutoff',.35);m:SetFloat('_Cull',0);m:SetFloat('_Surface',0)
                            m:SetFloat('_ZWrite',1);m:SetFloat('_Smoothness',.15)
                            m:EnableKeyword('_ALPHATEST_ON');m:SetOverrideTag('RenderType','TransparentCutout');m.renderQueue=2450
                            f.material=m;report('reed cutout shader '..sh.name)
                        end
                    end
                    if f.material then rs[ri].sharedMaterial=f.material end
                end
                end
                local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
                local lower,upper
                for j=0,ts.Length-1 do
                    if ts[j].name=='reed_lower' then lower=ts[j] end
                    if ts[j].name=='reed_upper' then upper=ts[j] end
                end
                if lower and upper then
                    local cols=go:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
                    for j=0,cols.Length-1 do cols[j].enabled=false end
                    f.items[#f.items+1]={root=go.transform,lo=lower,hi=upper,lr=lower.localRotation,hr=upper.localRotation,x=0,z=0,vx=0,vz=0,phase=go.transform.position.x*.32+go.transform.position.z*.22}
                end
            end
        end
        if f.next>=#f.names then report('reeds ready '..#f.items..'/'..#f.names) end
    end
    f.tick=f.tick+1
    local p=actor.position
    local dt=math.min(Time.deltaTime,.033)
    for i,v in ipairs(f.items) do
        local rp=v.root.position
        local dx,dz=rp.x-p.x,rp.z-p.z
        local d2=dx*dx+dz*dz
        if d2<144 or (i+f.tick)%6==0 then
            local tx,tz=0,0
            if d2<4 and math.abs(rp.y-p.y)<2.5 then
                local dist=math.sqrt(d2)
                local dir=v.root:InverseTransformDirection(Vector3(dx/math.max(.05,dist),0,dz/math.max(.05,dist)))
                local strength=(1-math.min(1,dist/2))
                tx=dir.z*32*strength;tz=-dir.x*32*strength
                if not f.contactLogged and strength>.3 then f.contactLogged=true;report('reeds contact bend active') end
            end
            v.vx=v.vx+((tx-v.x)*45-v.vx*10)*dt
            v.vz=v.vz+((tz-v.z)*45-v.vz*10)*dt
            v.x=v.x+v.vx*dt;v.z=v.z+v.vz*dt
            local wind=math.sin(Time.time*1.1+v.phase)*2.2+math.sin(Time.time*.43+v.phase*.45)*1.1
            v.lo.localRotation=v.lr*Quaternion.Euler(v.x+wind,0,v.z+wind*.42)
            v.hi.localRotation=v.hr*Quaternion.Euler(v.x*.65+wind*1.4,0,v.z*.65+math.sin(Time.time*1.6+v.phase)*1.7)
        end
    end
end
