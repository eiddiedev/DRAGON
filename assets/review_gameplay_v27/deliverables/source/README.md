# v27 制作源恢复

此目录保存本轮实际作者目标 `actors_v27`、`gameplay_v27` 的制作源快照。原作者位于独立工程 `project-8f93f84d-13f4-4ca1-95b2-42eafc8c27a5` 的 `workspace_amfuq048`；这些旧标识用于追溯，不是新电脑可直接复用的会话。

- `actors_v27/`：角色、骨骼动画引用、坐骑和羊的脚本与模型作者输入。
- `gameplay_v27/`：玩法与界面脚本、预制风车、模型作者输入、音频和特效制作源。
- `source-manifest.json`：每个保留文件的大小与 SHA-256，以及原资源归档 URI/内容摘要。原归档回执只是对应旧字节的来源记录，修改源码后不能当成新版本已归档。
- 上一级 `actors_v27.wprefab`、`gameplay_v27.wprefab`：本轮完整可导入容器，用于通过公开 CLI 恢复新的作者目标。

保留了 `prefab.json`、`meta.json`、注册 Lua、拓扑 GLB、Three.js 作者文件、贴图、特效配置与 WAV。没有复制 `.awc`、日志、私有会话状态、`.tmp` 或可重建的 `package/`；小型资源归档回执另存清单。模型恢复所得的 `original-meta-*`、`restore-model.glb` 等来源证据仍保留。目录中缺少某项作者元数据时，保持导入器的原状，没有补造来源。

## 恢复可编辑目标

1. 安装当前造世界 CLI，先读 `douyin-world guide workflow` 与 `douyin-world guide prefab`。选择隔离制作工程，通过公开 `project workspace create` 创建新的真实工作区，记录返回的工作区 ID。不要复制旧 MIX/.state 或会话文件，也不要将此目录直接覆盖正式工程。
2. 从仓库根目录，把上一级完整容器导入**新的**作者目标。下列占位符替换为实际新工作区；已有同名目标拒绝覆盖，改用新的名称。

   ```sh
   douyin-world authoring prefab import assets/review_gameplay_v27/deliverables/gameplay_v27.wprefab --prefab gameplay_v27_restored --workspace-id <新工作区ID>
   douyin-world authoring prefab import assets/review_gameplay_v27/deliverables/actors_v27.wprefab --prefab actors_v27_restored --workspace-id <新工作区ID>
   douyin-world project locate gameplay_v27_restored
   douyin-world project locate actors_v27_restored
   ```

3. 用 `authoring resource list --prefab <新目标> --workspace-id <新工作区ID>` 核对恢复结果。按定位返回的真实作者目录编辑；本快照供逐文件对照和补回实际作者输入。保留恢复后脚本身份与绑定，不把旧 `prefab.json`、节点 ID 或脚本 ID 直接覆盖进新目标。需要恢复未带回的模型输入时，用公开 `authoring resource model import <新资源ID> --glb <本目录实际GLB> --prefab <新目标> --workspace-id <新工作区ID>`，再用 SDK 显式更新目标引用。
4. 修改后依次执行相关资源检查/归档、作者 `validate`、`build` 和 `result archive`。资源归档不会自动替换实例。正式场景已有 v27 两包，不应再次整包叠加导入；后续替换先只读确认当前根和布局，按新的改动范围更新。

风车的可动轴在 `gameplay_v27/assets/models/model-windmill-v27/topology/model.glb` 中，名称为 `windmill_rotor_pivot`；保留层级和反向子节点位移。不要重新合并扇叶与塔身，也不要恢复成依赖手机 CPU 网格切割的旧模型。

此来源快照不含编辑器下载缓存或账号凭据。已有云端资源仍需账号权限与网络；源码/包恢复成功不代表手机审核端通过。安装状态与待验收问题见本轮 `REPORT.md` 和仓库 `HANDOFF.md`。

## 核对快照完整性

在仓库根目录运行以下只读检查：

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json
root = Path('assets/review_gameplay_v27/deliverables/source')
manifest = json.loads((root / 'source-manifest.json').read_text())
count = 0
for prefab, entry in manifest['prefabs'].items():
    expected = set(entry['files'])
    actual = {str(p.relative_to(root / prefab)) for p in (root / prefab).rglob('*') if p.is_file()}
    assert actual == expected, (prefab, 'file set mismatch')
    for name, spec in entry['files'].items():
        content = (root / prefab / name).read_bytes()
        assert len(content) == spec['bytes'], (prefab, name, 'size')
        assert hashlib.sha256(content).hexdigest() == spec['sha256'], (prefab, name, 'sha256')
        count += 1
print(f'OK: {count} author source files')
PY
```
