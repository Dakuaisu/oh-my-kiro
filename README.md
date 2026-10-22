# oh-my-kiro

Multi-agent orchestration for [kiro-cli](https://kiro.dev): the agents, model routing, delegation and `ultrawork` mode of [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode), rebuilt on kiro-cli's native agent configs, `subagent` tool and hooks.

You talk to **Sisyphus**. Sisyphus plans, fans work out to cheaper specialist agents in parallel, verifies what comes back, and keeps going until the todo list is empty. Type `ulw` in your prompt and it goes all in.

## Install

Requires `kiro-cli` and `python3`.

```bash
git clone https://github.com/Dakuaisu/oh-my-kiro.git
cd oh-my-kiro
./install.sh --default           # sisyphus becomes the agent plain `kiro-cli` starts with
./install.sh --default --trust   # same, plus no approval prompts (see Permissions)
```

The installer copies prompts and hooks into `~/.kiro`, generates the agent configs in `~/.kiro/agents/`, and validates each one. It is safe to re-run after pulling updates.

## Usage

```bash
kiro-cli                                  # starts sisyphus if installed with --default
kiro-cli chat --agent sisyphus            # otherwise
> ulw add pagination to the /users endpoint and make the tests pass
```

Switch agents inside a session with `/agent swap <name>` or the shortcuts below.

### Plan → execute workflow

1. `ctrl+shift+p` → **Prometheus** interviews you and writes a plan to `.sisyphus/plans/<name>.md`.
2. `ctrl+shift+a` → **Atlas**: `execute .sisyphus/plans/<name>.md`. Atlas delegates each task, verifies it, and ticks the plan's checkboxes.

For long unattended runs, combine with kiro's `/goal <description> --max N`, which re-prompts until the goal is verifiably done.

## Keywords

Detected by a `userPromptSubmit` hook in sisyphus, atlas and prometheus. Text inside code blocks/backticks is ignored.

| Keyword | Effect |
|---|---|
| `ultrawork` / `ulw` | Maximum-effort mode: parallel exploration, delegation, strict verification, no stopping with open todos. Prometheus gets a planner-only variant. |
| search words (`find`, `where is`, `search`, …) | Search mode: parallel explore + librarian stages. |
| analysis words (`why is`, `debug`, `analyze`, …) | Analyze mode: gather context in parallel, consult oracle when complex. |

Keywords are also matched in Korean, Japanese, Chinese and Vietnamese.

## Agents

| Agent | Model | Role |
|---|---|---|
| `sisyphus` (ctrl+shift+s) | claude-opus-5.5 | Main orchestrator |
| `atlas` (ctrl+shift+a) | claude-opus-4.5 | Executes `.sisyphus/plans/*.md` by delegating every task |
| `prometheus` (ctrl+shift+p) | claude-opus-4.5 | Planner; can only write `.md` under `.sisyphus/` (enforced by hook) |
| `oracle` | gpt-5.6-sol | Read-only consultant: architecture, hard debugging, self-review |
| `librarian` | glm-5 | External docs / OSS / GitHub research with citations |
| `explore` | claude-haiku-4.5 | Fast local codebase search |
| `multimodal-looker` | claude-haiku-4.5 | Images, screenshots, PDFs, diagrams |
| `metis` | claude-opus-4.5 | Pre-planning gap analysis |
| `momus` | gpt-5.6-sol | Plan reviewer (OKAY / REJECT) |
| `sisyphus-junior` | claude-sonnet-4.5 | Focused executor, never delegates |

Category workers (sisyphus-junior plus a category mindset), picked by the orchestrators per task:

| Agent | Model | For |
|---|---|---|
| `cat-quick` | claude-haiku-4.5 | Trivial single-file changes |
| `cat-unspecified-low` | claude-sonnet-4.5 | Moderate, contained work |
| `cat-unspecified-high` | claude-opus-4.5 | Substantial multi-module work |
| `cat-ultrabrain` | gpt-5.6-sol | Deep logic, hard architecture |
| `cat-visual-engineering` | claude-sonnet-4.5 | Frontend, UI/UX, styling |
| `cat-artistry` | claude-opus-4.5 | Highly creative work |
| `cat-writing` | claude-sonnet-4.5 | Docs and prose |

To change a model, edit `CATEGORIES` / the `agent(...)` entries in `generate-agents.py` and re-run `./install.sh`.

## Permissions

By default each agent auto-approves only read-only tools (`read`, `grep`, `glob`, `code`, `todo_list`; librarian also `web_search` / `web_fetch`). Writes and non-read-only shell commands prompt for approval, including inside subagents.

`./install.sh --trust` makes that permanent instead: every agent that has `write` / `shell` auto-approves them, and orchestrators spawn any subagent without asking. A deny-list still blocks `sudo`, `rm -rf` on `/` or `~`, `git push --force`, `git reset --hard`, `git clean -f`, `mkfs` and `dd` to devices, and Prometheus can still only write `.md` under `.sisyphus/`. Re-run `./install.sh` without `--trust` to restore prompts.

For a single session instead, use `kiro-cli chat --trust-all-tools` or `/tools trust-all` (subagents inherit it).

## Differences from oh-my-opencode

kiro-cli is not a plugin runtime, so some features are approximated or absent:

- **Delegation** uses kiro's `subagent` tool: parallel stages in one blocking call. No background tasks, no resuming a subagent session, and subagents cannot spawn subagents.
- **Todo continuation** ("the boulder") is a standing prompt rule, not a system-enforced loop. Use `/goal` for enforcement.
- **No Gemini/Grok** models in kiro-cli; visual/multimodal work runs on Claude.
- **Not ported:** skills (git-master, playwright), comment-checker, provider fallback chains, OpenCode-specific LSP/AST tools (kiro's `code` tool covers symbol search, AST pattern search/rewrite and LSP operations).

## Layout

```
├── install.sh             # copy into ~/.kiro, generate + validate agents
├── generate-agents.py     # source of truth for agent configs (models, tools, hooks)
├── hooks/
│   ├── keyword-detector.py    # ulw / search / analyze injection
│   └── prometheus-md-only.py  # blocks planner writes outside .sisyphus/**/*.md
├── prompts/               # system prompts, translated from upstream src/agents/*.ts
│   └── modes/             # keyword-mode directives
└── TRANSLATION_GUIDE.md   # rules used to port prompts from upstream
```

The prompts were ported from the oh-my-opencode TypeScript plugin at commit `aead4ae`; the plugin sources are not kept in this repo (browse them at https://github.com/opensoft/oh-my-opencode/tree/aead4ae/src).

## Uninstall

```bash
kiro-cli agent set-default kiro_default
rm -rf ~/.kiro/prompts/oh-my-kiro ~/.kiro/hooks/oh-my-kiro
cd ~/.kiro/agents && rm -f sisyphus.json atlas.json prometheus.json oracle.json librarian.json \
  explore.json multimodal-looker.json metis.json momus.json sisyphus-junior.json cat-*.json
```

## Credits and license

oh-my-kiro is a port of [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) by [@code-yeongyu](https://github.com/code-yeongyu). Agent designs and prompts derive from that project and remain under its [Sustainable Use License](LICENSE.md).
