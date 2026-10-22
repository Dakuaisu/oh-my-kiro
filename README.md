# oh-my-kiro

Multi-agent orchestration for [kiro-cli](https://kiro.dev): the agents, model routing, delegation and `ultrawork` mode of [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) (formerly oh-my-opencode), rebuilt on kiro-cli's native agent configs, `subagent` tool and hooks.

You talk to **Sisyphus**. Sisyphus plans, fans work out to cheaper specialist agents in parallel, verifies what comes back, and keeps going until the todo list is empty. Type `ulw` in your prompt and it goes all in.

## Install

Requires `kiro-cli` and `python3`.

```bash
git clone https://github.com/Dakuaisu/oh-my-kiro.git
cd oh-my-kiro
./install.sh --default   # --default makes sisyphus the agent plain `kiro-cli` starts with
```

The installer copies prompts and hooks into `~/.kiro` (replacing any previous oh-my-kiro prompts), generates the agent configs in `~/.kiro/agents/`, and validates each one. It is safe to re-run after pulling updates. `--trust` is accepted for scripted runs; the installer never prompts.

## Usage

```bash
kiro-cli                                  # starts sisyphus if installed with --default
kiro-cli chat --agent sisyphus            # otherwise
> ulw add pagination to the /users endpoint and make the tests pass
```

Switch agents inside a session with `/agent swap <name>` or the shortcuts below. For goal-in, result-out work on a GPT model, use **Hephaestus** (`ctrl+shift+h`): it explores, implements and verifies end-to-end on its own and delegates only research and category work.

### Plan → execute workflow

1. `ctrl+shift+p` → **Prometheus** interviews you and writes a plan to `.sisyphus/plans/<name>.md`.
2. `ctrl+shift+a` → **Atlas**: `execute .sisyphus/plans/<name>.md`. Atlas delegates each task, verifies it, and ticks the plan's checkboxes.

For long unattended runs, combine with kiro's `/goal <description> --max N`, which re-prompts until the goal is verifiably done.

## Keywords

Detected by a `userPromptSubmit` hook in sisyphus, hephaestus and atlas. Text inside code blocks/backticks and prompts starting with a slash command are ignored.

| Keyword | Effect |
|---|---|
| `ultrawork` / `ulw` | Maximum-effort mode: certainty before implementation, a written work breakdown, parallel delegation, scenario-based manual QA, no stopping with open todos. `ulw-*` names such as `ulw-plan` do not trigger it. Hephaestus gets the GPT variant. |

Ultrawork is sticky: after the first trigger, every later prompt in the same session carries a compact `<ultrawork-mode>active</ultrawork-mode>` marker. `/stop-continuation` ends it. Prometheus never receives ultrawork (it is already the planner).

## Agents

| Agent | Model | Role |
|---|---|---|
| `sisyphus` (ctrl+shift+s) | claude-opus-5.5 | Main orchestrator |
| `hephaestus` (ctrl+shift+h) | gpt-5.6-sol | Autonomous deep worker: takes a goal end-to-end, delegates research/category work |
| `atlas` (ctrl+shift+a) | claude-sonnet-5 | Executes `.sisyphus/plans/*.md` by delegating every task |
| `prometheus` (ctrl+shift+p) | claude-opus-5.5 | Planner; can only write `.md` under `.sisyphus/` (enforced by hook) |
| `oracle` | gpt-5.6-sol | Read-only consultant: architecture, hard debugging, self-review |
| `librarian` | gpt-5.6-luna | External docs / OSS / GitHub research with citations |
| `explore` | gpt-5.6-luna | Fast local codebase search |
| `multimodal-looker` | gpt-5.6-sol | Images, screenshots, PDFs, diagrams |
| `metis` | claude-opus-5.5 | Pre-planning gap analysis |
| `momus` | claude-opus-5.5 | Plan reviewer (OKAY / REJECT) |
| `sisyphus-junior` | claude-sonnet-5 | Focused executor, never delegates |

Category workers (sisyphus-junior plus a category mindset), picked by the orchestrators per task:

| Agent | Model | For |
|---|---|---|
| `cat-quick` | gpt-5.6-luna | Trivial single-file changes |
| `cat-unspecified-low` | claude-sonnet-5.5 | Moderate, contained work |
| `cat-unspecified-high` | claude-opus-5.5 | Substantial multi-module work |
| `cat-ultrabrain` | gpt-5.6-sol | Genuinely hard, logic-heavy problems |
| `cat-deep-low` | gpt-5.6-sol | Default deep lane: one goal, decisions settleable from the code |
| `cat-deep-high` | gpt-5.6-sol | Escalation deep lane: a decision evidence cannot settle |
| `cat-visual-engineering` | claude-opus-5.5 | Frontend, UI/UX, design systems |
| `cat-artistry` | claude-opus-5.5 | Unconventional, creative problem-solving |
| `cat-writing` | claude-opus-5.5 | Docs and prose |

Models follow upstream's model chains: the first rung kiro-cli offers, otherwise kiro's closest model in the first rung's family (e.g. upstream's GPT-6 ultrabrain and deep-high run on gpt-5.6-sol, and haiku/luna-class lanes run on gpt-5.6-luna). To change a model, edit `CATEGORIES` / the `agent(...)` entries in `generate-agents.py` and re-run `./install.sh`.

