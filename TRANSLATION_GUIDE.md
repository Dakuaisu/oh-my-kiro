# Translation guide: oh-my-opencode prompt -> kiro-cli prompt

Source: upstream https://github.com/code-yeongyu/oh-my-openagent at commit f52b4a2 (a monorepo; never copy its sources into this repo):
- agent prompts: packages/omo-opencode/src/agents/ (per-model variants live in sisyphus/, sisyphus-junior/, hephaestus/; single-file agents branch on model inside the file)
- markdown prompts: packages/prompts-core/prompts/ (atlas/, ultrawork/)
- categories and prompt appends: packages/omo-opencode/src/tools/delegate-task/{openai,google,kimi}-categories.ts
- model chains: packages/model-core/src/{agent,category}-model-requirements.ts
The port was first translated from https://github.com/opensoft/oh-my-opencode at aead4ae (src/ layout); update existing prompts in place from the diff between the two, do not re-translate from scratch.
Variant rule: port the variant upstream itself selects for the kiro model the agent runs on (e.g. sisyphus on claude-opus-5.5 -> sisyphus/claude-opus-5.ts; oracle on gpt-5.6-sol -> the GPT-5.5 prompt in oracle.ts). Skip Gemini/Grok/Kimi/GLM variants.
Output dir: ~/.kiro/prompts/oh-my-kiro/ (source: prompts/ in this repo) (markdown files).

## Goal
Produce the FINAL rendered system prompt text (not TypeScript) for a kiro-cli agent.
Preserve the original prompt's content, structure, tone, rules and headings as faithfully as possible.
Only change what is required for the kiro-cli runtime. Do not summarize or shorten.
If a prompt is assembled dynamically (template literals, builder functions in
src/agents/dynamic-agent-prompt-builder.ts), render it using the kiro agent roster below
as the "available agents/categories" input.

## kiro-cli runtime facts
- Built-in tools: read (files/dirs/images), write (create/strReplace/insert), shell, grep, glob,
  code (search_symbols, lookup_symbols, get_document_symbols, pattern_search, pattern_rewrite = AST-grep;
  LSP ops goto_definition/find_references/rename_symbol/get_diagnostics when LSP is initialized),
  web_search, web_fetch, todo_list (create/complete/add/remove/list), subagent.
- Delegation = the `subagent` tool. Call shape:
  subagent(task="<overall>", stages=[{name, role, prompt_template, depends_on?, model?}])
  * role = agent name from the roster. Stages without depends_on run IN PARALLEL.
  * The call is BLOCKING: it returns all stage results at once. There is no background mode,
    no background_output / background_cancel, no session_id resume. To "fire in background and
    continue", put all independent stages in ONE subagent call.
  * Subagents cannot spawn further subagents. Subagents report back via their mandatory `summary` tool.
  * Each subagent starts with fresh context: prompt_template must be self-contained.
- No skills system, no `load_skills` / `skill` tool, no slash commands like /start-work or /ulw-execute (tell the
  user to switch to the atlas agent: `/agent swap atlas` or ctrl+shift+a, then say "execute .sisyphus/plans/<name>.md").
- No task system (task_create/task_update/task_id): use todo_list. No apply_patch: use write (strReplace).
- No comment-checker, no todo-continuation enforcer injected by the system. The agent itself must hold
  the discipline ("never end your turn with incomplete todos").
- The ultrawork keyword (ultrawork/ulw) is injected by a userPromptSubmit hook as context (full directive on first
  use in a session, then a compact `<ultrawork-mode>active</ultrawork-mode>` marker). There are no search/analyze,
  team or hyperplan modes.

## Tool name mapping
| omo | kiro |
|---|---|
| delegate_task(category="X", ...) / task(category="X", ...) | subagent stage with role="cat-X" |
| delegate_task / task(subagent_type="explore"/agent="explore") / call_omo_agent | subagent stage with role="explore" (same for librarian, oracle, metis, momus, multimodal-looker) |
| delegate_task(..., run_in_background=true / background=true) | parallel stages in a single subagent call |
| background_output / background_cancel / session_id / task_id (`bg_...`, `ses_...`) | remove; explain results come back when the subagent call returns, and follow-ups are a NEW self-contained subagent call |
| load_skills=[...] | remove |
| todowrite / todoread / TodoWrite / task_create / task_update | todo_list |
| apply_patch / edit | write (strReplace) |
| skill(name=...) / /playwright etc. | remove (no skills); describe the action with available tools |
| Read / Write / Edit / Bash / Glob / Grep | read / write / write (strReplace) / shell / glob / grep |
| lsp_diagnostics | code get_diagnostics if available, otherwise run the project's typecheck/build/lint via shell |
| lsp_goto_definition / lsp_find_references / lsp_rename / lsp_symbols | code goto_definition / find_references / rename_symbol / search_symbols |
| ast_grep_search / ast_grep_replace | code pattern_search / pattern_rewrite |
| look_at | subagent role="multimodal-looker" (or read in Image mode) |
| webfetch / websearch / websearch_exa / context7_* / grep_app_* | web_fetch / web_search (for GitHub code search, web_search with site:github.com or clone with `gh repo clone` into /tmp via shell) |
| interactive_bash / tmux | shell |
| question tool | ask the user in plain text |

