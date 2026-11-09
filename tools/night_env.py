#!/usr/bin/env python3
"""把世界环境改成奇幻夜晚，可重复运行。用法：night_env.py <工程目录>
编辑器打开工程时按 settings/env-param-overrides.json 里选中的模板加载环境，所以真正生效的是这个文件；
scene.data 的 envParamJson 也同步改掉。模板先在编辑器里选成「黑夜」(env_night)。必须在工程关闭时运行。
"""
import json
import sys
import os
import zipfile

project = sys.argv[1]
src = os.path.join(project, 'scene.data')
out = src + '.tmp'
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
e = json.loads(d['envParamJson'])


def rgb(r, g, b):
    return {'r': r, 'g': g, 'b': b, 'a': 1.0}


e.update(
    # 月光：从西南斜照，出生点看到的这一面有层次（和地形贴图里烘的方向一致）
    mainLightColor=rgb(.66, .76, 1.0),
    mainLightStrength=.95,
    mainLightDir={'x': 40.0, 'y': 60.0, 'z': 0.0},
    shadowStrength=.85,
    # 角色不能黑成一团
    characterLightColor=rgb(.72, .78, 1.0),
    characterStrenght=2.4,
    characterAmbient=rgb(.42, .42, .62),
    # 紫色远雾；天空穹顶在 520 米，雾要从更远的地方才起作用
    fogEnable=True,
    fogColor=rgb(.11, .07, .24),
    fogMode=1,
    startFog=260.0,
    endFog=1500.0,
    # 太阳光晕关掉
    flareEnable=False,
    # 发光更明显，边缘压暗
    BloomEnabled=True,
    BloomThreshold=.85,
    BloomIntensity=.85,
    BloomScatter=.65,
    LUT=False,
    Vignette=True,
    VignetteColor=rgb(.05, .03, .16),
    VignetteAmount=.28,
    VignetteSoftness=.45,
)
d['envParamJson'] = json.dumps(e, ensure_ascii=False, separators=(',', ':'))
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
os.replace(out, src)

# 模板覆盖参数（字段名和 envParamJson 不一样）
path = os.path.join(project, 'settings', 'env-param-overrides.json')
o = json.load(open(path, encoding='utf8'))
assert o['selected']['templateId'] == 'env_night', o['selected']
o['overrides']['official']['env_night']['params'].update(
    flareEnable=False,
    mainLightColor='#A8C2FF',
    mainLightStrength=.95,
    mainLightPitch=40.0,
    mainLightYaw=60.0,
    shadowStrength=.85,
    characterAmbient='#6B6B9E',
    characterLightColor='#B8C7FF',
    characterStrenght=2.4,
    fogEnable=True,
    fogColor='#1C123D',
    startFog=260,
    endFog=1500,
    bloomEnabled=True,
    bloomThreshold=.85,
    bloomIntensity=.85,
    bloomScatter=.65,
    vignette=True,
    vignetteColor='#0D0829',
    vignetteAmount=.28,
    vignetteSoftness=.45,
)
json.dump(o, open(path, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
print('env updated')
