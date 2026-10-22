#!/usr/bin/env python3
"""preToolUse hook: kiro port of oh-my-opencode's prometheus-md-only guard.

Blocks (exit 2) any write by the planner agent unless the target is a .md file
under a .sisyphus/ directory inside the working directory. Also blocks the
`code` tool's pattern_rewrite (it mutates files).
"""
import json
import os
import re
import sys

SISYPHUS_DIR = re.compile(r"(^|[/\\])\.sisyphus[/\\]", re.I)


def block(msg: str) -> int:
    sys.stderr.write(
        f"[prometheus-md-only] BLOCKED: {msg}\n"
        "You are Prometheus, a READ-ONLY planner. You may only write markdown files under "
        ".sisyphus/ (plans: .sisyphus/plans/*.md, drafts: .sisyphus/drafts/*.md). "
        "Do not retry. Implementation happens after planning, via the sisyphus/atlas agents.\n"
    )
    return 2


def is_allowed(path: str, cwd: str) -> bool:
    resolved = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    root = os.path.realpath(cwd)
    rel = os.path.relpath(resolved, root)
    if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel):
        return False
    return bool(SISYPHUS_DIR.search(rel)) and resolved.lower().endswith(".md")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    tool = (event.get("tool_name") or "").lower()
    inp = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()

    if tool == "code":
        if inp.get("operation") == "pattern_rewrite" and inp.get("dry_run") is False:
            return block("code pattern_rewrite modifies files.")
        return 0

    if tool in ("write", "fs_write", "fswrite"):
        path = inp.get("path")
        if not path:
            return block("write without a path.")
        if not is_allowed(path, cwd):
            return block(f"'{path}' is not a .md file under .sisyphus/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
