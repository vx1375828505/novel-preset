# tools — 跨 Agent 读取辅助
> 【序号】117｜【优先级】—｜类=资料

Python 3 标准库，无依赖。手机/电脑都能跑。

```bash
python3 tools/project_read.py plan <file...>
python3 tools/project_read.py chunk <file> <outdir> [--chunk-size 30000]
python3 tools/project_read.py search <dir> "<regex>" [--max-hits 20]
python3 tools/project_read.py card <file>
```

- `plan`：列出文件大小、按 30K 切需要几块；用于“读前预检”。
- `chunk`：按段落切块，写 `*.chunkNN.txt` + `*.index.json`；供大文件分段读。
- `search`：递归正则检索，只输出命中行；没有 `rg` 时的替代。
- `card`：打印 5 行层卡模板（文件/段/要点/用途/状态）。

30K 是单份拆分阈值，不是每轮上限；同一轮可并行读多份。
