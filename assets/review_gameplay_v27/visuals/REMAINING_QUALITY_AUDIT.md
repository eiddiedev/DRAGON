# 撤降档后：纹理与材质路径复核

## 结论

只读检查了正式 v26 与隔离 v27 的**保存场景内全部 38 个登记脚本**及资源表，排除了磁盘上历史 prefab 的未绑定旧源码。没有发现仍在对世界模型纹理写入 mip 上限、强制降分辨率、Resize、Reinitialize、Compress 或 Point filtering 的路径。没有另写未经证实的恢复补丁。

v27 已移除全局 0.6 renderScale 和 HDR/后处理/阴影关闭逻辑；`visuals-live.json` 的实际读回为 renderScale=1、HDR=true、post=true、shadows=All、shadowDistance=40，保留 30 FPS。该读回中的 AA=0、MSAA=false 是本轮没有修改的实际平台设置，不能称作已恢复到 AA=4，也不能在没有既有默认依据时强行拉高。

## 有针对性的检查

| 路径 | 证据及结论 |
|---|---|
| 原始地形图 | v26/v27 保存 ZIP 中全部 22 个非场景 JSON payload 字节完全一致；43 个 resourceRefs 完全相同，环境参数也相同。地形色图保持 2048×2048，没有本轮缩图。 |
| 白草修复 | bridge 的 `UI.bindMobileFlowerGround` 只对 `ParaSpace/World/ENV/EnvGrass03` 的 `_GroundTex` 绑定地形色图，未改叶片 base texture、alpha、shader 或过滤方式。其 v26/v27 嵌入备用图片和当前保存的 MatCoverTex **SHA256 完全相同**：`d6b33233bfc4a4de9bbdc5333559da41278a7fa8863bf92eb9f9543fd61d3a0e`。应保留，不能盲撤。 |
| 麦田 | `UI.updateReeds` 克隆已载入材质并调金色，只做低频摆动；当前版本没有恢复旧 URP Shader.Find 替换路径。当前 `wheat-high/low/single-geometry.glb` 本身使用顶点色，没有图片纹理可被脚本降低分辨率。 |
| 小草、松树 | 全部有效脚本内未发现对它们纹理 mip、过滤器、尺寸的写入。松树优化只限制枝叶角度、频率与碰撞，不替换材质贴图。 |
| 旧地形细节 | `setupDetail` 只向历史 `t000_000` 等命名模型的 emission 通道加入细节图，不替换原 base texture、不缩图；当前主地形是 ID 3193404 的 terrainDisplayData，原 16 层数据保持不变。 |
| 天空材质 | `UI.setupMotion` 为天空渐变采用透明 unlit，传入原始 texture 对象；没压缩/替换低清图。本轮没有回滚到手机不兼容 shader。 |
| Point filtering | bridge 唯一 `FilterMode.Point` 写入位于 `UI.makeGrain`，仅为自行生成的 UI 纸面噪点层；不是草、麦、地形或模型贴图。 |
| 64/96/128 纹理 | dragon_rpg 64 像素纹理是按钮图标，96 是选中圆环，bridge 128 是任务 logo；不能把这些尺寸当成世界模型纹理精度。 |
| 古书/地图 | v24 曾将 UI 解码从 mipmap+Trilinear 改成 no-mipmap+Bilinear，并释放 CPU 可读副本；**图片本身像素尺寸未降**。这是 UI 独立内存路径，不解释模型纹理恶化，本轮不恢复多余 CPU 副本。 |
| 城堡 | castle_baked_display / castle_smooth_display 使用原完整烘焙颜色图作为 emission；_ORM 白图与底色黑是既有烘焙显示约定，而非手机性能版缩贴图。仅作用各自城堡根。本轮不撤，避免双重打光。 |
| 服装/敌人 | 服装构造和敌人特殊材质存在去贴图/纯色操作，仅在指定服装或战斗节点上；源代码与既有版本相同，不作用植被和地形。本轮未修改已确认服装或战斗外观规则。 |

## 剩余风险的准确表述

脚本无继续降纹理的证据，不代表手机端纹理加载、shader alpha 或平台采样已验收。新的提审包仍须对截图中具体草花检查 base texture 是否存在、实际加载尺寸/mipmapLimit、透明裁切和 shader；不能只凭本地 screenshot 宣称手机质量恢复。

麦田缓存 key 使用 shader+mainTexture+tone，不含全部材质属性；对未来纹理不同且 custom shader 的 mainTexture 未映射的麦田资产存在合并风险。但当前三种麦田都是相同顶点色材质、无贴图，尚无实际纹理被缓存串用的证据，因此未扩大修复范围。

审计产物：`remaining-quality-audit.json`；重算：`python3 assets/review_gameplay_v27/visuals/audit_remaining_quality.py`。没有更改已合并文件、资源或实例。
