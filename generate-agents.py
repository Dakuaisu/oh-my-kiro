#!/usr/bin/env python3
"""Generates ~/.kiro/agents/*.json for oh-my-kiro (port of oh-my-opencode). Re-runnable."""
import json
import os

HOME = os.path.expanduser("~")
AGENTS_DIR = f"{HOME}/.kiro/agents"
PROMPTS = f"{HOME}/.kiro/prompts/oh-my-kiro"
HOOKS = f"{HOME}/.kiro/hooks/oh-my-kiro"

READ_TOOLS = ["read", "grep", "glob", "code"]
WEB_TOOLS = ["web_search", "web_fetch"]
SPECIALISTS = ["explore", "librarian", "oracle", "multimodal-looker"]


def kw_hook(agent):
    return {"userPromptSubmit": [{"command": f"{HOOKS}/keyword-detector.py {agent}", "timeout_ms": 5000,
                                  "max_output_size": 32768}]}


def agent(name, description, model, tools, allowed, settings=None, hooks=None, shortcut=None, welcome=None,
          prompt_file=None):
    cfg = {
        "name": name,
        "description": description,
        "model": model,
        "prompt": f"file://{PROMPTS}/{prompt_file or name}.md",
        "tools": tools,
        "allowedTools": allowed,
    }
    if settings:
        cfg["toolsSettings"] = settings
    if hooks:
        cfg["hooks"] = hooks
    if shortcut:
        cfg["keyboardShortcut"] = shortcut
    if welcome:
        cfg["welcomeMessage"] = welcome
    return cfg


READONLY_SHELL = {"shell": {"autoAllowReadonly": True}}

configs = [
    # ---- primary (user-facing) agents ----
    agent(
        "sisyphus",
        "OmO primary orchestrator. Plans, delegates to specialists in parallel, verifies, keeps going until done. Say 'ulw' for ultrawork mode.",
        "claude-opus-4.5",
        READ_TOOLS + ["write", "shell", "subagent", "todo_list"] + WEB_TOOLS,
        READ_TOOLS + ["todo_list"],
        {
            **READONLY_SHELL,
            "crew": {
                "availableAgents": SPECIALISTS + ["sisyphus-junior", "cat-*", "metis", "momus"],
                "trustedAgents": SPECIALISTS + ["metis", "momus"],
            },
        },
        kw_hook("sisyphus"),
        shortcut="ctrl+shift+s",
        welcome="Sisyphus ready. Include 'ultrawork' / 'ulw' for maximum-effort mode.",
    ),
    agent(
        "atlas",
        "OmO master orchestrator. Executes a .sisyphus/plans/*.md work plan by delegating every task to category/specialist agents and verifying each result.",
        "claude-opus-4.5",
        READ_TOOLS + ["write", "shell", "subagent", "todo_list"],
        READ_TOOLS + ["todo_list"],
        {
            **READONLY_SHELL,
            "crew": {
                "availableAgents": SPECIALISTS + ["sisyphus-junior", "cat-*", "momus"],
                "trustedAgents": SPECIALISTS + ["momus"],
            },
        },
        kw_hook("atlas"),
        shortcut="ctrl+shift+a",
        welcome="Atlas ready. Point me at a plan in .sisyphus/plans/ to execute it.",
    ),
    agent(
        "prometheus",
        "OmO strategic planner. Interviews you, consults Metis/Momus, writes work plans to .sisyphus/plans/*.md. Never implements.",
        "claude-opus-4.5",
        READ_TOOLS + ["write", "subagent", "todo_list"] + WEB_TOOLS,
        READ_TOOLS + ["todo_list"],
        {
            "write": {"allowedPaths": ["./.sisyphus/**/*.md", "**/.sisyphus/**/*.md"]},
            "crew": {
                "availableAgents": ["explore", "librarian", "oracle", "metis", "momus"],
                "trustedAgents": ["explore", "librarian", "oracle", "metis", "momus"],
            },
        },
        {
            **kw_hook("prometheus"),
            "preToolUse": [{"matcher": "write", "command": f"{HOOKS}/prometheus-md-only.py", "timeout_ms": 5000}],
        },
        shortcut="ctrl+shift+p",
        welcome="Prometheus (planner). Describe what you want built; I'll interview you and write a plan.",
    ),
    # ---- specialists ----
    agent(
        "oracle",
        "Read-only high-IQ consultant for hard debugging, architecture decisions, and self-review after significant work.",
        "gpt-5.6-sol",
        READ_TOOLS,
        READ_TOOLS,
    ),
    agent(
        "librarian",
        "External reference researcher: official docs, open-source implementations, GitHub code, library internals. Returns cited evidence.",
        "glm-5",
        READ_TOOLS + ["shell"] + WEB_TOOLS,
        READ_TOOLS + WEB_TOOLS,
        READONLY_SHELL,
    ),
    agent(
        "explore",
        "Fast contextual grep for the local codebase. Answers 'where is X / how is Y wired' with absolute paths.",
        "claude-haiku-4.5",
        READ_TOOLS,
        READ_TOOLS,
    ),
    agent(
        "multimodal-looker",
        "Analyzes images, screenshots, diagrams and documents and returns the extracted information.",
        "claude-haiku-4.5",
        ["read", "glob"],
        ["read", "glob"],
    ),
    agent(
        "metis",
        "Pre-planning consultant. Finds hidden intent, ambiguities, missing guardrails and AI-slop risks before a plan is written.",
        "claude-opus-4.5",
        READ_TOOLS,
        READ_TOOLS,
    ),
    agent(
        "momus",
        "Ruthless work-plan reviewer. Verifies a plan is executable and references are valid; returns OKAY or REJECT with fixes.",
        "gpt-5.6-sol",
        READ_TOOLS,
        READ_TOOLS,
    ),
    agent(
        "sisyphus-junior",
        "Focused executor. Implements one delegated task end-to-end, verifies it, never delegates.",
        "claude-sonnet-4.5",
        READ_TOOLS + ["write", "shell", "todo_list"],
        READ_TOOLS + ["todo_list"],
        READONLY_SHELL,
    ),
]

# ---- category agents (sisyphus-junior + category prompt-append) ----
CATEGORIES = {
    "visual-engineering": ("claude-sonnet-4.5", "Frontend, UI/UX, design, styling, animation"),
    "ultrabrain": ("gpt-5.6-sol", "Deep logical reasoning, complex architecture decisions requiring extensive analysis"),
    "artistry": ("claude-opus-4.5", "Highly creative/artistic tasks, novel ideas"),
    "quick": ("claude-haiku-4.5", "Trivial tasks - single file changes, typo fixes, simple modifications"),
    "unspecified-low": ("claude-sonnet-4.5", "Tasks that don't fit other categories, low effort required"),
    "unspecified-high": ("claude-opus-4.5", "Tasks that don't fit other categories, high effort required"),
    "writing": ("claude-sonnet-4.5", "Documentation, prose, technical writing"),
}
for cat, (model, desc) in CATEGORIES.items():
    configs.append(
        agent(
            f"cat-{cat}",
            f"Category worker ({cat}): {desc}.",
            model,
            READ_TOOLS + ["write", "shell", "todo_list"],
            READ_TOOLS + ["todo_list"],
            READONLY_SHELL,
        )
    )

os.makedirs(AGENTS_DIR, exist_ok=True)
for cfg in configs:
    path = f"{AGENTS_DIR}/{cfg['name']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(path)
