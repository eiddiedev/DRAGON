# Lua 脚本编写

编写、修改或审查 WPrefab 的 Lua 源码时，先读本页的脚本结构、参数声明与通用规则，再按任务读取末尾的具体参考。只改实例参数无需阅读本页。

## 编写前确认

编写前，先确认要实现的行为、脚本保存路径和挂载节点。根据资源类型阅读对应的行为指南，只加载本次需要的参考，复用已确认的信息。只解释或审查 Lua 时，不修改场景。

如果需要新增资源或节点，先完成资源准备和实例装配，再编写使用它们的 Lua。只修改已有实例的脚本时，不重新生成模型等资源。

核对代码将调用的接口、事件、字段和 `require` 所需的全部模块，确认它们在当前环境中可用。缺少必要信息时，明确说明缺少什么，不猜名称或用法。绑定到节点的普通脚本不能通过 `require` 加载。官方文件和用于识别脚本作用域的内部标记由系统维护，AI 不得自行创建或修改。

使用模板时，按模板指南检查所需组件、Runtime Host 关联和需要调用的其它脚本方法。生成模板源码不代表这些条件已经满足。

## 文件形态

- 顶层直接声明 `function Start()`、`function Update()`、`function OnEnable()`、`function OnDisable()` 等生命周期或平台回调。
- 文件开头写一句简短用途注释，后面保持局部变量、helper、生命周期函数清晰分组。
- 每个用户可见脚本必须在第一行可执行代码之前声明且只声明一次 `---@displayName {中文名称}`。名称应直接描述该脚本的用途，例如 `---@displayName 车辆属性`。
- `self` 是当前脚本的 C# `DouyinScript` 组件，不是 GameObject，也不是保存 Lua 函数的 script table。通过 `self.gameObject`、`self.transform` 访问挂载对象；当前文件声明的 `PlayAction`、`GetState` 等 Lua 函数不能写成 `self.PlayAction`、`self.GetState`。
- 一个 Lua chunk 职责过多或 active locals 接近 200 时，按职责拆分文件；不要只为缩短文件机械拆分。

## 参数声明

参数注释声明名称、类型、默认值及面板显示方式。新增或修改脚本前，必须先判断哪些值应向用户提供，再填写声明。

在 Lua 文件头部、第一行可执行代码之前，用注释声明需要显示在面板中的参数。运行时会注入 `---@var` 声明的同名值，脚本可以直接读写；不要再声明同名 `local`。
每个脚本只保留一个 `---@start` / `---@end` 块，普通参数与 `---@varSync` 同步变量合并在这个块内。采用 Hamlet 示例时也必须补齐本节的声明格式，不直接照搬缺少块边界或中文名称的片段。

创建或修改参数声明时，数值参数默认不写 `---@range`，让用户直接输入需要的值。只有用户明确要求限制或调整范围，或者明确提到上下限或步长时才使用该指令。

### 三类参数

面板只提供少量、明确、可以独立调整的入口，参数分成三类：

- **默认显示**：用户容易理解、经常调整、会直接影响体验，而且能单独安全修改。用户要编辑的文案和含义明确的功能开关也属于这一类。
- **按需显示**：很少调整、需要和其它参数配合，或需要物理、动画、相机等专业知识。默认使用已经验证过的 `local` 值；只有当前目标确实需要调节时才放到面板。
- **不显示**：运行状态、缓存引用、计时器当前值、模型尺寸等已知信息、计算结果、接口名、资源 ID、节点路径、算法固定值、重试和安全保护值。保留为 `local` 或模板内部配置。

分类时再检查：

- 一个面板参数已经能表达目标时，不再把它背后的底层系数一起显示。
- 专用模板可以比通用示例显示更少的参数，但资源指南明确要求的参数必须保留。
- 不按固定数量增减参数。重点是面板易懂、参数互不打架、默认组合可以直接使用。
- 不要隐藏用户必须编辑的文案或脚本明确提供的功能开关。

### 注释格式

