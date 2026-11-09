# 龙眠之境 · 交接文档

抖音「造世界编辑器」比赛作品。暗黑奇幻风的龙与守夜人世界，默认黑夜，有昼夜循环，主体是自由游玩。

- **世界观、故事、地名、UI 定调**：[docs/世界观与UI定调.md](docs/世界观与UI定调.md)
- **编辑器实测踩坑记录**：[docs/claude-memory/world-editor-pipeline.md](docs/claude-memory/world-editor-pipeline.md)，这份最重要
- **用户确认过的美术方向和历史反馈**：[docs/claude-memory/dragonrest-final-vision.md](docs/claude-memory/dragonrest-final-vision.md)

本文最后更新：2026-11-09。

---

## 1. 换电脑：拉下来就能用

只支持 macOS，编辑器只有 Mac 版。工具脚本也依赖 macOS 的路径和 `sed -i ''`。

1. 安装「造世界编辑器」，用**同一个抖音账号**登录。场景里的模型都是云端地址（`hamlet-ugc/...glb`），登录后编辑器会自动下载，所以本地缓存 `asset-cache`（约 900 MB）没有放进仓库。
2. 克隆仓库，建议放在 `~/Documents/awesomeWRLD`：
   ```bash
   git clone https://github.com/eiddiedev/DRAGON.git ~/Documents/awesomeWRLD
   ```
3. 如果用户名不是 `a1234`，或者仓库没放在上面的路径，运行一次路径修正：
   ```bash
   ~/Documents/awesomeWRLD/tools/fix_paths.sh
   ```
4. 先退出编辑器，或者停在首页，再把工程装进编辑器：
   ```bash
   ~/Documents/awesomeWRLD/tools/restore_project.sh
   ```
   会复制到 `~/Library/Application Support/AI World Creator/projects/project_lapv8fm0`。已有同名工程时会先自动改名备份。
5. 打开编辑器，在首页找到「我的项目」，点「去编辑」，第一次加载约 1 到 2 分钟。点「本地运行」能看到标题页「龙眠之境」，就说明装好了。
6. Python 工具需要 `python3`，以及这些包：
   ```bash
   pip3 install numpy pillow opencv-python-headless scipy fonttools lupa
   ```
   名字带「Blender --background」的脚本是早期的建模工具，要装 Blender，现在的主流程用不到。

**提交新改动前**，先让编辑器回到首页，保证存档已写盘，再把编辑器里的工程同步回仓库：
```bash
~/Documents/awesomeWRLD/tools/sync_from_editor.sh
```

---

## 2. 仓库结构

| 路径 | 内容 |
|---|---|
| `editor_project/project_lapv8fm0/` | **编辑器工程本体**。`scene.data` 是场景存档（zip，见第 4 节），`scripts/modules/world_main.lua` 是运行的脚本，`ai-sessions/` 是编辑器 AI 生成资产的会话记录 |
| `scripts/world_main_v5.lua` | **主脚本源码**，唯一的真源。`world_main.lua` 是它的副本，其余是旧版本 |
| `scripts/ui_v1.lua` | 界面模块源码（标题页、古书、地图、音效），由 `tools/ui/embed_ui.py` 嵌进主脚本 |
| `tools/install_lua5.py` | 把主脚本装进工程：`debug` 打开测试按键，`release` 关闭 |
| `tools/place_world6.py` | 当前的摆放脚本：读 `backups/scene.v6-before-fix.data` 作为底，重写所有摆放、地形贴图和高度 |
| `tools/terrain_native/` | 原生地形的高度、16 层贴图权重和覆盖色（`repaint.py`、`cover.py`），以及植物摆放（`plants_block.py`） |
| `tools/ui/` | 界面美术：`basemap.py` 画地图底稿，`make_ui.py` 生成全部 UI 贴图和 GLB，`embed_ui.py` 嵌入脚本 |
| `tools/models/` | 自制模型工具。`glbw.py` 是不依赖 Blender 的 GLB 写入器，支持蒙皮、动画和透明 |
| `tools/dragon/` | 暗影龙六段模型的烘焙和组装（`bake6.py`、`assemble6.py`） |
| `assets/` | 所有自制资产：GLB、贴图、地形数据、音乐、字体。`assets/ui/glb/ui_*.glb` 是界面贴图载体 |
| `assets/fonts/` | 开源字体：思源黑体 Heavy、思源宋体 Heavy、霞鹜文楷，均为 SIL OFL |
| `docs/` | 世界观、地图底稿、地点坐标 `docs/ui/poi.json`、记忆笔记 |
| `backups/` | 存档备份，仓库里只留最近三个，见第 6 节 |

