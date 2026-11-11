# UI 视觉资产

本文维护 Runtime UI 视觉资产的选择、生成和组合方式；HTML 图片节点的 `data-u-name` 与 `src` 契约见 [UI HTML](./ui-html.md#图片引用)。

## 选择资产格式

根据视觉语义选择 PNG、SVG 或纯 HTML，不为每个按钮机械添加图片。

### 使用 PNG

- 具有明确视觉特征的复杂静态图标使用 PNG，例如武器、装备、技能、道具、货币、宝石、药水、钥匙、宝箱、任务物、角色头像、阵营、敌人、地图地标、成就、元素状态、增益、减益、稀有度和奖励。
- 选择列表、快捷栏、背包格、技能栏、奖励列表、任务列表和地图标记中的不同语义项分别使用独立图标，不用纯文字或统一占位图替代。
- 核心操作按钮需要具象图标时，只有图标使用 PNG；按钮底板、描边、发光、按下态和点击区域使用 SVG 或 HTML 节点表达。
- PNG 生成或裁切失败时可以降级为 SVG，并在完成说明中列出资产名和原因。

### 使用 SVG

- 圆角面板、按钮皮肤、规则槽位、徽章底板、状态条外框、可拉伸底板和简单几何视觉使用 SVG。
- 生命、能量、护盾、冷却、进度和倒计时等运行时变化的状态层使用 SVG 或 HTML 节点，不使用 PNG 图集。
- 需要按 HTML 节点尺寸稳定拉伸、保持锐利边缘或控制裁切时，优先使用 SVG。
- SVG 不替代具有明确外观差异的复杂静态图标。
- 超过 12 个具象语义图标时属于 PNG atlas 的容量路由例外：每个图标仍需独立、无文字且保持可区分的语义外观，不能合并或用统一占位图代替。

### 使用纯 HTML

- 确认、取消、返回、关闭、重置、继续和开始等通用命令可以使用文字、背景色和独立点击区域，不要求 PNG 或 SVG。
- 状态标签、轻量提示和普通列表项在图片只会重复文字或增加噪音时不添加图片。
- 武器、技能、道具、货币、角色、敌人、地标、状态和奖励不适用上述豁免。

## 组合按钮与图片

- button 负责点击区域，skin 负责底板，icon 负责语义图标，label 负责文字；四种职责使用独立节点表达。
- 图片不能遮挡按钮的实际点击区域，也不能挤压或覆盖文字。节点层级和局部坐标按 UI HTML 的坐标规则编写。
- label 位于槽位外时，icon 在整个槽位内居中。
- label 位于按钮内时，将按钮划分为 `iconViewport` 和 `labelArea`，icon 只在 `iconViewport` 内居中。
- icon 的位置按 `left = viewportLeft + (viewportWidth - iconWidth) / 2`、`top = viewportTop + (viewportHeight - iconHeight) / 2` 计算。同组槽位使用相同视口尺寸，图标尺寸可以按长宽比调整。

## 生成 PNG 图集

- 新增具象语义图标且没有可复用的真实业务图片时，先按最终去重数量路由：1–12 个调用一次 `generate-ui-png-atlas.mjs`，单个图标也调用；超过 12 个时整组编写独立 SVG，并记录 `png-atlas-count-exceeded: N > 12`，不得调用图片生成工具。
- 每次调用显式传 prefabId 选择预制体根，再用 resourceId 选择其中的 UI 资源目录；具体参数见下方命令说明。调用前先确定最终 HTML 中确实显示的 image 节点，并让 `assetNames` 与这些节点一一同名；不生成备用图片。成功后立即为对应节点显式填写 `src="../images/<assetName>.png"`。
- 尺寸、目标槽位和美术风格兼容的图标可以合并进同一次 atlas；头像、物品、地图标记等视觉体系或长宽比差异明显时拆成多次调用。语义相近只作为分组建议，不作为是否生图的前置条件。
- 图集只包含复杂静态图标，不包含面板、按钮皮肤、槽位底板、状态条外框或填充、冷却遮罩、进度层和其他可拉伸几何资产。
- 生成提示必须要求透明背景或纯色可抠背景，并明确无文字、无数字、无水印、无完整 UI 截图背景。单图提示只描述一个孤立资产；图集提示只包含可裁切的同类图标。
- 工具会按本次实际行列数自动生成纯白、浅灰细线、等大正方形格子的布局参考图并作为图片输入；不得另行指定固定 5×4 参考图，也不要要求模型照抄参考图中的内容。
- 裁切后的 PNG 使用透明背景，边缘不保留大面积空白，长宽比与目标 image 节点接近。
- 每个裁切结果对应一个 image 节点。
- 若误把超过 12 个资产传给 `generate-ui-png-atlas.mjs`，只能在 receipt 同时包含 `outcome=fallback`、`errorCode=UI_PNG_ATLAS_ASSET_LIMIT_EXCEEDED`、`fallbackMode=svg` 和 `imageRequestIssued=false` 时按容量路由继续；其它失败仍是生图失败，不能静默伪装成 SVG 路由。

### 命令与参数

先准备目标 UI 资源目录并确定要显示的图标名，然后从工作区根运行：

```bash
node "<skill-local>/ui/scripts/generate-ui-png-atlas.mjs" \
  --config '{"prefabId":"village","resourceId":"ui-hud","prompt":"统一低多边形游戏图标：金币和钥匙，正面视角，无文字、数字或水印","assetNames":["coinIcon","keyIcon"]}'
```

| 参数 | 要求 |
| --- | --- |
| `prefabId`、`resourceId` | 必填，当前预制体及 `ui-*` 资源目录 |
| `prompt` | 必填，非空的静态外观与美术方向；说明每个图标的具体语义，不生成完整 UI 截图 |
| `assetNames` | 必填，互不重复的图片名，使用字母/数字开头及字母、数字、下划线、连字符；正常生成 1–12 项 |
| `atlasName` | 可选，原始图文件名，不含扩展名，命名格式同 `assetNames`，默认 `uiAtlas` |
| `columns` | 可选，1–5 的整数；省略时按数量自动确定列数 |
| `postprocessMode` | 可选，默认 `preserve-model`，保留外观并裁边去背景；`procedural-normalize` 会重绘成简化 UI 皮肤 |
| `timeout` | 可选，等待图片请求的秒数，最小 1，默认 360；设置 shell 超时时预留后处理时间 |

成功返回 `outcome:"completed"`、`image_paths`、`raw_atlas_output_path`、`layout_reference_path`、行列数和 `postprocess`。裁切图位于资源 `images/<name>.png`，原图与网格参考位于 `.png-atlas-work/`。查看裁切图后更新 HTML 图片引用，再运行 UI 检查；命令不会自动修改 HTML 或准备 UI GLB。

同一 UI 资源内重复使用 `assetNames` 会覆盖同名裁切图；重复使用 `atlasName` 会覆盖 `.png-atlas-work/<atlasName>.raw.png` 与 `<atlasName>.layout-reference.png`。生成期间还会写入 `images/<atlasName>.png`，成功后若它不是本次裁切图则删除。调用前核对这些名称；保留原图时使用新名称，`atlasName` 不要占用需要保留的图片名。

接口允许 13–20 项以返回明确的容量分流回执，但不发起图片请求；按前述规则整组改用 SVG，退出码为 0。真实生图或后处理失败返回 `outcome:"failed"` 或错误诊断并退出非零，不能当作容量分流。

图片逐个写入，失败或取消后已覆盖文件不会自动恢复。检查本次 `assetNames` 对应图片、`images/<atlasName>.png` 及图集工作文件，报告已写入或覆盖的内容和未完成项。收到取消后停止操作，不把部分图片当作完整成功结果。

## 编写 SVG

SVG 可以使用：

- 静态 `<svg>`；
- 基础 shape、`path`、`linearGradient`、`radialGradient`；
- 内联 `fill`、`stroke`、`opacity` 等静态属性。

SVG 禁止使用：

- `<script>` 和任意 `on*` 事件属性；
- `foreignObject`；
- `<text>` 和 `<tspan>`；
- `<line>` 和 `<polyline>`；
- 远程 `<image>`、远程 CSS、远程字体、`url(http...)` 和 `javascript:` URL。

设计要求：

- SVG 视口与目标 image 节点尺寸匹配或可等比缩放。
- 描边、阴影和发光向内预留 4–8px，或扩大 viewBox，避免边缘被裁切。
- 面板底板不添加没有业务含义的装饰线或分割线。需要刻度、路线或轴线时，使用 `path` 绘制在独立 image 节点中，并避开文字区域。
- SVG 只包含当前图片的静态视觉，不包含完整 HTML、业务脚本或调试信息。
