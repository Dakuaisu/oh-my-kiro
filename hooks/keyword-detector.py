#!/usr/bin/env python3
"""userPromptSubmit hook: kiro port of oh-my-openagent's keyword-detector.

Reads the hook event JSON on stdin, strips code blocks, and when the prompt
contains the ultrawork keyword (`ultrawork` / `ulw`, but not `ulw-*` names),
prints the ultrawork directive to stdout. kiro adds hook stdout to the agent's
context.

Ultrawork is sticky per session, as upstream: once a prompt in a session
triggered it, later prompts in the same session get a compact
`<ultrawork-mode>active</ultrawork-mode>` marker instead of the full directive.

Usage: keyword-detector.py <agent-name> [model-id]
  agent-name: planner agents (prometheus/planner/plan) never get ultrawork.
  model-id:   GPT models get the GPT ultrawork variant.
"""
import json
import os
import re
import sys
import tempfile

MODES_DIR = os.path.expanduser("~/.kiro/prompts/oh-my-kiro/modes")
STATE_DIR = os.path.join(tempfile.gettempdir(), "oh-my-kiro-ultrawork")
SESSION_CAP = 256

CODE_BLOCK = re.compile(r"```[\s\S]*?```")
INLINE_CODE = re.compile(r"`[^`]+`")
# `ulw-plan`, `ulw-research` and other ulw-* skill names are not the ultrawork keyword.
ULTRAWORK = re.compile(r"\b(?:ultrawork|ulw(?!-\w))\b", re.I)
SLASH_COMMAND = re.compile(r"^\s*/[a-zA-Z][\w-]*(?:\s|$)")
STOP_CONTINUATION = re.compile(r"^\s*/stop-continuation(?:\s|$)", re.I)
CONTINUATION_MARKER = "<ultrawork-mode>active</ultrawork-mode>"


def is_planner(agent: str) -> bool:
    a = agent.lower()
    if "prometheus" in a or "planner" in a:
        return True
    return bool(re.search(r"\bplan\b", re.sub(r"[_-]+", " ", a)))


def source_for(model: str) -> str:
    return "gpt" if "gpt" in model.lower() else "default"


def load(name: str) -> str:
    try:
        with open(os.path.join(MODES_DIR, name), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def state_path(session_id: str):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    return os.path.join(STATE_DIR, safe) if safe else None


def read_state(session_id: str):
    path = state_path(session_id)
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def write_state(session_id: str, source: str) -> None:
    path = state_path(session_id)
    if not path:
        return
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        entries = sorted(
            (os.path.join(STATE_DIR, n) for n in os.listdir(STATE_DIR)),
            key=os.path.getmtime,
        )
        while len(entries) >= SESSION_CAP and path not in entries:
            os.remove(entries.pop(0))
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
    except OSError as err:
        sys.stderr.write(f"[keyword-detector] could not persist ultrawork state: {err}\n")


def clear_state(session_id: str) -> None:
    path = state_path(session_id)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError as err:
            sys.stderr.write(f"[keyword-detector] could not clear ultrawork state: {err}\n")


def main() -> int:
    agent = sys.argv[1] if len(sys.argv) > 1 else ""
    model = sys.argv[2] if len(sys.argv) > 2 else ""
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    prompt = event.get("prompt") or ""
    session_id = str(event.get("session_id") or "")

    if SLASH_COMMAND.match(prompt):
        if STOP_CONTINUATION.match(prompt):
            clear_state(session_id)
        return 0
    if is_planner(agent):
        return 0

    text = INLINE_CODE.sub("", CODE_BLOCK.sub("", prompt))
    source = source_for(model)
    explicit = bool(ULTRAWORK.search(text))
    active = read_state(session_id) if session_id else None
    if not explicit and active is None:
        return 0

    message = load("ultrawork-gpt.md" if source == "gpt" else "ultrawork.md")
    if not message:
        return 0
    if message in prompt:  # already injected
        return 0

    # Full directive on first activation (or when the model family changed), compact marker afterwards.
    output = CONTINUATION_MARKER if active == source else message
    sys.stdout.write(output + "\n")
    if session_id:
        write_state(session_id, source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
