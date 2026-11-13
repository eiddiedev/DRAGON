---@id c896d1fb-6b7d-48a2-9690-0ba8f0a43f19
---@sourceScriptId d2269ea1-ecd8-4cd0-bf9c-9ee09965e230
---@referenceName dragon_progress_rules.lua
---@displayName 龙契主线规则
local materials={mushroom=true,flower=true,wool=true}
local classes={melee=true,mage=true,ranged=true}
local potions={grow=true,shrink=true,sheep=true}
local costs={moon=30,ember=3,stardew=1}
local function copy(x)if type(x)~='table'then return x end;local y={};for k,v in pairs(x)do y[k]=copy(v)end;return y end
local function count(v)return type(v)=='number'and v==v and v>=0 and v%1==0 and v<1000000000000 end
function New()
 return{schema=2,revision=0,class=nil,moon=0,ember=0,stardew=0,mushroom=0,flower=0,wool=0,charred=0,potions={wind=0,grow=0,shrink=0,glow=0,sheep=0},deposited={moon=0,ember=0,stardew=0},pact=false,hatchReady=false,day=0,daily={mushroom=0,flower=0,wool=0,ember=0},cookUntil=0,receipts={},receiptOrder={},battles={}}
end
function Copy(p)return copy(p)end
function Validate(p)
 if type(p)~='table'or p.schema~=2 then return false end
 for _,k in ipairs({'moon','ember','stardew','mushroom','flower','wool','charred','revision','day','cookUntil'})do if not count(p[k])then return false end end
 if p.class~=nil and not classes[p.class]then return false end
 for _,k in ipairs({'potions','deposited','daily','receipts','receiptOrder','battles'})do if type(p[k])~='table'then return false end end
 for k in pairs(potions)do if not count(p.potions[k])then return false end end
 for k,c in pairs(costs)do if not count(p.deposited[k])or p.deposited[k]>c then return false end end
 for k in pairs({mushroom=1,flower=1,wool=1,ember=1})do if not count(p.daily[k])then return false end end
 return true
