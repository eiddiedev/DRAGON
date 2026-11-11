import json
from pathlib import Path
from html import escape

root = Path(__file__).resolve().parent
plan = json.loads((root / 'review-plan.json').read_text())
cards = []
for i, item in enumerate(plan['entries'], 1):
    image = root / item['id'] / 'concept.png'
    name = escape(item['name'])
    status = '已通过' if item['status'] == 'concept_approved' else '修订待验收'
    src = item['id'] + '/concept.png'
    if not image.exists():
        raise FileNotFoundError(image)
    cards.append(f'<article data-category="{item["category"]}"><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{name}"></a><div><small>{i:02d} · {item["category"]}</small><h2>{name}</h2><p>{status} · 点击图片查看原图</p><a href="{item["id"]}/prompt.txt">生成提示词</a></div></article>')
html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>龙眠之境 · 模型概念图验收</title><style>
*{box-sizing:border-box}body{margin:0;background:#11121b;color:#f0edf7;font:16px/1.6 system-ui,sans-serif}header,main{max-width:1500px;margin:auto;padding:32px}header p{color:#bcb6cd;max-width:950px}h1{font-size:34px;margin:0}nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:24px}button{background:#272536;color:#fff;border:1px solid #59516b;border-radius:30px;padding:9px 20px;cursor:pointer}button.active{background:#7957ae}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:24px;padding-top:0}article{background:#20202d;border:1px solid #363344;border-radius:16px;overflow:hidden}article img{width:100%;height:330px;object-fit:contain;background:#d7d7d7;display:block}article div{padding:20px}h2{font-size:20px;margin:4px 0}small,p{color:#bcb6cd}article p{margin:4px 0}a{color:#cbb3ef}article[hidden]{display:none}footer{padding:32px;text-align:center;color:#aaa}
</style><header><h1>龙眠之境 · 概念图验收</h1><p>34 张概念图均已通过，模型已下载，动作正在检查。<a href="horse_motion/index.html">查看马的行走修正预览</a>。所有龙纹统一为西方龙。传送门、龙和松树不在本批范围内。城堡只制作附加装饰件，保留现有建筑格局；古树拆为树干与一片独立叶片，叶片由你自行复制摆放，通过材质改色与发光。马、羊和女巫按现有工程资产重新调整比例。<a href="style_references/current_sheep.png">查看工程原羊模型参考</a></p><nav>'''
categories = ['全部'] + list(dict.fromkeys(x['category'] for x in plan['entries']))
html += ''.join(f'<button class="{"active" if i == 0 else ""}" data-filter="{c}">{c}</button>' for i,c in enumerate(categories))
html += '</nav></header><main>' + ''.join(cards) + '</main><footer>内置 imagegen 生成 · 原图与每张提示词均保存在本目录 · 请按名称或编号反馈修改</footer><script>document.querySelectorAll("button").forEach(b=>b.onclick=()=>{document.querySelectorAll("button").forEach(x=>x.classList.remove("active"));b.classList.add("active");document.querySelectorAll("article").forEach(x=>x.hidden=b.dataset.filter!=="全部"&&x.dataset.category!==b.dataset.filter)});</script></html>'
(root / 'index.html').write_text(html)
print(f'Gallery ready: {len(cards)} images')
