# -*- coding: utf-8 -*-
"""整章通读对照页：模糊逐段配对，避免自动对齐把相邻段糊在一起。"""
import io, sys, html, difflib

base_p, new_p, out, title, note = sys.argv[1:6]
old = [p.strip() for p in io.open(base_p, encoding="utf-8").read().split("\n") if p.strip()]
new = [p.strip() for p in io.open(new_p, encoding="utf-8").read().split("\n") if p.strip()]

def sim(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

# 贪心配对：允许一段对多段（原稿两段合成定稿一段），相似度 >=0.55
pairs, used_old, last = [], set(), -1
for j, np_ in enumerate(new):
    best, bi, blen = 0.0, -1, 1
    for i in range(last + 1, min(len(old), last + 1 + 12)):
        if i in used_old:
            continue
        for L in (3, 2, 1):
            if i + L > len(old):
                continue
            joiner = "" if L > 1 else None
            cand = "".join(old[i:i + L]) if L > 1 else old[i]
            r = sim(cand, np_)
            if r > best:
                best, bi, blen = r, i, L
    if bi >= 0 and best >= 0.55:
        pairs.append(("merge" if blen > 1 else "pair", bi, j, blen)); last = bi + blen - 1
        for k in range(blen):
            used_old.add(bi + k)
    else:
        pairs.append(("ins", -1, j, 1))

def chardiff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    o = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            o.append(html.escape(a[i1:i2]))
        elif tag == "delete":
            o.append("<del>%s</del>" % html.escape(a[i1:i2]))
        elif tag == "insert":
            o.append("<ins>%s</ins>" % html.escape(b[j1:j2]))
        else:
            o.append("<del>%s</del><ins>%s</ins>" % (html.escape(a[i1:i2]), html.escape(b[j1:j2])))
    return "".join(o)

body, nchg, prev_old = [], 0, -1
for kind, i, j, blen in pairs:
    if kind == "merge":
        for k in range(prev_old + 1, i):
            body.append('<p class="blk-del"><del>%s</del></p>' % html.escape(old[k])); nchg += 1
        joined = "".join(old[i:i + blen])
        if joined == new[j]:
            body.append("<p>%s</p>" % html.escape(joined))
        else:
            body.append("<p>%s</p>" % chardiff(joined, new[j])); nchg += 1
        prev_old = i + blen - 1
    elif kind == "pair":
        for k in range(prev_old + 1, i):
            body.append('<p class="blk-del"><del>%s</del></p>' % html.escape(old[k])); nchg += 1
        if old[i] == new[j]:
            body.append("<p>%s</p>" % html.escape(old[i]))
        else:
            body.append("<p>%s</p>" % chardiff(old[i], new[j])); nchg += 1
        prev_old = i
    else:
        body.append('<p class="blk-ins"><ins>%s</ins></p>' % html.escape(new[j])); nchg += 1
for k in range(prev_old + 1, len(old)):
    body.append('<p class="blk-del"><del>%s</del></p>' % html.escape(old[k])); nchg += 1

doc = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>
:root{--ink:#1d1d1f;--muted:#6b6b70;--red:#b3261e;--redbg:#fdecea;--green:#146c43;--greenbg:#e6f4ec;--line:#e5e5ea;}
*{box-sizing:border-box}
body{margin:0;background:#faf9f7;color:var(--ink);font:17px/1.95 -apple-system,"PingFang SC","Noto Sans CJK SC",serif}
.wrap{max-width:44em;margin:0 auto;padding:28px 20px 80px}
h1{font-size:22px;margin:0 0 6px}
.sub{color:var(--muted);font-size:14px;margin-bottom:16px;line-height:1.7}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:#fff;margin-bottom:18px}
.chapter{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px 20px}
.chapter p{margin:0 0 14px;text-indent:2em}
del{color:var(--red);background:var(--redbg);text-decoration:line-through;text-decoration-thickness:1px}
ins{color:var(--green);background:var(--greenbg);text-decoration:none;border-radius:3px;padding:0 1px}
.blk-del,.blk-ins{padding-left:10px;border-left:3px solid}
.blk-del{border-color:var(--red)}.blk-ins{border-color:var(--green)}
.foot{color:var(--muted);font-size:13px;margin-top:18px;line-height:1.8}
</style></head><body><div class="wrap">
<h1>%s</h1><div class="sub">%s</div>
<div class="legend"><span><del>删</del>＝原稿有、改后没有</span><span><ins>增</ins>＝改后新增</span><span><b>黑字</b>＝一字未动</span></div>
<div class="chapter">%s</div>
<div class="foot">红色删除线＝原稿字；绿色＝新增字；黑字＝未动。</div>
</div></body></html>""" % (html.escape(title), html.escape(title), html.escape(note), "\n".join(body))
io.open(out, "w", encoding="utf-8").write(doc)
print("段对", len(pairs), "改动", nchg)