end
function Apply(current,op)
 if not Validate(current)then return nil,'进度异常，本次操作未执行'end
 if type(op)~='table'or type(op.id)~='string'or #op.id>140 or not count(op.day)or type(op.now)~='number'then return nil,'请求无效'end
 if current.receipts[op.id]then return copy(current),current.receipts[op.id],true end
 local p=copy(current);local result=''
 if op.day>p.day then p.day=op.day;p.daily={mushroom=0,flower=0,wool=0,ember=0}end
 if op.day<p.day then return nil,'服务器日期尚未同步'end
 if op.kind=='class'then
  if not classes[op.class]then return nil,'职业无效'end;p.class=op.class;result='誓约已签订'
 elseif op.kind=='gather'then
  if not materials[op.material]or not op.isDay then return nil,'白天才能采集'end
  p[op.material]=p[op.material]+1;p.daily[op.material]=p.daily[op.material]+1;result='采集成功'
 elseif op.kind=='stardew'then
  local missing={};for _,v in ipairs({{'mushroom','蘑菇',3},{'flower','月见花',3},{'wool','羊毛',1}})do if p[v[1]]<v[3]then missing[#missing+1]=v[2]..' '..(v[3]-p[v[1]])..'份'end end
  if #missing>0 then return nil,'还缺：'..table.concat(missing,'、')end
  p.mushroom=p.mushroom-3;p.flower=p.flower-3;p.wool=p.wool-1;p.stardew=p.stardew+1;result='获得星露'
 elseif op.kind=='brew'then
  if not potions[op.potion]then return nil,'药水无效'end
  result='你喝下了女巫的神秘药水'
 elseif op.kind=='cookStart'then
  if p.cook or op.now<p.cookUntil then return nil,'请稍后再烤'end
  if p.mushroom<1 then return nil,'需要一份蘑菇'end
  p.mushroom=p.mushroom-1;p.cook={token=op.id,at=op.now,duration=op.duration or 5};p.cookUntil=math.floor(op.now+20);result='开始烹饪'
 elseif op.kind=='cookFinish'then
  if not p.cook or p.cook.token~=op.token then return nil,'这串蘑菇已结算'end
  local ratio=math.max(0,(op.now-p.cook.at)/p.cook.duration);p.cook=nil
  if ratio>=.55-1e-7 and ratio<=.68+1e-7 then
   if p.daily.ember<3 then p.ember=p.ember+1;p.daily.ember=p.daily.ember+1;result='完美！获得火种'else result='完美！今日火种已满三份'end
  elseif ratio>.68 and ratio<=.85+1e-7 then result='烤熟了'
  elseif ratio>.85 then p.charred=p.charred+1;result='烤焦了，下次早点松手'else result='还没烤熟'end
 elseif op.kind=='cookCancel'then p.cook=nil;result='烹饪已中断'
 elseif op.kind=='roast'then
  -- v15 烤蘑菇：光标落在金色火区时出锅算烤熟，得火种；否则是生的
  if p.mushroom<1 then return nil,'需要一份蘑菇'end
  p.mushroom=p.mushroom-1
  if op.hit==true then p.ember=p.ember+1;result='烤熟了，得到一枚火种'else result='没烤熟'end
 elseif op.kind=='drink'then
  if not potions[op.potion]or p.potions[op.potion]<1 then return nil,'没有这瓶药水'end
  p.potions[op.potion]=p.potions[op.potion]-1;result='饮用药水'
 elseif op.kind=='deposit'then
  local moved=0;for k,c in pairs(costs)do local n=math.min(p[k],c-p.deposited[k]);p[k]=p[k]-n;p.deposited[k]=p.deposited[k]+n;moved=moved+n end
  if moved==0 then return nil,p.pact and '已经缔结龙契'or '暂时没有可供奉的材料'end
  p.hatchReady=p.deposited.moon==30 and p.deposited.ember==3 and p.deposited.stardew==1;result=p.hatchReady and '龙魂正在苏醒'or '供奉完成'
 elseif op.kind=='hatch'then
  if not p.hatchReady then return nil,'材料尚未集齐'end;p.pact=true;result='龙魂归位，龙契已成'
 elseif op.kind=='battle'then
  if type(op.battleId)~='string'or #op.battleId>120 or not count(op.amount)or op.amount>100 then return nil,'战斗结算无效'end
  if p.battles[op.battleId]then return p,'这场战斗已结算',true end
  p.battles[op.battleId]=true;p.moon=p.moon+op.amount;result='获得月辉'
 else return nil,'未知操作'end
 p.revision=p.revision+1;p.receipts[op.id]=result;p.receiptOrder[#p.receiptOrder+1]=op.id
 while #p.receiptOrder>24 do local old=table.remove(p.receiptOrder,1);p.receipts[old]=nil end
 return p,result,false
end
function EggStage(p)
 if p.pact then return 3 end
 local total=p.deposited.moon/30+p.deposited.ember/3+p.deposited.stardew
 return total==0 and 0 or(total<2 and 1 or 2)
end
function ObjectiveIndex(p)
 if not p.class then return 1 end
 if p.pact then return 7 end
 if p.hatchReady then return 6 end
 if p.stardew+p.deposited.stardew<1 then return 2 end
 if p.ember+p.deposited.ember<3 then return 3 end
 if p.moon+p.deposited.moon<30 then return 4 end
 return 5
end
-- 六个步骤各自是否已完成（誓约之书左页的清单）
function Steps(p)
 return {p.class~=nil,p.stardew+p.deposited.stardew>=1,p.ember+p.deposited.ember>=3,p.moon+p.deposited.moon>=30,p.hatchReady or p.pact,p.pact}
end
function Objective(p)
 local i=ObjectiveIndex(p)
 local t={{'在古书上签下职业誓约','出生古书'},{'白天采集蘑菇3、月见花3、羊毛1，交给女巫调制星露','女巫药铺'},{'在营地把蘑菇烤熟，攒够三枚火种','守夜人营地'},{'入夜后到麦田魔法阵迎战影灵，攒够三十月辉','影灵试炼'},{'三样供品已备齐，献给祭坛上的龙魂之卵','唤龙祭坛'},{'回到唤龙祭坛，见证龙魂苏醒','唤龙祭坛'},{'龙契已成，点左侧龙印唤墨曜降临','唤龙祭坛'}}
 return t[i][1],t[i][2]
end
