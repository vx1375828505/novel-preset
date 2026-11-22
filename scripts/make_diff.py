#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 【文件卡】作用=生成“对照页”单文件 HTML（原稿→现文 的逐字修订视图 / 建议稿预览），供用户验收｜何时用=精修交付后、分析报告出完待拍板时｜上游=023_报告格式.md §对照页｜下游=minis://workspace/ 或 05_草稿/归档备份/ 的输出文件｜依赖=Python3 标准库，无外部资源，跨平台可带走
"""用法：
  1) 精修交付：python3 tools/make_diff.py 原件.txt 现文.txt --title "ch003 精修对照" --out /var/minis/workspace/x.html
  2) 建议预览：python3 tools/make_diff.py 现文.txt --pairs 建议.txt --title "ch003 建议预览" --out ...
     建议.txt 每行一条：原句|||改后     （空行和 # 开头行忽略；原句必须能在现文找到）
  红=删、绿=增、黑=未动。
"""
import argparse, html, io, re, sys, difflib


def paras(t):
    return [p.strip() for p in re.split(r"\n{2,}", t) if p.strip()]


def chardiff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(html.escape(a[i1:i2]))
        elif tag == "delete":
            out.append("<del>%s</del>" % html.escape(a[i1:i2]))
        elif tag == "insert":
            out.append("<ins>%s</ins>" % html.escape(b[j1:j2]))
        else:
            out.append("<del>%s</del><ins>%s</ins>" % (html.escape(a[i1:i2]), html.escape(b[j1:j2])))
    return "".join(out)


def apply_pairs(base, pairs_path, strict=True):
    pairs, skipped = [], []
    for ln, line in enumerate(io.open(pairs_path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "|||" not in line:
            skipped.append("第%d行缺 ||| 分隔" % ln)
            continue
        old, new = line.split("|||", 1)
        if old not in base:
            skipped.append("第%d行原句未命中：%s" % (ln, old[:20]))
            if strict:
                continue
            continue
        base = base.replace(old, new)
        pairs.append((old, new))
    return base, pairs, skipped


def build(base_text, new_text, title, subtitle_note=""):
    op_, cp_ = paras(base_text), paras(new_text)
    sm = difflib.SequenceMatcher(None, op_, cp_, autojunk=False)
    body, nchg = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for p in op_[i1:i2]:
                body.append("<p>%s</p>" % html.escape(p))
        elif tag == "delete":
            nchg += i2 - i1
            for p in op_[i1:i2]:
                body.append('<p class="blk-del"><del>%s</del></p>' % html.escape(p))
        elif tag == "insert":
            nchg += j2 - j1
            for p in cp_[j1:j2]:
                body.append('<p class="blk-ins"><ins>%s</ins></p>' % html.escape(p))
        else:
            nchg += 1
            for k in range(max(i2 - i1, j2 - j1)):
                a = op_[i1 + k] if i1 + k < i2 else None
                b = cp_[j1 + k] if j1 + k < j2 else None
                if a and b:
                    body.append("<p>%s</p>" % chardiff(a, b))
                elif a:
                    body.append('<p class="blk-del"><del>%s</del></p>' % html.escape(a))
                else:
                    body.append('<p class="blk-ins"><ins>%s</ins></p>' % html.escape(b))

    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>
:root{--ink:#1d1d1f;--muted:#6b6b70;--red:#b3261e;--redbg:#fdecea;--green:#146c43;--greenbg:#e6f4ec;--line:#e5e5ea;}
*{box-sizing:border-box}
body{margin:0;background:#faf9f7;color:var(--ink);font:17px/1.95 -apple-system,"PingFang SC","Noto Sans CJK SC",serif}
.wrap{max-width:44em;margin:0 auto;padding:28px 20px 80px}
h1{font-size:22px;margin:0 0 6px}
.sub{color:var(--muted);font-size:14px;margin-bottom:16px;line-height:1.7}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:#fff;margin-bottom:18px}
.legend b{font-weight:600}
.chapter{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px 20px}
.chapter p{margin:0 0 14px;text-indent:2em}
del{color:var(--red);background:var(--redbg);text-decoration:line-through;text-decoration-thickness:1px}
ins{color:var(--green);background:var(--greenbg);text-decoration:none;border-radius:3px;padding:0 1px}
.blk-del,.blk-ins{padding-left:10px;border-left:3px solid}
.blk-del{border-color:var(--red)}.blk-ins{border-color:var(--green)}
.foot{color:var(--muted);font-size:13px;margin-top:18px;line-height:1.8}
</style></head><body><div class="wrap">
<h1>%s</h1>
<div class="sub">%s</div>
<div class="legend"><span><del>删</del>＝原稿有、现在没有</span><span><ins>增</ins>＝现在新增</span><span><b>黑字</b>＝一字未动</span></div>
<div class="chapter">
%s
</div>
<div class="foot">%s</div>
</div></body></html>""" % (
        html.escape(title), html.escape(title),
        html.escape(subtitle_note or ("共 %d 处段落级改动" % nchg)),
        "\n".join(body),
        "红色删除线＝原稿有、现在没有；绿色＝现在新增；黑字＝未动。",
    )


def main():
    ap = argparse.ArgumentParser(description="生成逐字对照页（单文件 HTML）")
    ap.add_argument("base", help="基线文本（精修前原件 / 现行正文）")
    ap.add_argument("current", nargs="?", help="对照文本（精修后定稿）；与 --pairs 二选一")
    ap.add_argument("--pairs", help="建议列表：每行 原句|||改后")
    ap.add_argument("--title", default="对照页")
    ap.add_argument("--note", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = io.open(args.base, encoding="utf-8").read()
    if args.pairs:
        new, pairs, skipped = apply_pairs(base, args.pairs)
        note = args.note or ("建议稿预览（未落盘）· %d 条建议生效" % len(pairs))
        if skipped:
            note += " · 跳过：" + "；".join(skipped[:5])
        tgt = new
    else:
        if not args.current:
            sys.exit("需要 current 文件或 --pairs")
        tgt = io.open(args.current, encoding="utf-8").read()
        note = args.note
    io.open(args.out, "w", encoding="utf-8").write(build(base, tgt, args.title, note))
    print("已生成:", args.out)


if __name__ == "__main__":
    main()
