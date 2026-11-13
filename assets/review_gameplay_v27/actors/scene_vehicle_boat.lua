---@id a821baf4-2e71-4757-bc3f-e090c5f6a4d8
---@referenceName scene_vehicle_boat.lua
-- Standing helm control: no sitting request and no Jump-key interaction.
---@displayName 站立开船
local U=CS.UnityEngine
local driver,button,localId,anchor,camera,saved=nil,nil,nil,nil,nil,nil
local yaw,homeY=0,0
local available=false
local helmY=1.05
local function canBoard(a)
 if not a or a:IsSitting() or a:IsFlying() or a.gameObject.transform.parent~=nil then return false end
 local p=self.transform:InverseTransformPoint(a.position)
 return math.abs(p.x)<4.8 and math.abs(p.z)<10 and p.y> -2.8 and p.y<5.5
end
local xInput,yInput=0,0
local function label()
 if button then local t=button:GetComponentInChildren(typeof(U.UI.Text),true);if t then t.text=driver and '下船' or '开船' end end
end
local function align()
 if not driver then return end
 anchor.transform.position=self.transform:TransformPoint(U.Vector3(0,helmY,-4.95))
 anchor.transform.rotation=U.Quaternion.Euler(0,yaw,0)
 local t=driver.gameObject.transform;t:SetParent(anchor.transform,true);t.localScale=saved.scale;t.localPosition=U.Vector3.zero;t.localRotation=U.Quaternion.identity
end
local function leave()
 if not driver or not saved then return end
 local a=driver;local state=saved;driver=nil;saved=nil
 -- Restore only captured colliders, preserving each original enabled value.
 for _,v in ipairs(state.colliders)do pcall(function()v.c.enabled=v.enabled end)end
 pcall(function()a.gameObject.transform:SetParent(state.parent,true);a.gameObject.transform.localScale=state.scale end)
 pcall(function()a.jumpHeight=state.jumpHeight end)
 pcall(function()a:Immobilize(false)end)
 pcall(function()a:Teleport(state.position,state.rotation)end)
 if camera then pcall(function()U.Object.Destroy(camera.gameObject)end);camera=nil end
 xInput=0;yInput=0;pcall(label)
end
function Start()
 yaw=self.transform.eulerAngles.y;homeY=self.transform.position.y
 anchor=U.GameObject(self.gameObject.name..'_HelmAnchor')
 local pos=self.transform:TransformPoint(U.Vector3(0,0,-4.95))
 local hits=U.Physics.RaycastAll(pos+U.Vector3(0,4,0),U.Vector3.down,5,-1,U.QueryTriggerInteraction.Ignore)
 for i=0,hits.Length-1 do local h=hits[i];if h.collider.transform:IsChildOf(self.transform) and h.normal.y>.7 then helmY=math.max(helmY,h.point.y-homeY+.04) end end
 self:DisableInteraction()
 DouyinInputService.onMoveInputPerform:AddListener(OnMove)
 DouyinInputService.onMoveInputCancel:AddListener(OnMoveStop)
end
function OnMove(v) if driver then xInput=v.x;yInput=v.y end end
function OnMoveStop() xInput=0;yInput=0 end
function OnActorTriggerEnter(a) if a and a.isLocal then localId=a.actorID end end
function OnActorTriggerExit(a) if a and a.isLocal and not driver then localId=nil;self:DisableInteraction() end end
function OnFocus() if not button then button=self:AddInteractorButton() end;label() end
function OnLostFocus() if button then self:RemoveInteractorButton(button);button=nil end end
function OnInteractorButtonClick(index)
 if index~=1 or not localId then return end
 if driver then leave();return end
 local a=DouyinActorService.GetActorById(localId);if not canBoard(a) then return end
 local t=a.gameObject.transform;local cs=a.gameObject:GetComponents(typeof(U.Collider));local colliders={}
 for i=0,cs.Length-1 do colliders[#colliders+1]={c=cs[i],enabled=cs[i].enabled};cs[i].enabled=false end
 saved={scale=t.localScale,parent=t.parent,position=a.position,rotation=a.rotation,jumpHeight=(a.jumpHeight==a.jumpHeight and math.abs(a.jumpHeight)>.1) and math.abs(a.jumpHeight) or 2,colliders=colliders}
 driver=a;a:Immobilize(true);a.jumpHeight=0;align();self:EnableInteraction();OnFocus()
 local main=DouyinCameraService.GetCamera()
 if main then local g=U.GameObject('boat_drive_camera');camera=g:AddComponent(typeof(U.Camera));camera:CopyFrom(main);camera.depth=main.depth+3;camera.fieldOfView=60
  pcall(function() local T=typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData);local src=main:GetComponent(T);local dst=g:AddComponent(T);if src then dst.renderPostProcessing=src.renderPostProcessing;dst.renderShadows=src.renderShadows end end)
 end
end
function Update()
 if not driver then
  local a=DouyinActorService.GetLocalActor();local near=canBoard(a)
  if near~=available then available=near;if near then localId=a.actorID;self:EnableInteraction() else self:DisableInteraction();OnLostFocus() end end
  return
 end
 local dt=math.min(U.Time.deltaTime,.05)
 local x,y=xInput,yInput
 if U.Input.GetKey('w') then y=1 elseif U.Input.GetKey('s') then y=-.5 end
 if U.Input.GetKey('a') then x=-1 elseif U.Input.GetKey('d') then x=1 end
 yaw=yaw+x*40*dt;self.transform.rotation=U.Quaternion.Euler(0,yaw,0)
 local f=U.Vector3(math.sin(math.rad(yaw)),0,math.cos(math.rad(yaw)))
 local p=self.transform.position;local target=p+f*math.max(-.5,math.min(1,y))*6*dt
 -- A downward terrain probe prevents driving onto land. Ignore the boat itself.
 local hits=U.Physics.RaycastAll(U.Vector3(target.x,40,target.z),U.Vector3.down,40,-1,U.QueryTriggerInteraction.Ignore)
 local blocked=false
 for i=0,hits.Length-1 do local hit=hits[i];if hit.collider.name=='地形块' and hit.point.y>27.4 then blocked=true end end
 if not blocked then target.y=homeY+.06*math.sin(U.Time.time);self.transform.position=target end
end
function LateUpdate()
 if not driver then return end
 align()
 if camera then
  local f=U.Vector3(math.sin(math.rad(yaw)),0,math.cos(math.rad(yaw)))
  local target=self.transform.position+U.Vector3(0,3,0)
  local eye=target-f*18+U.Vector3(0,9,0)
  camera.transform.position=eye;camera.transform.rotation=U.Quaternion.LookRotation(target-eye)
 end
end
function OnDisable()
 leave();available=false;localId=nil
 pcall(function()self:DisableInteraction()end);pcall(OnLostFocus)
end
function OnDestroy()
 OnDisable()
 pcall(function() DouyinInputService.onMoveInputPerform:RemoveListener(OnMove);DouyinInputService.onMoveInputCancel:RemoveListener(OnMoveStop) end)
 if anchor then U.Object.Destroy(anchor) end
end