## Permissions

Each agent auto-approves only read-only tools (`read`, `grep`, `glob`, `code`, `todo_list`; librarian also `web_search` / `web_fetch`). Writes and non-read-only shell commands prompt for approval, including inside subagents. `/tools trust-all` in the parent session is inherited by subagents it spawns.

## Differences from oh-my-openagent

kiro-cli is not a plugin runtime, so some features are approximated or absent:

- **Delegation** uses kiro's `subagent` tool: parallel stages in one blocking call. No background tasks, no resuming a subagent session, and subagents cannot spawn subagents.
- **Todo continuation** ("the boulder") is a standing prompt rule, not a system-enforced loop. Use `/goal` for enforcement.
- **No Gemini/Grok/Kimi/GLM** prompt variants or models; each agent gets the upstream prompt variant for the Claude or GPT model it runs on.
- **Plans stay in `.sisyphus/`.** Upstream moved plans to `.omo/`; this port keeps `.sisyphus/plans`, `.sisyphus/drafts` and `.sisyphus/notepads`.
- **Prometheus keeps its full interview prompt.** Upstream's Prometheus now only loads the `ulw-plan` skill; kiro-cli has no skills.
- **Not ported:** skills (ulw-plan, ulw-execute, git-master, browser, ...), `team mode` / `hyperplan` keywords (need team tools and skills), plan-agent delegation, Atlas/todo continuation hooks, comment-checker, provider fallback chains, OpenCode-specific LSP/AST tools (kiro's `code` tool covers symbol search, AST pattern search/rewrite and LSP operations).

## Layout

```
.
├── install.sh             # copy into ~/.kiro, generate + validate agents
├── generate-agents.py     # source of truth for agent configs (models, tools, hooks)
├── hooks/
│   ├── keyword-detector.py    # ultrawork injection (sticky per session)
│   └── prometheus-md-only.py  # blocks planner writes outside .sisyphus/**/*.md
├── prompts/               # system prompts, translated from upstream
│   └── modes/             # ultrawork directives (Claude and GPT variants)
└── TRANSLATION_GUIDE.md   # rules used to port prompts from upstream
```

The prompts track oh-my-openagent at commit `f52b4a2` (first ported from oh-my-opencode `aead4ae`); the plugin sources are not kept in this repo. TRANSLATION_GUIDE.md lists the upstream files each prompt comes from.

## Uninstall

```bash
kiro-cli agent set-default kiro_default
rm -rf ~/.kiro/prompts/oh-my-kiro ~/.kiro/hooks/oh-my-kiro
cd ~/.kiro/agents && rm -f sisyphus.json hephaestus.json atlas.json prometheus.json oracle.json librarian.json \
  explore.json multimodal-looker.json metis.json momus.json sisyphus-junior.json cat-*.json
```

## Credits and license

oh-my-kiro is a port of [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) (formerly oh-my-opencode) by [@code-yeongyu](https://github.com/code-yeongyu). Agent designs and prompts derive from that project and remain under its [Sustainable Use License](LICENSE.md).
