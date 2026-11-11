UI.foliage = { items = {}, next = 0, names = __TREE_NAMES__ }
function UI.updateFoliage(actor)
    local f=UI.foliage
    for _=1,2 do
        if f.next>=#f.names then break end
        f.next=f.next+1
        local go=GameObject.Find(f.names[f.next])
        if go then
            local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
            for i=0,ts.Length-1 do
                local t=ts[i]
                if t.name=='Leaves' then
                    -- Leaf volumes only sense proximity: triggers never block the player.
                    -- Trunk colliders are outside this subtree and stay solid.
                    local meshes=t.gameObject:GetComponentsInChildren(typeof(UnityEngine.MeshFilter),true)
                    for j=0,meshes.Length-1 do
                        local mf=meshes[j]
                        if mf.sharedMesh and not mf.gameObject:GetComponent(typeof(UnityEngine.Collider)) then
                            local mc=mf.gameObject:AddComponent(typeof(UnityEngine.MeshCollider))
                            mc.sharedMesh=mf.sharedMesh;mc.convex=true;mc.isTrigger=true
                        end
                    end
                    local cols=t.gameObject:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
                    for j=0,cols.Length-1 do
                        local mc=cols[j].gameObject:GetComponent(typeof(UnityEngine.MeshCollider))
                        if mc then mc.convex=true end
                        cols[j].enabled=true;cols[j].isTrigger=true
                    end
                    -- Keep the authored attachment rigidly anchored. A dynamic canopy
                    -- with a world spring can drift after controller/physics contacts.
                    local joints=t.gameObject:GetComponents(typeof(UnityEngine.ConfigurableJoint))
                    for j=0,joints.Length-1 do UnityEngine.Object.Destroy(joints[j]) end
                    local rb=t.gameObject:GetComponent(typeof(UnityEngine.Rigidbody))
                    if not rb then rb=t.gameObject:AddComponent(typeof(UnityEngine.Rigidbody)) end
                    rb.useGravity=false;rb.isKinematic=true;rb.detectCollisions=true
                    f.items[#f.items+1]={t=t,rb=rb,cols=cols,home=t.localPosition,rot=t.localRotation,x=0,z=0,vx=0,vz=0}
                end
            end
        end
    end
    if f.next>=#f.names and not f.ready then f.ready=true;report('soft anchored canopies ready '..#f.items) end
    local p=actor.position+Vector3(0,1,0)
    local dt=math.min(Time.deltaTime,.033)
    for _,v in ipairs(f.items) do
        local tx,tz=0,0
        -- Always restore the local attachment, even after external teleports or bumps.
        v.t.localPosition=v.home
        if Vector3.Distance(v.t.position,p)<24 then
            local distance=100
            for j=0,v.cols.Length-1 do
                if v.cols[j].enabled then distance=math.min(distance,Vector3.Distance(v.cols[j]:ClosestPoint(p),p)) end
            end
            if distance<.7 then
                local away=v.t.position-p;away.y=0
                if away.sqrMagnitude>.001 then
                    local dir=v.t.parent and v.t.parent:InverseTransformDirection(away.normalized) or away.normalized
                    local amount=(1-distance/.7)*7
                    if not f.contactLogged then f.contactLogged=true;report("foliage soft contact active") end
                    tx=dir.z*amount;tz=-dir.x*amount
                end
            end
        end
        -- Damped angular response only: no translation or accumulating impulses.
        v.vx=v.vx+((tx-v.x)*55-v.vx*15)*dt
        v.vz=v.vz+((tz-v.z)*55-v.vz*15)*dt
        v.x=math.max(-7,math.min(7,v.x+v.vx*dt))
        v.z=math.max(-7,math.min(7,v.z+v.vz*dt))
        v.t.localRotation=v.rot*Quaternion.Euler(v.x,0,v.z)
    end
end
