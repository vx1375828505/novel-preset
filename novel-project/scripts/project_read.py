#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable read helper for the novel project: plan / chunk / search / card.

Python 3 standard library only. Works on phone or desktop.
"""
import argparse
import json
import os
import re


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def cmd_plan(args):
    rows = []
    for p in args.files:
        if os.path.isfile(p):
            n = os.path.getsize(p)
            c = (n + args.chunk_size - 1) // args.chunk_size if n else 0
            rows.append((p, n, c))
        else:
            rows.append((p, -1, 0))
    print(f"{'file':<70} {'bytes':>9} {'chunks':>7}")
    for p, n, c in rows:
        print(f"{p:<70} {n:>9} {c:>7}")
    total = sum(n for _, n, _ in rows if n > 0)
    print(f"\ntotal={total} bytes; chunk_size={args.chunk_size}")
    print("plan: 第1层启动 → 第2层任务底座 → 读取计划 → 后续层")


def split_text(text, max_chars):
    paras = re.split(r"\n\s*\n", text)
    chunks, buf, size = [], [], 0
    for para in paras:
        para = para.strip()
        if not para:
            continue
        if len(para) > max_chars:
            if buf:
                chunks.append("\n\n".join(buf))
                buf, size = [], 0
            for i in range(0, len(para), max_chars):
                chunks.append(para[i:i + max_chars])
            continue
        if size + len(para) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf, size = [], 0
        buf.append(para)
        size += len(para) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def cmd_chunk(args):
    text = read_text(args.file)
    os.makedirs(args.outdir, exist_ok=True)
    chunks = split_text(text, args.chunk_size)
    base = os.path.basename(args.file)
    index = []
    for i, ch in enumerate(chunks, 1):
        fn = os.path.join(args.outdir, f"{base}.chunk{i:02d}.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(ch)
        index.append({"chunk": i, "file": fn, "chars": len(ch), "head": ch[:60]})
    with open(os.path.join(args.outdir, f"{base}.index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(chunks)} chunks -> {args.outdir}")


def cmd_search(args):
    rx = re.compile(args.query, re.I)
    hits = 0
    exts = (".md", ".txt", ".json", ".py")
    for dirpath, _, files in os.walk(args.root):
        for fn in files:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dirpath, fn)
            try:
                lines = read_text(p).splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    print(f"{p}:{i}: {line.strip()[:220]}")
                    hits += 1
                    if hits >= args.max_hits:
                        print("... (max hits)")
                        return
    if not hits:
        print("no hits")


def cmd_card(args):
    n = os.path.getsize(args.file) if os.path.isfile(args.file) else -1
    print(f"文件：{args.file}\n大小：{n}\n段：\n要点：\n用途：\n状态：✅/◐/❗")


def main():
    ap = argparse.ArgumentParser(description="Portable read helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="show file sizes and chunk plan")
    p.add_argument("files", nargs="+")
    p.add_argument("--chunk-size", type=int, default=30000)
    p.set_defaults(func=cmd_plan)

    c = sub.add_parser("chunk", help="split one file into chunks")
    c.add_argument("file")
    c.add_argument("outdir")
    c.add_argument("--chunk-size", type=int, default=30000)
    c.set_defaults(func=cmd_chunk)

    s = sub.add_parser("search", help="regex search under a directory")
    s.add_argument("root")
    s.add_argument("query")
    s.add_argument("--max-hits", type=int, default=20)
    s.set_defaults(func=cmd_search)

    d = sub.add_parser("card", help="print a 5-line layer card template")
    d.add_argument("file")
    d.set_defaults(func=cmd_card)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
