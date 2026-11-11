"""Prepare ONLY a reviewable patch from today's main script; never install or save the scene."""
from pathlib import Path
import hashlib,difflib,json
from lupa import LuaRuntime
D=Path(__file__).parent
P=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scripts/modules/world_main.lua')
s=P.read_text();original=s
assert s.count('function UI.enterPlay(actor)')==1 and s.count('function UI.finishBook(actor)')==1
s=s.replace('function UI.enterPlay(actor)','function UI.enterPlayAfterContract(actor)',1)
s=s.replace('function UI.finishBook(actor)','function UI.finishBookAfterContract(actor)',1)
marker='function UI.updateMap(actor, dt)'
addition='''-- RPG bridge: the book owns the opening transition; RPG owns class selection.
function UI.getRpg()
    if UI.rpg then return UI.rpg end
    local root=UnityEngine.GameObject.Find("龙眠职业与战斗")
    local component=root and root:GetDouyinScript("dragon_rpg.lua")
    if component then UI.rpg=component.script end
    return UI.rpg
end
function UI.contractThen(actor, continuation)
    local rpg=UI.getRpg()
    if not rpg then
        toast("职业之书正在准备，请稍候")
        return false
    end
    local profile=rpg.GetProfile()
    if profile and profile.class then continuation(actor);return true end
    local before=UI.state
    if rpg.OpenContract(false,function()
        continuation(actor)
    end) then UI.state="contract";return true end
    UI.state=before
    return false
end
function UI.enterPlay(actor)
    UI.contractThen(actor,UI.enterPlayAfterContract)
end
function UI.finishBook(actor)
    UI.contractThen(actor,UI.finishBookAfterContract)
end

'''
s=s.replace(marker,addition+marker,1)
needle='    updateDayNight(actor)\n    updatePortals(actor)'
assert s.count(needle)==1
s=s.replace(needle,'''    local rpg=UI.getRpg()
    if rpg then
        rpg.SetExplorationReady(UI.state=="play")
        rpg.SetContext({menu=UI.state~="play",mounted=DR.rider~=nil or actor:IsSitting() or actor:IsFlying()})
    end
'''+needle,1)
ok,error=LuaRuntime(unpack_returned_tuples=True).eval('function(s)local f,e=load(s);return f~=nil,e end')(s)
assert ok,error
(D/'world_main.book-PROPOSED.lua').write_text(s)
(D/'book-integration.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='current/world_main.lua',tofile='proposed/world_main.lua')))
(D/'book-patch-manifest.json').write_text(json.dumps({'source':str(P),'sha256':hashlib.sha256(original.encode()).hexdigest(),'installed':False,'scope':'opening contract gates only; no transforms or castle edits','remaining':'player persistence, tree respec native trigger, shared battle/mainline are not installed'},ensure_ascii=False,indent=2))
print('Prepared book gate patch; main scene/source unchanged')
