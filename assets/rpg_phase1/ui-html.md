# UI HTML

本文维护 Runtime UI 的 HTML 结构、布局、控件字段、图片引用和归档检查。PNG、SVG 和纯 HTML 的选择由 [UI 视觉资产](./ui-assets.md) 维护。

## 阅读顺序

1. 按 [官方 UI 参考与避让](#官方-ui-参考与避让)确定可用区域。
2. 按 [HTML DSL](#html-dsl)编写结构、控件和样式。
3. 按 [坐标与归档检查](#坐标与归档检查)完成自查。

## 官方 UI 参考与避让

- 模板中的 `nativeTopLeftProtectedArea`、`nativeMoreWorldProtectedArea` 和 `nativeRightSystemProtectedArea` 不可被 Runtime UI 覆盖或复刻。
- `nativeMoveJoystickArea` 及其说明区域默认保留。只有需求明确使用自定义摇杆或由底层玩法接管移动输入时，才将 `UIType.MoveJoyStick` 记为待隐藏控件。
- `hideableRightActionArea`、`nativeChatPanelArea` 及其说明区域属于高冲突区。无法避让时，记录发生冲突的官方控件和原因，由 UI Lua 执行最小范围的临时隐藏与恢复。
- 普通 HUD、驾驶状态、计分、金币、速度、任务提示和常驻重置按钮只能放在模板剩余的非交叠区域。
- 普通 HUD、车控和状态面板不得覆盖聊天区。只有全屏面板、文本输入面板或明确替代聊天输入的界面可以占用该区域。

### 大型面板

- 背包、装备、商店、技能树、地图、任务日志、武器库、设置页和排行榜详情默认只展示入口按钮、状态胶囊或小图标。
- HTML 使用两个稳定节点：`<feature>EntryBtn` 或 `<feature>EntryRoot` 作为入口，`<feature>PanelRoot` 作为完整面板。面板使用展开后的最终坐标，内部节点使用局部坐标，并包含明确的关闭按钮。
- 不使用负坐标、超大透明遮罩、`alpha=0` 或屏幕外坐标表达折叠状态。面板的初始隐藏和打开关闭逻辑由 UI Lua 维护。
- 必须开局展示大型面板时，说明原因并提供关闭入口。

## HTML DSL

### HTML 边界

- 所有节点必须声明 `data-u-name` 和合法的 `data-u-type`。
- 根节点必须是 `data-u-type="div"`，且 `data-u-name` 等于该 UI 的 canonical 语义身份。新建时等于 `<resourceId>`，例如 `ui-aircraft-controls` 对应 `data-u-name="ui-aircraft-controls"`；复制或恢复到其它存储目录时，保留原 `meta.resourceId`、bundle/runtimeUI 身份和 HTML 根名，不按新目录名重命名。
- 横屏根尺寸固定为 `width: 1920px; height: 1080px;`，竖屏根尺寸固定为 `width: 1170px; height: 2532px;`。横竖屏可以使用不同布局，但对应同一交互的关键节点保持相同名称。
- 根节点必须显式声明 `background-color: rgba(0, 0, 0, 0);`。面板、蒙层和 HUD 底板使用独立子节点，只覆盖需要的区域。

### 命名

- HTML 节点和图片资产使用 lowerCamelCase，例如 `takeoffActionBtn`。
- `data-u-name` 在同一 UI resource 内全局唯一。除根节点外，每个名称会成为 UGUI GameObject 名和 Lua 节点路径的一段。

### 节点类型

`data-u-type` 只接受：

- `div`
- `image`
- `text`
- `button`
- `input`
- `scroll`
- `toggle`
- `slider`
- `dropdown`

面板、卡片和容器使用 `div`，不使用 `panel`。

需要绑定点击事件的区域必须写成 `<div data-u-type="button" data-u-name="...">`。HTML 标签使用 `<div>`，但 `data-u-type` 必须是 `button`；`data-u-type="div"` 只生成容器，不会因为名称含 `Button` / `Btn`、外观像按钮或包含按钮文案而生成 Button 组件。不要使用原生 `<button>`，避免浏览器默认 border、padding 和 appearance 污染预览。

### 图片引用

- 每个 `image` 节点都必须显式填写 `src`，只接受 `../images/<safe-name>.png` 或 `../images/<safe-name>.svg`；不要省略或留空。多个节点可以引用同一文件；归档后的图片键仍是各节点自己的 `data-u-name`。
- `images/` 中未被任何图片节点引用的安全 PNG/SVG 不进入 GLB，也不阻断归档；同一被引用的基础文件名不能同时提供 PNG 和 SVG。
- 横竖屏中同名图片节点必须使用同一 `src`。

### Canvas 和节点层级

- 根节点 `z-index` 映射为 Canvas `sortingOrder`。允许 `1..999`（官方主界面之上）或 `-999..-11`（官方界面之下）；`-10..0` 为官方 UI 保留区。省略时不写入该字段。
- 子节点 `z-index` 只控制同一父节点内的顺序：数值较大的节点后渲染；未声明时按 `0` 处理；相同值保持 HTML 原顺序。

### 自动布局

- 需要 Unity LayoutGroup 时，在容器上声明 `data-u-layout="h|v|grid"`，不同时声明 `display:flex` 或 `display:grid`。
- 布局容器可以使用 `padding`、`gap`、`row-gap`、`column-gap`、`justify-content`、`align-items`、`align-content` 和 `flex-direction`。
- grid 可以用正数 `data-u-columns` 指定列数。未显式提供单元格尺寸时，首个子节点的 `width` 和 `height` 作为单元格尺寸，因此同组单元格应保持一致。
- 以上布局属性只对显式布局容器生效。`input` 的 `padding` 是非布局节点的唯一例外。

### Toggle、Input 和 Scroll

- Toggle：`checked` 或 `data-u-checked="true"` 设置初始选中；`data-u-group="<safe-id>"` 设置组名。任意容器可以用 `data-u-toggle-group="<safe-id>"` 声明 ToggleGroup。
- ToggleGroup 标识只允许字母、数字、下划线和连字符，并且必须以字母或数字开头。
- Input：`<input data-u-type="input">` 支持 `placeholder`、`value`、`type` 和 `padding`；`<textarea data-u-type="input">` 或 `data-u-multiline="true"` 生成多行输入。
- Input `type` 可用 `password`、`email`、`number`、`decimal`、`integer`、`int`、`range`、`tel`、`pin`、`name`、`alphanumeric`、`autocorrected`、`search` 或 `custom`；其他值按普通文本输入处理。
- Scroll：`overflow-x` 或 `overflow-y` 的值为 `scroll` 或 `auto`。两者均未声明时，使用 `data-u-dir="h|v|hv"`。`data-u-content-layout="h|v|grid"` 设置 Content 布局；grid 可以用正数 `data-u-content-columns` 指定列数。

### 富文本

- `text` 和 `button` 的内联 `<b>/<strong>`、`<i>/<em>`、`<u>/<ins>`、`<s>/<del>` 与 `<br>` 会合并到同一个 TMP 文本节点，不生成额外 UGUI 节点；`button` 内显式声明的 `image` 等 Runtime UI 节点仍会独立归档。
- 内联 `font-weight`、`font-style`、`text-decoration`、`color` 和数值 `font-size` 会转换为对应 TMP 标记。其他 HTML 标签不提供布局能力。
- 富文本仍受节点矩形和文字安全区约束，不依赖浏览器换行或嵌套元素定位。

### Slider

- 可拖动数值控件使用原生 `data-u-type="slider"` 节点，不使用 `div`、`image` 或 SVG 拼接滑条。
- slider 必须有正数 `width` 和 `height`，并声明 `min`、`max`、`value`。可选字段为 `step`、`data-u-direction`（`left-to-right`、`right-to-left`、`bottom-to-top`、`top-to-bottom`）和 `data-u-whole-numbers="true|false"`。
- `max` 必须大于 `min`，`value` 必须在区间内，`step` 必须大于 `0`。未声明 `data-u-whole-numbers` 时，整数 `step` 自动启用整数值，其余情况关闭。
- 轨道、填充和手柄由 Unity Slider 表达。外观图片和文字不得覆盖实际拖动区域；当前值、单位和刻度使用独立 `text` 节点。
- Slider 事件由 UI Lua 绑定。

### 样式与禁止项

- 使用静态结构和内联 style。`left`、`top`、`width`、`height`、`font-size` 使用 `px` 或无单位数字。
- 优先使用绝对尺寸、位置、颜色、字号和层级；横竖屏分别维护，不依赖浏览器响应式布局。
- 文案保持简短。`text` 节点的 `height` 必须容纳真实行高：英文和数字至少为 `font-size * 1.25`，中文或粗体至少为 `font-size * 1.35`。
- 禁止 `<script>`、`<style>`、`iframe`、内联事件属性、远程 CSS、远程图片、外链字体、`javascript:` URL 和依赖脚本生成的动态节点。
- 禁止 `border`、`border-radius` 及其分方向属性。需要边框或圆角时使用图片底板，格式按 UI 视觉资产选择。
- 除[自动布局](#自动布局)声明的字段外，禁止 `display:flex`、`display:grid`、margin、right、bottom、transform、其他 flex/grid 属性、百分比、`calc()`、`var()` 和 media query。

## 坐标与归档检查

### 坐标

- 根节点的直接子节点使用画布坐标；嵌套子节点的 `left/top` 以直接父节点左上角为原点。
- 例如按钮位于 `left:754px;top:240px;width:178px;height:102px` 时，内部 skin 从 `left:0px;top:0px` 开始，icon 和 label 也使用按钮范围内的局部坐标。
- 复杂面板只选择一种坐标策略：所有可见节点直接挂根节点并使用全局坐标，或由外层 panel、column、slot 承担全局坐标且内部全部使用局部坐标。优先使用后者。
- 除根节点外，每个节点应满足 `0 <= left/top`、`left + width <= parent.width`、`top + height <= parent.height`。需要更多空间时扩大父容器或改为根级叠层。

### 归档布局检查

- 归档器会拒绝可确定的文字与带文案按钮相交、外层文字与深层文字相交、`*Icon` 图片覆盖居中按钮文案，以及文字跨出同级 `*Skin` 图片边界。错误会指出节点、相交尺寸和调整方向。
- 底板覆盖、空文案按钮热区、完全落在按钮内的标签、小型角标，以及分别位于同级互斥页面中的节点属于允许叠层。
- 参与检查的语义图片分别使用 `Icon`、`Skin` 后缀；允许叠层按上一条所列结构表达。

### 圆角与文字安全区

- 圆角面板、卡片、徽章、按钮底板、状态条外框、技能槽和提示条使用 `image` 图片底板。
- 内容节点位于底板之后或使用更高的 `z-index`。可见文字使用独立 `text` 节点，不画入 PNG 或 SVG。
- 文字矩形必须位于底板或边框的内容区内，四边至少内缩 12px；描边不小于 3px、存在发光或内阴影，或字号大于 28px 时，至少内缩 16px。
- 同一面板中的多行文字先划分固定行区域，行间距至少 8px。
- toast、hint 和 cooldown 文案必须完整位于面板内容区内，或完整位于面板外并与边框至少间隔 8px。
- 进度刻度、地图路线和其他有业务含义的线性视觉使用独立 image 节点，与文字矩形至少间隔 12px。
- 文字无法放入安全区时，优先扩大底板、按钮或面板，其次减少内容或降低字号。