---

## 3. 现在世界里有什么

**地形与环境**
- 原生地形 257×257，覆盖 256 米见方，使用编辑器的 16 层材质。
- 草地用光照压暗。默认黑夜，有昼夜循环，按时之晷切换。
- 天空是自制穹顶，加三层旋转漩涡和月亮。夜里漩涡带自发光，比之前明显。

**地点**（坐标见 `docs/ui/poi.json`）
- 晷石原：出生点和时之晷。
- 灯火村：房屋、雾港码头和三艘帆船，船可以登船出海。
- 女巫药铺、风车、守夜人营地（篝火和帐篷）、幽菇林、唤龙祭坛、萤光古树、薰衣草花海、孤灯塔、飞毯驿站。
- 龙眠堡：哥特城堡，内部有王座厅、书库、宴会厅、军械库、厨房、龙巢圣所、寝殿。
- 试炼场：城堡山体内的角斗场。
- 月桥、墨曜峰（暗影龙所在）。

**植物**：公共库的松树、灌木、青草、勿忘草、薰衣草、狼尾草，约 2200 个节点。

**玩法**
- 骑龙：在唤龙祭坛 20 米内按跳跃，被送上墨曜峰的龙背。摇杆控制飞行，再按跳跃降落，只能落在陆地上。落地后龙自己飞回山顶。
- 坐船、飞毯、夜里路灯自动亮起、篝火、蘑菇发光、城堡昼夜变色。

**界面**（2026-11-09 新做）
- 标题页、5 页序章古书、左上角地图（19 个可点地点）、7 种合成音效。
- 详见世界观文档的「实现状态」。

**测试按键**：只在 `install_lua5.py debug` 时有效。
- `1`~`7`、`o h j k l n , .` 等传送到各地点，坐标表在主脚本的 `TELEPORTS`。
- `0` 切换昼夜，`8` 量高度，`Tab` 开关地图。

---

## 4. 关键流程（必读）

### 4.1 改存档的唯一安全流程

工程开着的时候写 `scene.data`，会被编辑器覆盖。所以必须按这个顺序：

1. 编辑器里先「停止运行」。
2. 菜单「造世界编辑器 → 退出应用」，弹出「是否保存工程」时点「保存」。编辑器回到首页，工程关闭。没有改动时不会弹框。
3. 确认 `scene.data` 的修改时间是刚才，再用脚本写存档（摆放脚本、`install_lua5.py` 等）。
4. 回到首页，在「我的项目」上点「去编辑」重新打开，等 1 到 2 分钟。

`scene.data` 是一个 zip，里面有：
- `SerializePcgData.json`：节点、脚本、环境。
- `HeightMap_*.data`：257² 的 float，乘 256 得到米。
- `SplatMap_*_0..15.png`：16 层贴图权重，行序和高度图上下颠倒。
- `MatCoverTex_*.png`：2048 的俯视覆盖色。

### 4.2 改脚本

```bash
cd ~/Documents/awesomeWRLD
# 1. 改 scripts/world_main_v5.lua；如果改的是界面，改 scripts/ui_v1.lua 后运行：
python3 tools/ui/embed_ui.py
# 2. 检查语法和局部变量数（主块已经贴近 Lua 200 个局部变量的上限，超了整段脚本静默不运行）
python3 -c "from lupa import LuaRuntime;print(LuaRuntime().eval(\"function(s) local f,e=load(s) return e or 'ok' end\")(open('scripts/world_main_v5.lua').read()))"
# 3. 编辑器回到首页后安装（debug 或 release）
python3 tools/install_lua5.py debug
```

- 新增的状态一律放进表里（`DR`、`BT`、`HV`、`UI`），不要再加顶层 `local`。
- 调试日志用 `CS.UnityEngine.Debug.LogError`，写在 `~/Library/Logs/造世界编辑器/main.log`。`print` 看不到。
- **发布前务必装 `release`。**

### 4.3 导入自制模型

编辑器左下「资产库 → 我的 → 导入」。导入框需要的操作：
- **资产描述一定要手填一个词**，否则会走 AI 自动描述，又慢又容易卡死。
- 资产名不超过 15 个字。单个模型不超过 3 万面。
- 贴图会被压到 1024：带透明的存成无损 ARGB32，不透明的存成 ETC2。

导入后把资产拖进场景，节点名就是资产名，脚本里用 `GameObject.Find` 找。

### 4.4 界面怎么做的

