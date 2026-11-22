#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小说项目库初始化器：把模板复制到新书目录，并替换占位符。

用法：
    python3 init_project.py <目标目录> --title "书名" [--genre 都市] [--platform 番茄]
        [--hero 男主名] [--role 女主名] [--date 2026-11-23] [--force] [--dry-run]

模板默认取本脚本同级目录的 ../template/（技能安装后即
/var/minis/skills/novel-project/template）。

设计原则：
- 只替换「有实际值」的占位符；{{此处填写}} 等保持原样，留给用户后续填。
- 目标目录非空时默认拒绝，需显式 --force，避免误覆盖已有书稿。
- 纯标准库，无第三方依赖；手机端 python3 可直接跑。
"""
import argparse
import os
import shutil
import sys

# 可替换的占位符 -> 参数名
REPLACEABLE = {
    "{{书名}}": "title",
    "{{流派}}": "genre",
    "{{平台}}": "platform",
    "{{男主名}}": "hero",
    "{{角色名}}": "role",
    "{{日期}}": "date",
    "{{章标题}}": "chapter_title",
}

# 保持原样的占位符（提示用户后续手工填）
KEEP = ["{{此处填写}}", "{{用户}}", "{{曾用名}}", "{{对标文名}}",
        "{{设定名}}", "{{第N章}}", "{{YYYY-MM-DD}}", "{{YYYYMMDD}}"]


def iter_files(root):
    for base, _dirs, files in os.walk(root):
        for name in files:
            yield os.path.join(base, name)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_tpl = os.path.normpath(os.path.join(here, "..", "template"))

    ap = argparse.ArgumentParser(description="按预设模板初始化小说项目库")
    ap.add_argument("dest", help="目标目录，例如 /var/minis/mounts/小说/我的新书")
    ap.add_argument("--template", default=default_tpl, help=f"模板目录（默认 {default_tpl}）")
    ap.add_argument("--title", required=True, help="书名，替换 {{书名}}")
    ap.add_argument("--genre", default="", help="流派，替换 {{流派}}")
    ap.add_argument("--platform", default="", help="平台，替换 {{平台}}")
    ap.add_argument("--hero", default="", help="男主名，替换 {{男主名}}")
    ap.add_argument("--role", default="", help="角色名，替换 {{角色名}}")
    ap.add_argument("--date", default="", help="日期，替换 {{日期}}")
    ap.add_argument("--chapter-title", default="", help="第001章标题，替换 {{章标题}}")
    ap.add_argument("--force", action="store_true", help="目标非空也继续（会覆盖同名文件）")
    ap.add_argument("--dry-run", action="store_true", help="只报告将要做什么，不写盘")
    args = ap.parse_args()

    tpl = os.path.abspath(args.template)
    dest = os.path.abspath(args.dest)
    if not os.path.isdir(tpl):
        sys.exit(f"[x] 模板目录不存在：{tpl}")
    if not os.path.isdir(os.path.join(tpl, "项目导引")):
        sys.exit(f"[x] 模板结构异常（缺 项目导引/）：{tpl}")

    values = {
        "title": args.title.strip(),
        "genre": args.genre.strip(),
        "platform": args.platform.strip(),
        "hero": args.hero.strip(),
        "role": args.role.strip(),
        "date": args.date.strip(),
        "chapter_title": args.chapter_title.strip(),
    }
    active = {ph: key for ph, key in REPLACEABLE.items() if values[key]}

    if os.path.isdir(dest) and os.listdir(dest) and not args.force:
        sys.exit(f"[x] 目标目录非空：{dest}\n    加 --force 可强制写入（会覆盖同名文件）")

    print(f"模板：{tpl}")
    print(f"目标：{dest}")
    print(f"替换：{'、'.join(active) if active else '（无）'}")
    if args.dry_run:
        n = sum(1 for _ in iter_files(tpl))
        print(f"[dry-run] 将复制 {n} 个文件，未写盘")
        return

    copied = 0
    replaced = 0
    for src in iter_files(tpl):
        rel = os.path.relpath(src, tpl)
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not src.lower().endswith((".md", ".txt", ".html", ".py", ".json")):
            shutil.copyfile(src, dst)
            copied += 1
            continue
        with open(src, "r", encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
        for ph, key in active.items():
            hit = text.count(ph)
            if hit:
                text = text.replace(ph, values[key])
                replaced += hit
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        copied += 1

    # 统计剩余占位符
    left = {}
    for f in iter_files(dest):
        if not f.lower().endswith((".md", ".txt", ".html")):
            continue
        with open(f, "r", encoding="utf-8-sig", errors="replace") as fh:
            body = fh.read()
        for ph in KEEP:
            c = body.count(ph)
            if c:
                left[ph] = left.get(ph, 0) + c

    print(f"\n[ok] 复制 {copied} 个文件，替换 {replaced} 处占位符")
    if left:
        print("待你后续填写：")
        for ph, c in sorted(left.items(), key=lambda x: -x[1]):
            print(f"  {ph}  x{c}")
    print("\n下一步：先读 项目导引/001_总路由.md 与 项目中枢/006_进度.md，再按 061 路由选一份规则。")


if __name__ == "__main__":
    main()
