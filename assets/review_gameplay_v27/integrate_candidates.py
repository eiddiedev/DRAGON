from pathlib import Path
import re,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent
PROJECT=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-8f93f84d-13f4-4ca1-95b2-42eafc8c27a5')
W=PROJECT/'ai-sessions/workspace_amfuq048/wprefabs'
spec=importlib.util.spec_from_file_location('visual',ROOT/'visuals/patch_visuals.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
identity=re.compile(r'^---@(?:id|sourceScriptId|referenceName) .*\n',re.M)
manifest=[]
def install(src,dst):
 before=dst.read_text();ids=''.join(identity.findall(before));after=ids+identity.sub('',src)
 dst.write_text(after);manifest.append({'file':str(dst),'before':hashlib.sha256(before.encode()).hexdigest(),'after':hashlib.sha256(after.encode()).hexdigest()})
for p in (ROOT/'interactions').glob('dragon_*.lua'):
 install(p.read_text(),W/'gameplay_v27/scripts'/p.name)
bridge=W/'gameplay_v27/scripts/dragon_world_bridge.lua';install(mod.patch(bridge.read_text()),bridge)
for name in ('horse_seat_v1.lua','tripo_sheep_motion.lua'):
 install((ROOT/'actors'/name).read_text(),W/'actors_v27/scripts'/name)
# The test project is a byte-for-byte copy of official saved content. Keep all registered identities.
for p in (ROOT/'interactions').glob('dragon_*.lua'):
 install(p.read_text(),PROJECT/'scripts/modules/imported/prefab_20'/p.name)
bridge=PROJECT/'scripts/modules/imported/prefab_20/dragon_world_bridge.lua';install(mod.patch(bridge.read_text()),bridge)
(ROOT/'integration-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Updated',len(manifest),'registered/author sources; no scene byte edits')