| 注释指令 | 是否必需 | 作用 | 示例 |
| --- | --- | --- | --- |
| `---@start` | 必需 | 参数区开始 | - |
| `---@end` | 必需 | 参数区结束 | - |
| `---@var {name}:{type}={default}` | 必需 | 声明参数名、类型和默认值 | `---@var MoveSpeed:number=3.5` |
| `---@name {中文名}` | 必需 | 面板中显示的中文名 | `---@name 移动速度` |
| `---@desc {描述}` | 可选 | 鼠标悬停时显示的说明 | `---@desc 每秒移动距离` |
| `---@range {min,max[,step]}` | 可选，仅用户明确要求时 | 按用户要求设置数值范围和可选步长 | `---@range 0,10,0.1` |
| `---@group {分组名}` | 可选 | 把同组参数放进同一个可折叠区域 | `---@group 运动` |
| `---@enum {k1=label1,k2=label2}` | 可选 | 为可选值提供面板文案 | `---@enum 1=简单,2=困难` |
| `---@hidden` | 可选 | 不在面板中显示 | - |

需要多人同步状态时，可使用 `---@varSync {name}:{type}[={default}]` 声明网络同步变量；默认值可以省略。内部同步状态在声明后加 `---@hidden`，不要作为可调参数显示，也不要改为同名 `local`。例如：

```lua
---@displayName 交互控制
---@start
---@var MoveSpeed:number=3.5
---@name 移动速度
---@varSync isActive:bool=false
---@hidden
---@end
```

### 支持声明的类型及示例

以下片段演示不同类型的单项声明，使用时放入同一个 `---@start` / `---@end` 块，不为每个参数单独建块。

#### int

```lua
---@var SpawnCount:int=3
---@name 生成数量
---@desc 单次触发时生成的敌人数量
```

#### number

浮点数。

```lua
---@var MoveSpeed:number=3.5
---@name 移动速度
---@desc 角色每秒移动距离，单位米/秒
```

#### boolean

```lua
---@var EnablePatrol:boolean=true
---@name 启用巡逻
---@desc 开启后 NPC 会按路径点自动巡逻
```

#### string

```lua
---@var InteractMode:string="press"
---@name 交互方式
---@desc 玩家触发交互的方式
---@enum press=按键触发,auto=靠近触发,none=禁用
```

#### Color

RGBA 颜色。

```lua
---@var BodyColor:Color=(0.2,0.7,1,1)
---@name 车身颜色
```

#### Vector2 / Vector3 / Vector4

```lua
---@var SpawnOffset:Vector3=(0,1.5,0)
---@name 出生点偏移
```

#### List<T>

```lua
---@var RewardItems:List<string>={"coin","gem"}
---@name 奖励列表
```

#### UnityEngine.GameObject / UnityEngine.AudioClip