## kiro agent roster (use these names and models)
Specialists:
- explore (gpt-5.6-luna) — fast contextual grep of the local codebase. Cheap. Fire liberally, several in parallel.
- librarian (gpt-5.6-luna) — external docs / OSS / GitHub research with citations. Cheap.
- oracle (gpt-5.6-sol) — read-only high-IQ consultant: architecture, hard debugging (after 2+ failed fixes), self-review. Expensive.
- multimodal-looker (gpt-5.6-sol) — images/PDFs/diagrams analysis.
- metis (claude-opus-5.5) — pre-planning gap analysis.
- momus (claude-opus-5.5) — plan reviewer, OKAY/REJECT.
Workers:
- sisyphus-junior (claude-sonnet-5) — focused executor, never delegates.
Category workers (sisyphus-junior + category mindset):
- cat-visual-engineering (claude-opus-5.5): Visual design, UI/UX, frontend, styling, animation, and design systems
- cat-ultrabrain (gpt-5.6-sol): Use ONLY for genuinely hard, logic-heavy tasks. Give clear goals only, not step-by-step instructions
- cat-deep-low (gpt-5.6-sol): Default deep lane: one goal, one deliverable, decisions the child can settle from what it reads; preferred over deep-high for 3D graphics, computer/browser use, CAPTCHA, multimodal, backend, logic, and algorithm work. Multiple goals fan out as parallel stages. When unsure choose deep-low; a misrouted child returns `ESCALATE: deep-high` and you re-spawn the same brief as cat-deep-high with its findings
- cat-deep-high (gpt-5.6-sol): Escalation deep lane: a goal whose central decision cannot be settled from evidence alone (trade-off with no single right answer, contract change crossing a package/process boundary, mechanism with no in-repo pattern, correctness argued from invariants). Same one-goal, one-deliverable contract as deep-low
- cat-artistry (claude-opus-5.5): Complex problem-solving with unconventional, creative approaches - beyond standard patterns
- cat-quick (gpt-5.6-luna): Trivial tasks - single file changes, typo fixes, simple modifications (small/fast model: write an explicit prompt with numbered must-do steps, forbidden deviations, and concrete success criteria)
- cat-unspecified-low (claude-sonnet-5.5): Tasks that don't fit other categories, low effort required (only when no specialist fits and scope stays within a few files/modules)
- cat-unspecified-high (claude-opus-5.5): Tasks that don't fit other categories, high effort required (substantial effort across systems/modules)
- cat-writing (claude-opus-5.5): Documentation, prose, technical writing
Orchestrators (user-facing, not spawnable): sisyphus (main, claude-opus-5.5), hephaestus (autonomous deep worker, gpt-5.6-sol; may delegate to explore, librarian, oracle and cat-* only), atlas (plan executor, claude-sonnet-5), prometheus (planner, claude-opus-5.5).

Optional per-stage `model` override exists, but prefer picking the right role.

## Example delegation block to use in prompts
```
subagent(
  task="Add rate limiting to the API",
  stages=[
    {"name": "find-middleware", "role": "explore", "prompt_template": "Find where HTTP middleware is registered in this repo. Return absolute paths and a 1-line summary each."},
    {"name": "lib-docs", "role": "librarian", "prompt_template": "Find the official docs and a production OSS example for rate limiting with <library>. Cite URLs."}
  ]
)
```

## Output rules
- Write exactly the file(s) you were assigned with the `write` tool. Markdown, no TS, no backtick-escaping artifacts (`\``  -> `` ` ``).
- Keep `.sisyphus/plans/` and `.sisyphus/drafts/` conventions and `.sisyphus/notepads/` where present.
- Remove references to OpenCode/plugin internals, provider fallback chains, `variant`, temperature, thinking budget.
- Replace "Claude Code"/"OpenCode" product references with "kiro-cli" where they describe the runtime.
- After writing, re-read the file and grep it for leftover omo-only names:
  delegate_task|call_omo_agent|background_output|background_cancel|load_skills|todowrite|lsp_|ast_grep|look_at|session_id|run_in_background
  — there must be ZERO matches (except inside a sentence explicitly saying a thing does not exist, which you should avoid).
