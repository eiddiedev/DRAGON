-- v27 bounded UGC animation requests. This file is inlined into each actor script.
-- It never patches shared scope functions and never changes the model/Controller.
local function createAnimationPlayer(owner, prefix)
 local s={wanted=nil,played=nil,anim=nil,controller=nil,nextProbe=0,nextPlay=0,deadline=0,
  attempts=0,successes=0,errors=0,status='idle',warnings={},disposed=false}
 local function warn(key,msg)
  if s.warnings[key] then return end;s.warnings[key]=true
  CS.UnityEngine.Debug.LogWarning('['..prefix..'] '..msg)
 end
 local function resetAttempt(now)
  s.nextProbe=0;s.nextPlay=0;s.deadline=now+60;s.attempts=0;s.status='waiting'
 end
 function s.request(name)
  if s.disposed then return end
  if s.wanted~=name then s.wanted=name;resetAttempt(CS.UnityEngine.Time.realtimeSinceStartup) end
 end
 function s.resume()
  s.disposed=false;s.anim=nil;s.controller=nil;s.played=nil
  resetAttempt(CS.UnityEngine.Time.realtimeSinceStartup)
 end
 function s.tick()
  if s.disposed or not s.wanted then return end
  local now=CS.UnityEngine.Time.realtimeSinceStartup
  if now>s.deadline and s.anim==nil then
   s.status='controller timeout';warn(s.status,s.status..' for '..s.wanted);return
  end
  if now>=s.nextProbe then
   s.nextProbe=now+1
   local ok,a=pcall(function()
    local typ=typeof(CS.ModularAnim.Runtime.UGCAnimator)
    -- Both saved actors own UGCAnimator on this exact root. A seated player
    -- becomes a child, so never scan children and accidentally acquire their animator.
    return owner:GetComponent(typ)
   end)
   if not ok then s.status='component error';s.errors=s.errors+1;warn('component',tostring(a));a=nil end
   if a~=s.anim then s.anim=a;s.controller=nil;s.played=nil;resetAttempt(now);s.nextProbe=now+1 end
  end
  local ok,controller=pcall(function()return s.anim and s.anim.enabled and s.anim.Controller or nil end)
  if not ok then s.errors=s.errors+1;warn('controller',tostring(controller));controller=nil end
  if controller~=s.controller then
   s.controller=controller;s.played=nil;resetAttempt(now)
  end
  if s.played==s.wanted and controller then s.status='playing';return end
  if now>s.deadline then
   s.status=controller and 'clip timeout' or 'controller timeout'
   warn(s.status,s.status..' for '..s.wanted);return
  end
  if now<s.nextPlay then return end;s.nextPlay=now+.5
  if not controller then s.status='waiting controller';return end
  s.attempts=s.attempts+1
  local good,played=pcall(function()return s.anim:Play(s.wanted)end)
  if good and played==true then
   s.played=s.wanted;s.successes=s.successes+1;s.status='playing'
  else
   s.status=good and 'clip unavailable' or 'play error'
   if not good then s.errors=s.errors+1 end
   warn(s.status..':'..s.wanted,s.status..' '..s.wanted..(good and '' or ': '..tostring(played)))
  end
 end
 function s.stop()s.disposed=true;s.anim=nil;s.controller=nil;s.played=nil end
 function s.diagnostics()
  return {wanted=s.wanted,played=s.played,status=s.status,attempts=s.attempts,successes=s.successes,errors=s.errors}
 end
 return s
end