参数披露中的引用类型必须使用完整类型名，并显式声明默认值为 `nil`（写作 `=nil`），不能省略或填写 URI、路径、空字符串。GameObject 可引用模型或 WPrefab，AudioClip 引用 MP3/WAV。具体参数披露与示例见[特效指南](../resources/effect.md#参数披露)或[音频指南](../resources/audio.md#参数披露)。

`refFrom` 指定来源，`assetCategory` 指定资源分类，`dataType` 指定数据类型。资源 URI 写入[实例绑定参数](../editing/operations/script-management.md#资产引用参数)，Runtime 注入 GameObject 或 AudioClip；Lua 直接使用参数，不声明同名 `local`。

GameObject 引用场景实体时显式声明 `refFrom scene`；AudioClip 只支持资产来源。引用集合和 AnimationClip 参数暂不支持。

#### Dictionary<K,V>

当前 key 只支持 `int` / `string` 两种类型，int key 使用方括号写法，例如 `---@var Rewards:Dictionary<int,string>={[1]="coin",[2]="gem"}`。

```lua
---@var DropWeights:Dictionary<string,int>={coin=80,gem=20}
---@name 掉落权重
```

## Unity 命名空间

文件顶部按实际使用声明别名：

```lua
local UnityEngine = CS.UnityEngine
local Time = CS.UnityEngine.Time
local HandType = CS.HandType
```

规则：

- 使用 `UnityEngine.*`、`Time.*`、`HandType.*` 前，必须先有对应 `local` 声明。
- 如果没有声明别名，就必须写完整命名空间，例如 `CS.UnityEngine.Vector3(...)`、`CS.HandType.Right`。
- C# 类型（包括 `typeof(...)` 的参数）必须使用完整的 `CS.<命名空间>.<类型>` 或当前脚本中显式声明的局部别名。发现类型名与示例不一致时，回查对应示例确认，不凭记忆认定它是可用的全局变量。
- Unity 类型构造不使用 `new`，直接调用 `UnityEngine.Vector3(x, y, z)`、`UnityEngine.Quaternion.Euler(x, y, z)`、`UnityEngine.Matrix4x4.TRS(...)`。

## 生命周期与回调

常用生命周期：

- `Start()`
- `Update()`
- `FixedUpdate()`
- `LateUpdate()`
- `OnEnable()`
- `OnDisable()`
- `OnDestroy()`

常用交互回调：

- `OnFocus(handType)`
- `OnLostFocus(handType)`
- `OnInteractorButtonClick(index)`
- `OnPickup(actor, handType, pickUpPoint)`
- `OnDrop(actor)`
- `OnSeatEntered(actor, handType)`
- `OnSeatExited(actor)`
- `OnActorTriggerEnter(actor)`
- `OnActorTriggerExit(actor)`

扩展回调索引：

- 通用交互：`OnInteract(actor)`。
- 普通 trigger / player trigger：`OnTriggerEnter(c)`、`OnTriggerExit(c)`、`OnPlayerTriggerEnter(player)`、`OnPlayerTriggerExit(player)`。
- 碰撞：`OnCollisionEnter(c)`、`OnCollisionExit(c)`。
- 玩家 / Actor 生命周期：`OnPlayerJoined(player, evt)`、`OnPlayerLeft(player, evt)`、`OnActorSpawned(actor)`、`OnActorDespawned(actor)`。
- 网络对象生命周期：`OnNetSpawned()`、`OnNetDestroy()`。

回调规则：

- actor 回调修改本地 UI、按钮或仅作用于本地玩家的状态时，先判断 `actor and actor.isLocal`；拾取与座位确认回调是否全端执行，以所选 Hamlet 实现为准，不统一套用本地 guard。
- 成对事件尽量成对实现，例如 trigger enter / exit、focus / lost focus。

## API 调用

平台能力按 [Hamlet API 索引](../../hamlet-skill/references/api-reference-index.md)定位并读取实际使用的属性、方法或回调文档，核对类型、参数、坐标空间和限制。涉及 Unity/C# 原生类型或 Lua 底层接口时，核对 [API 白名单](../../hamlet-skill/references/api-whitelist.md)和 [API 黑名单](../../hamlet-skill/references/api-blacklist.md)。

读取或修改玩家、精灵属性时，从 [DouyinActor API](../../hamlet-skill/references/api-reference/DouyinActor.md)进入对应字段页。Actor、脚本挂载对象和相机是不同对象：

- `position` 是 Actor 的世界位置，但文档未指定脚底或身体中心；需要精确接触点时核对相应能力，不自行加减半个身高。
- `rotation` 是世界旋转，`velocity` 描述运动速度；运动方向不能直接代替面向。文档未提供 `actor.transform`，也未保证关联 GameObject 的 `transform.forward` 等同于玩法要求的朝向，不按 Unity 使用习惯补写这些关系。
- 投掷或射线需要方向向量时，确认玩法要求的是 Actor 朝向还是相机瞄准方向，再读取对应接口和经过验证的转换方式；Actor 属性表不提供相机方向。

- 静态方法用 `.`，实例方法用 `:`。
- `self:*` 表示平台注入的当前宿主实例方法，只能调用，不要自行实现同名函数或 `function self:*`。
- `Start()`、`Update()`、`OnFocus()`、`OnInteractorButtonClick(index)` 这类生命周期 / 平台事件才写成顶层回调函数，由平台调用。

### Lua 组件类型参数

`CS.<命名空间>.<类型>` 是 Lua 中的 C# 类型表；将它赋给局部别名不会转换类型。`GetComponent`、`GetComponentInChildren`、`GetComponentsInChildren` 等组件 API 的 `System.Type` 参数必须传入 `typeof(...)` 的结果，允许调用的 `AddComponent` 重载也遵守此规则。

```lua
local Button = CS.UnityEngine.UI.Button -- C# 类型表，不能直接作为组件查询的类型参数
local ButtonType = typeof(Button) -- 转换后的 System.Type，可缓存并直接传入
local button = gameObject:GetComponent(ButtonType)
local animator = modelRoot:GetComponent(typeof(CS.ModularAnim.Runtime.UGCAnimator))
```

接收组件类型的辅助函数同样必须使用转换后的 `System.Type`。检查 `GetComponent(componentType)` 等调用时，追踪变量的赋值来源；变量名带 `Type` 或用 `pcall` 取得类型表都不代表已转换。已由 `typeof(...)` 转换的值直接使用，不再次转换，也不通过 `CS.System.Type` 或反射取得类型。

## 日志

需要输出日志时，按 [Logger API](references/official-api/core/logger.md) 加载 `official.core.logger`，并在当前脚本创建一个 local logger。模型实例、Runtime UI 和预制体协调脚本的 Lua 不直接调用 `print` 或 `UnityEngine.Debug`。

- tag 使用固定、简短的脚本名或功能名，不使用用户输入或节点名称。
- `Update()`、`FixedUpdate()`、循环和高频回调只在状态变化时输出；重复失败使用 `logger:warnOnce(key, ...)`。

## Transform 与值类型

- 访问普通节点、组件和外部回调参数前先检查 `nil`；找不到可选节点时跳过当前操作，不要让整个脚本报错。跨脚本调用的节点和脚本 ID 已经确定时，按下一节精确调用，不用遍历根节点或尝试多条路径来掩盖挂载错误。
- `transform.position` 是世界坐标；`transform.localPosition` 只相对于直接父节点。scene 的实例位置会作为层级内的局部变换应用，最终 WPrefab 可以被放置、旋转或缩放到任意世界位置，不得假定 Placement 坐标等于运行时世界坐标。
- 需求和设计中的方向、相对位置、邻接或包含关系只描述预期布局，不隐含具体坐标轴、正负方向、参考原点或数值范围。Lua 依赖最终模型的空间布局时，先按 [GLB 空间信息与 Unity 坐标](references/spatial/glb-unity-coordinates.md) 检查相关节点并完成坐标转换；检查前不得把空间语义写成具体坐标条件。
- 任务输入中的空间数值没有隐含坐标系。使用位置、边界或距离前，必须在当前脚本中明确参考 Transform、坐标空间和单位。`transform.position` 是世界坐标，与 Placement 坐标或其它局部坐标阈值不在同一坐标系，禁止直接比较其分量；必须先将位置和阈值转换到同一坐标系再比较。
- 空间规则优先使用相对于明确参考 Transform 的局部坐标，或从起点沿明确方向计算的相对距离。把世界坐标与局部坐标互相转换时使用：

```lua
-- 世界坐标转换到 referenceTransform 的局部坐标。
local localPoint = referenceTransform:InverseTransformPoint(worldPoint)

-- referenceTransform 的局部坐标转换到世界坐标。
local worldPoint = referenceTransform:TransformPoint(localPoint)
```

- `TransformPoint` 和 `InverseTransformPoint` 只用于位置点。转换方向时使用 `TransformDirection` 或 `InverseTransformDirection`，不要用位置转换 API 处理方向。
- 修改位置、旋转、缩放时，显式构造新值并写回：

```lua
local pos = wheel.localPosition
wheel.localPosition = UnityEngine.Vector3(pos.x, pos.y + 0.1, pos.z)
wheel.localEulerAngles = UnityEngine.Vector3(0, angleDeg, 0)
```

- Unity 值类型运算使用当前 XLua 运行时已验证的写法，不根据 C# 运算符方法名推断 Lua 中存在同名 API。
- `Vector3` 加减和标量缩放可取 `x/y/z` 分量计算后重新构造；保留已验证模板中的运算写法，不为兼容性猜测批量改写。
- 当前 XLua 运行时的 `Matrix4x4` 和 `Quaternion` 乘法使用 `*`，不可替换为 `Matrix4x4.op_Multiply(...)` 或 `Quaternion.op_Multiply(...)`。

## 官方 ModuleScript 与 `require`

`require` 只用于加载工作区根目录 `official/` 中实际存在的官方 ModuleScript。使用下表已文档化的模块时，读取对应 API 页；任务命中其它按需场景时，再读取该场景的 reference。不需要读取模块实现，只调用当前已读取文档明确列出的接口。

- 模块名相对工作区根目录省略 `.lua`，并把 `/` 替换为 `.`。例如 `official/core/logger.lua` 使用 `require("official.core.logger")`。
- 只使用静态字符串字面量 `require("official.<module>")`。AI 暂不自行创建 ModuleScript，也不加载自定义模块。不要使用变量、字符串拼接、别名或其它动态方式决定模块名。
- `official/**` 只能读取或搜索。禁止新增、修改、重命名、移动或删除其中的任何内容，对应文件不存在时，不要使用该模块，也不得创建同名文件来通过归档检查。
- 普通脚本定义通过 `scripts.bind` 挂到 GameObject 运行，不能作为 `require` 目标；同一作用域内的脚本调用使用 `runtimeScope:GetScript(scriptId)`。

## 脚本拆分与同资源调用

同一作用域内的模型实例脚本、Runtime UI 脚本和预制体协调脚本，可以通过已保存的 `runtimeScope:GetScript(scriptId)` 查询同一脚本树中的其它 DouyinScript。它不会跨作用域查找其它模型实例的脚本。

共同规则：

- `scriptId` 使用目标脚本的查询名称 `referenceName`。取得名称、区分 SDK handle 与源码路径，以及选择查询范围，见 [RuntimeScope 的脚本查询名称](references/official-api/core/runtime-scope.md#脚本查询名称)。
- 每个需要当前资源 Scope 的脚本都在 Lua chunk 顶层调用一次 `RuntimeScope.from(self)`；生命周期、回调和局部函数只复用该 scope。
- 供其它脚本调用的函数声明为当前脚本顶层的非 `local` 函数，并通过返回的 script table 使用 `.` 调用。只在当前文件内部使用的状态和函数保持 `local`。
- 需要把当前脚本的方法交给其它脚本回调时，在方法声明且所需状态初始化完成后，显式构造 Lua 接口表，例如 `{ PlayAction = PlayAction, GetState = GetState }`，按双方约定传递。禁止用 `RegisterNpc(self)`、`RegisterUi(self)` 代替接口表；接收方不能从 C# 组件上读取这些 Lua 函数。平台 API 明确接收 Component 或 GameObject 时，仍按其签名传 `self` 或 `self.gameObject`，不把接口表代替平台对象。

独立 helper 只在职责需要时增加，生命周期、listener 注册与清理保留在明确入口。

Runtime UI 与预制体协调脚本查询 root-bound helper 的写法相同：

```lua
local RuntimeScope = require("official.core.runtime_scope")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local function resetState()
  if runtimeScope == nil then return false end
  local state = runtimeScope:GetScript("helpers_state.lua")
  if state == nil or type(state.Reset) ~= "function" then return false end
  state.Reset()
  return true
end
```

简单按钮与动画可放在同一脚本，多脚本同节点时同一操作只能有一个请求发起者。跨脚本通过明确的顶层方法传递状态，不依赖不同 Start 的执行顺序或读取另一脚本的 local 状态。

挂载节点按[实例层级与脚本挂载约定](../SKILL.md#实例装配的层级关系)选择，使用 scene 查询或创建返回的真实 handle；`scriptId` 与绑定节点分开维护，不从目录推导节点。

## 跨资源调用

同一作用域的脚本使用 GetScript。需要多实例共享状态或统一协调时，按 [Runtime Host 协作](references/runtime-host/coordination.md)确定参与实例、公共方法、事件、共享状态及失败行为，再建立作用域和保存脚本。

跨作用域调用须先按[创建与核对作用域](references/runtime-host/coordination.md#创建与核对作用域)确认 Host 与参与实例的层级，再通过 `GetRuntimeHostScript` 调用已实现的接口。缺少所需能力或接口时报告缺失，不用 `GetScript` 代替跨实例调用，也不把跳过功能当作玩法已实现。

需要登记实例、按目标分发事件或统计状态时，使用[通用 Host 模板用法](references/runtime-host/coordination.md#使用通用模板)；规则型投篮使用[概率投篮模板](references/runtime-host/probability-basketball.md)。这些玩法方法由协调脚本提供，声明 Host 不会自动生成它们。

## 最小脚本骨架

```lua
-- 控制模型实例的局部运动或交互行为
---@displayName 旋转控制
---@start
---@var RotationSpeed:number=30
---@name 旋转速度
---@desc 脚本挂载对象每秒绕 Y 轴旋转的角度
---@group 运动
---@end

local UnityEngine = CS.UnityEngine
local Time = CS.UnityEngine.Time

-- target 缓存脚本挂载对象的 Transform；elapsed 用于演示 Update 中的持续状态。
local target = nil
local elapsed = 0

function Start()
  -- Start 中初始化引用，后续 Update 只使用已缓存的 Transform。
  target = self.transform
end

function Update()
  -- 每帧先做 nil guard，避免脚本挂载对象异常时整段行为崩掉。
  if target == nil then return end
  elapsed = elapsed + Time.deltaTime
  target.localEulerAngles = UnityEngine.Vector3(0, elapsed * RotationSpeed, 0)
end
```

## 硬约束

- 不访问 `window`、`document`、DOM、`requestAnimationFrame`。
- 不写编辑器 UI、导入器、构建脚本、Node.js 脚本或后端逻辑。
- 不自行增加排行榜、DataStore、胜负结算等整套系统。只有当前目标确实需要，并且相关接口已经明确可用时再实现。
- 不返回 table，不写 `return M` / `return { ... }`。
- `require` 只使用实际存在的 `official.*` 模块；不创建或加载自定义 ModuleScript，不 require 普通已绑定脚本、私有 alias 或其它搜索路径。
- 需要当前资源 Scope 时，必须在 Lua chunk 顶层、首个函数定义之前调用一次 `RuntimeScope.from(self)` 并保存返回的 scope。`Start()`、回调与辅助函数只能复用该 scope，不得再次调用 `RuntimeScope.from(self)`。模块级 `RuntimeScope.resolveResourceRoot(value)` 可在命中回调中直接调用，不要求创建当前 scope。
- 当前资源脚本与节点通过 [RuntimeScope API](references/official-api/core/runtime-scope.md) 访问：`GetScript(scriptId)` 取得脚本；`GetTransformByPath` / `GetGameObjectByPath` 接受当前实例的完整后代路径；`GetResourceRoot()` 取得资源根。

碰撞、接近或穿越目标参与玩法结果时，先读 [运动与命中检测](references/spatial/movement-hit-detection.md)，确认位移方式与命中检测匹配。

## 按需读取

以下参考各自说明实际操作或 API，按当前任务选择；平台 API 直接读取 Hamlet 中的对应文档。

| 场景 | 读取 |
| --- | --- |
| 读取或修改玩家、精灵的位置、朝向、速度等属性 | [Hamlet DouyinActor API](../../hamlet-skill/references/api-reference/DouyinActor.md) |
| 多个实例共享状态、统一处理事件或结果 | [Runtime Host 协作](references/runtime-host/coordination.md) |
| 运行时改颜色、自发光或恢复材质 | [材质颜色](references/material-colors.md) |
| 运动物体通过碰撞、接近或穿越目标产生结果 | [运动与命中检测](references/spatial/movement-hit-detection.md) |
| 为模型或普通行为节点选择 NetSpawn、ObjectSync，配置网络源与各端生命周期 | [GameObject 网络指南](references/gameobject-networking.md) |
| 本地或联网动态创建 GameObject，声明网络源，或统一销毁生成实例 | [Spawn API](references/official-api/core/spawn.md) |
| Lua 依赖最终 GLB 中节点的位置、方向、边界或空间区域 | [GLB 空间信息与 Unity 坐标](references/spatial/glb-unity-coordinates.md) |
| 输出普通日志、warning、error，或对重复 warning 去重 | [Logger API](references/official-api/core/logger.md) |
| 查询当前作用域或预制体协调脚本、取得根 GameObject | [RuntimeScope API](references/official-api/core/runtime-scope.md) |
| 判断一个 Collider 层级的包围范围是否完全位于另一个 Collider 层级的局部包围范围内 | [Containment API](references/official-api/geometry/containment.md) |
| 当前模型实例节点具有已保存 Trigger 组件，需要披露或读取触发范围 | [Trigger API](references/official-api/interaction/trigger.md) |
| 通过 GameObject 引用播放特效 | [Effect API](references/official-api/effect/playback.md) |
| Runtime UI 需要 tween 动画 | [Animation API](references/official-api/ui/animation.md) |