- **贴图**：所有 UI 贴图由 `tools/ui/make_ui.py` 生成，每张做成一个 1 米的透明方片 GLB（`assets/ui/glb/ui_*.glb`），共 9 个，已导入并拖进场景。脚本启动时 `GameObject.Find` 找到这些节点，取材质的 `_BaseTex`，然后把节点隐藏。
- **画界面**：Lua 里直接建 `Canvas`（ScreenSpaceOverlay）、`CanvasScaler`（参考高 1080），用 `RawImage` 画图。点击用 `Input.GetMouseButtonDown(0)` 自己做命中判断，不依赖 EventSystem。
- **平台按钮**：`DouyinUIService.SetUIVisible(false)` / `SetNativeUIVisible(false)` 可以隐藏平台的摇杆和按钮。
- **标题页镜头**：另开一台相机，`CopyFrom` 主相机后盖在上面。点击后飞到主相机的位置，再销毁。
- **音效**：用 `AudioClip.Create` 加 `SetData(lua 表)` 在运行时合成。
- **改文案或美术**：改 `make_ui.py`，重新生成，然后**重新导入对应的 GLB**。贴图在云端，不重新导入不会生效。地图的地名位置在 `docs/ui/poi.json`。只改排版数据的话，跑 `embed_ui.py` 就够了。

### 4.5 摆放与地形

`python3 tools/place_world6.py` 以 `backups/scene.v6-before-fix.data` 为底，重写摆放、地形贴图和高度，然后写进工程存档。它会**覆盖**编辑器里手动做的改动，比如这次新导入的 9 个 `ui_*` 节点。要再跑它，必须先把底换成最新存档，或者把 `ui_` 节点加进保留列表。

---

## 5. 待办与路线图

**马上要做的**
1. 用「手机预览」检查界面：左上角地图按钮会不会被平台按钮挡住，字够不够大。
2. 城堡：用户会让 Codex 结合现在的城堡和编辑器 MIX 生成的城堡（`module-gothic-castle`，外观好但不够高峻）打磨。新城堡做好后替换 `gothic_*` 节点。
3. 资产换成新的工作流：Claude 写提示词，Codex 生图，Tripo 生成模型，再导入。要做的有：马（编辑器生成的两版都不行）、羊、更精细的龙、传送门、召唤阵、船、树。
4. 编辑器 Agent 生成的传送门 `module-magic-portal` 效果不错，还没摆进场景。位置是城堡脚下的「裂隙之门」(125,135)。

**玩法**（设定见世界观文档第二章）

主线是自由游玩加夜间自愿挑战。灯火照到的地方安全，灯火之外有影灵。
- **影灵**：夜里从裂隙之门出来，打散后掉落月辉。这是主玩法，第三人称战斗。
- **守夜灯**：附属的塔防，每人最多插 3 盏。
- **龙蛋孵化**：月辉、火种、星露三样凑齐结成龙契，之后才能在祭坛骑龙。现在骑龙不需要龙契。
- **篝火「烤蘑菇」**：按住烤，松手出锅，停在金色区间得到火种。
- **女巫怪药水**：变大、变小、变羊等。
- **职业誓约**：骑士、巫师、游侠。
- 角斗场双人对决、城堡各房间的玩法、地图的「探索点亮」。

**技术上还没验证**：生命值和伤害接口、怪物寻路、人物缩放和隐藏、多人同步、骑马坐姿。之前用 `actor:SitDown` 骑龙时，角色没有摆出坐姿。

---

## 6. 备份

- 仓库里只放三个最近的存档：
  - `backups/scene.v7-ui.data`：当前版本，含界面。
  - `backups/scene.v6-placed.data`：界面之前。
  - `backups/scene.v6-before-fix.data`：`place_world6.py` 的底。
- 更早的备份在原电脑的 `backups/` 里，没上传（`.gitignore` 排除了）。
- 恢复某个存档：编辑器回到首页后，复制到 `~/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data`。

---

## 7. 红线与约定

- **审核红线**：
  - 不出现十字形，包括墓碑、装饰、图标。
  - 不用第三方 IP。参考图只取气质，字体只用 OFL 开源字体，音乐必须原创。
  - 不出现血，影灵打散时化成光点。
- **不要替用户上传或发布世界**，也不要替用户点同意平台协议。
- **不要逆向编辑器**：不翻 app.asar。能看的公开资料只有 `/Applications/造世界编辑器.app/Contents/Resources/addon/lua-support` 下的 Meta 声明、snippets、Library。
- **背景音乐只能选官方曲目**，在编辑器底部的「音乐」面板选。自定义音频不能当背景音乐。
- 星光（编辑器 AI 生成的点数）用户已授权随便用，用后报告花费。
- 用户可能同时在编辑器里操作，自动化操作前先截图看一眼。
