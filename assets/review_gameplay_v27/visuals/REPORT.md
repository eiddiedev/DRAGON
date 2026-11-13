# v27 画质与圣树修复候选

只写入本目录，没有修改主工程、场景节点、模型纹理、布局或正在运行的实例。

## 已确认的源码证据

1. `prefab_20/dragon_world_bridge.lua:4000` 的 `UI.applyLowRender` 仍然每秒生效，包含 `renderScale <= 0.6`、AA 为 0、禁用 HDR、MSAA、后处理及实时阴影。不是纹理文件被本轮缩图，而是整帧在低分辨率且没有抗锯齿的配置下渲染。关闭 HDR 和后处理还会去掉原有 Bloom 显示路径。对应旧版实测记录见 `assets/mobile_low_v24/REPORT.md`。
2. `prefab_20/dragon_world_bridge.lua:1124` 的圣树绑定只取每个 Renderer 的第一个 `.material`；第一次找到 Renderer 后永远设置 `found[name] = true`。迟到资源换掉材质时，后续仅更新旧材质 `_EmissionPower`，不检查场景当前实际材质。它也未开启 `_EMISSION`，未适配不使用 `_EmissionPower` 的 shader。
3. 历史材质探针 `assets/interactions_v1/real-tree-material-probe.json` 证明该树曾使用 `Douyin/AI/PBR/EnvLit_AI`，底纹属性为 `_BaseTex`。旧逻辑只找 `_BaseMap` / `_MainTex`，但不能仅据此断言本次 C 端最终 shader 相同。因此新逻辑保留导入材质，只按实际属性判断，不通过 Shader.Find 替换整个 shader。

## 候选变更

- 移除所有全局画质强降档，保留平台当前的纹理、renderScale、抗锯齿、阴影、HDR 与后处理设置。仅保留 30 FPS 帧率上限并在退出时还原上限，不盲目强制高于平台默认。
- 两个命名树冠每秒检查一次当前 Renderer / sharedMaterials，所有材质槽均支持，按原材质共享克隆，不修改其他树或草的颜色。异步资源替换后重新绑定，回收失去引用的克隆。
- 叶面按既有昼夜 blend 平滑转红；白天恢复原底色并将 emission 精确归零。EnvLit_AI 使用 `_EmissionPower`，Standard/URP 使用 HDR emission color。每秒最多 10 次绘制状态更新。
- 保留原有最多三盏不投射红色几何点的树冠灯，没有新增粒子或发光球。恢复平台后处理后允许原来的叶面光晕显示；若平台本身不启用 Bloom，需要实际提审环境判断，不能仅凭 CPU 测试承诺。
- 停用与退出恢复原材质并释放克隆和灯；公开 `GetHolyGlowDiagnostics()` 返回当前 shader、实际 emission、绑定数量与错误。
- `dragon_fx.lua` 及战斗粒子预算完全未修改。

## 合并

`python3 assets/review_gameplay_v27/visuals/patch_visuals.py <已经合并其他修复的bridge.lua> <输出bridge.lua>`

仅替换两个已有精确区块：`local holyTried...` 至城堡房间注释前，以及 `UI.lowRender...` 至 `GetLoadingDiagnostics` 前。`scope.GetScript`、桥脚本其余交互逻辑由交互代理单独合并，本补丁不覆盖。文件读写目标必须是候选目录。

## 验证与限制

`python3 assets/review_gameplay_v27/visuals/test_visuals.py` 使用 Lupa 执行真正的 Lua 替换代码。包含：首帧没有资源、延迟加载、多个材质槽、材质再次替换、外部覆盖颜色、两种 emission 路径、昼夜恢复、重复销毁、重新启用、既有 Update/Disable/Destroy 链，以及不修改任意平台原始画质值。合并后的整个 bridge 也经过 Lua 语法编译。结果在 `test-results.json`。

这些是状态逻辑验证，不是手机 GPU / 提审二维码验收。还需提审包读回 `GetMobileRenderStatus()` / `GetHolyGlowDiagnostics()`，确认夜间运行至少 10 秒和昼夜切换后两树冠持续红光、白天归绿，以及原始纹理与抗锯齿恢复；不能用本地截图替代手机验收。
