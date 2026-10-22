#!/usr/bin/env python3
"""userPromptSubmit hook: kiro port of oh-my-opencode's keyword-detector.

Reads the hook event JSON on stdin, strips code blocks, and when the prompt
contains ultrawork/ulw, search, or analyze keywords, prints the matching mode
directive(s) to stdout. kiro adds hook stdout to the agent's context.

Usage: keyword-detector.py [agent-name]
  agent-name is used to choose the planner variant of the ultrawork directive.
"""
import json
import os
import re
import sys

MODES_DIR = os.path.expanduser("~/.kiro/prompts/oh-my-kiro/modes")

CODE_BLOCK = re.compile(r"```[\s\S]*?```")
INLINE_CODE = re.compile(r"`[^`]+`")

ULTRAWORK = re.compile(r"\b(ultrawork|ulw)\b", re.I)
SEARCH = re.compile(
    r"\b(search|find|locate|lookup|look\s*up|explore|discover|scan|grep|query|browse|detect|trace|seek|track|pinpoint|hunt)\b"
    r"|where\s+is|show\s+me|list\s+all"
    r"|검색|찾아|탐색|조회|스캔|서치|뒤져|찾기|어디|추적|탐지|찾아봐|찾아내|보여줘|목록"
    r"|検索|探して|見つけて|サーチ|探索|スキャン|どこ|発見|捜索|見つけ出す|一覧"
    r"|搜索|查找|寻找|查询|检索|定位|扫描|发现|在哪里|找出来|列出"
    r"|tìm kiếm|tra cứu|định vị|quét|phát hiện|truy tìm|tìm ra|ở đâu|liệt kê",
    re.I,
)
ANALYZE = re.compile(
    r"\b(analyze|analyse|investigate|examine|research|study|deep[\s-]?dive|inspect|audit|evaluate|assess|review|diagnose|scrutinize|dissect|debug|comprehend|interpret|breakdown|understand)\b"
    r"|why\s+is|how\s+does|how\s+to"
    r"|분석|조사|파악|연구|검토|진단|이해|설명|원인|이유|뜯어봐|따져봐|평가|해석|디버깅|디버그|어떻게|왜|살펴"
    r"|分析|調査|解析|検討|研究|診断|理解|説明|検証|精査|究明|デバッグ|なぜ|どう|仕組み"
    r"|调查|检查|剖析|深入|诊断|解释|调试|为什么|原理|搞清楚|弄明白"
    r"|phân tích|điều tra|nghiên cứu|kiểm tra|xem xét|chẩn đoán|giải thích|tìm hiểu|gỡ lỗi|tại sao",
    re.I,
)


def is_planner(agent: str) -> bool:
    a = agent.lower()
    return "prometheus" in a or "planner" in a or a == "plan"


def load(name: str) -> str:
    try:
        with open(os.path.join(MODES_DIR, name), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def main() -> int:
    agent = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    prompt = event.get("prompt") or ""
    text = INLINE_CODE.sub("", CODE_BLOCK.sub("", prompt))

    blocks = []
    if ULTRAWORK.search(text):
        blocks.append(load("ultrawork-planner.md" if is_planner(agent) else "ultrawork.md"))
    if SEARCH.search(text):
        blocks.append(load("search.md"))
    if ANALYZE.search(text):
        blocks.append(load("analyze.md"))

    blocks = [b for b in blocks if b]
    if blocks:
        sys.stdout.write("\n\n".join(blocks) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
