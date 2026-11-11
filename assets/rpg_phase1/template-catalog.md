# Runtime UI 模板目录

本文统一维护 Runtime UI 模板的选择、应用、适配与清理。编写 HTML 前形成 `templateGate`，从下方三种模式中选择一种。

## 当前目录

| templateId | copyRoot | useCases | layoutSignature | visualLanguage |
| --- | --- | --- | --- | --- |
| `runtime-left-tab-horizontal-cards-popup` | `runtime/left_tab_horizontal_cards_popup` | popup、left-tabs、mail、tasks、rules、reward-detail | split-left-navigation、five-icon-description-tabs、right-message-content | warm-ivory、charcoal-header、muted-sand-navigation、gold-primary-action |
| `runtime-left-tab-item-grid-popup` | `runtime/left_tab_item_grid_popup` | popup、left-tabs、item-grid、inventory、collection | external-left-tabs、detached-header、6-column-2-row-wide-card-grid | warm-ivory、charcoal-header、muted-sand-grid、peach-icon-plates |
| `runtime-notification-popup` | `runtime/notification_popup` | notification、confirmation、warning、modal | centered-message-modal、detached-footer-actions | warm-ivory、charcoal-header、muted-sand-secondary-action |
| `runtime-split-detail-popup` | `runtime/split_detail_popup` | popup、left-tabs、split-detail、reward-choice、inspection | external-left-tabs、detached-header、4-column-detail-cards | warm-ivory、charcoal-header、muted-sand-content、peach-icon-plates |
| `runtime-three-panel-inventory-popup` | `runtime/three_panel_inventory_popup` | inventory、backpack、categories、item-grid、item-detail | external-left-tabs、5-column-scroll-grid、right-item-detail | warm-ivory、charcoal-header-and-grid、peach-slots、gold-primary-action |
| `runtime-top-tab-grid-popup` | `runtime/top_tab_grid_popup` | popup、top-tabs、item-grid、inventory、collection | top-tabs、6-column-scroll-grid、peek-next-row | warm-ivory、charcoal-header-and-actions、muted-sand-grid、peach-icon-plates |
| `runtime-vertical-action-list-popup` | `runtime/vertical_action_list_popup` | popup、ranking、leaderboard、player-list、vertical-actions | vertical-action-rows、peek-next-row | warm-ivory、charcoal-header-and-actions、muted-sand-list、rank-accent-colors |

## 选择顺序

1. 目标资源已有非空 HTML 时使用 `existing-source`，只修改当前需求涉及的现有结构；不重新选模板，也不调用应用脚本覆盖。
2. 新建资源先按 `useCases` 筛选，再比较 `layoutSignature`。只有模板能够以最小结构修改容纳需求时才使用 `direct`，选择信息架构最接近的一项。
3. 新建资源没有相近布局时使用 `none`，不读取具体模板、不调用应用脚本，只按 HTML DSL 创建最小合法 source HTML。
4. 不按题材、示例文案、配色或“看起来最接近”进行代表性回退。需要新增主要区域、删除主要列或改变导航层级才能使用的模板，不属于相近布局。

## `direct` 模式的应用与保护

确定精确 `templateId`、复用区块和必要修改后，在 Worldplay workspace 根目录运行：

```bash
node <skill-local>/ui/templates/scripts/apply-runtime-ui-template.mjs <templateId> wprefabs/<prefabId>/assets/uis/<resourceId>
```

`<skill-local>` 是 resource-generation 的 `SKILL.md` 所在目录。脚本原子创建 `html/`、`images/`，将横屏 HTML 根节点的 `data-u-name` 设置为目标 `<resourceId>`；模板、路径或目标状态不合法时不写入。

目录表的 `copyRoot` 只是模板的内部标识，不是 Agent 可直接读取的工作区路径。使用当前 Skill 返回的真实路径调用上面的公开脚本，再读取目标 `html/1920x1080.html`；不拼接或搜索 addon、runtime 或仓库中的模板源目录。

应用后立即读取工作区中的完整 HTML 和全部 `[ADAPTATION-CONTRACT ...]`，原样保留契约注释。应用后的 HTML 是最终底稿，不删除重建或整体替换；除契约明确允许的调整外，保留节点标签、父子层级、矩形和 `src`。默认保护：

- `layoutSignature` 对应的 panel、tab、list/grid/detail 空间层级；
- 主要信息架构、滚动方向、列数和区块关系；
- 实际复用的模板 skin、颜色关系和按钮层级。

只做当前需求必要的最小修改：业务文案和数据、真实语义图片、根 `resourceId`、契约要求的节点名和事件、功能数量，以及 Runtime UI DSL 或官方 HUD 规则要求的调整。不得因为个人偏好、统一命名或重新设计而整体重写模板。

模板 SVG 的配色、描边、圆角和阴影是只读视觉基线，按原有用途和矩形复用。除按契约删除未用资产或用真实语义图替换占位图外，不修改 SVG 内容，也不用新 SVG 或 HTML 重画同一皮肤。

默认只处理横屏 `html/1920x1080.html`；仅在任务明确要求且横屏已确认时追加竖屏 `html/1170x2532.html`。实例行为按 [UI 行为](../../../prefab-edit/resources/ui/instances.md)处理。

## 占位图与未用资产清理

- `itemIconPlaceholder.svg` 和头像占位图仅表示位置。有真实业务项时复用已有图片，或按 [UI 视觉资产](ui-assets.md) 调用 `generate-ui-png-atlas.mjs`，图片落盘后更新 `src`；无业务项时删除对应 `<img>`。不留空 `src`，图片引用规则见 [UI HTML](ui-html.md#图片引用)。
- `secondaryActionBtnSkin.svg` 仅在最终存在次操作、且由契约指定的 skin 节点引用时保留。归档前删除所有未被 HTML image 节点引用的图片，不通过隐藏或屏幕外节点保留备用资产。

## 模板专属适配

- `runtime-left-tab-horizontal-cards-popup`：按 `navigation-list` 选择列表项呈现方式；按 `navigation-actions` 和 `content-actions` 调整操作数量；按 `content-presentation` 保持正文落在内容区。
- `runtime-left-tab-item-grid-popup`：按 `optional-category-tabs` 决定是否保留左侧分类；按真实业务项调整卡片数量，删除末尾多余卡片，不保留由 Lua 隐藏的备用模板卡片。
- `runtime-notification-popup`：按 `notification-actions` 生成一到两个确认操作，并保持 skin 与 button 矩形一致。
- `runtime-split-detail-popup`：按 `optional-category-tabs` 决定是否保留左侧分类；按真实选项调整详情卡片数量。
- `runtime-three-panel-inventory-popup`：按 `optional-category-tabs`、`inventory-grid`、`detail-presentation` 和 `detail-actions` 调整；网格保持五列、row-major、末行左对齐，只删除末尾槽位。
- `runtime-top-tab-grid-popup`：按 `optional-top-tabs` 决定是否保留顶部分类；按真实业务项调整网格数量，删除末尾多余卡片，不保留由 Lua 隐藏的备用模板卡片。
- `runtime-vertical-action-list-popup`：按真实玩家或操作项调整行数，只为真实玩家保留头像；保持纵向滚动和下一行露出关系。
