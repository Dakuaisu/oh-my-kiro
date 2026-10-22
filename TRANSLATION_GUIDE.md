# Translation guide: oh-my-opencode prompt -> kiro-cli prompt

Source: the oh-my-opencode TypeScript sources (src/) at upstream commit aead4ae of https://github.com/opensoft/oh-my-opencode. Browse https://github.com/opensoft/oh-my-opencode/tree/aead4ae/src or fetch that commit into /tmp; never copy them into this repo.
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
- No skills system, no `load_skills`, no slash commands like /start-work (tell the user to switch to the
  atlas agent: `/agent swap atlas` or ctrl+shift+a, then say "execute .sisyphus/plans/<name>.md").
- No comment-checker, no todo-continuation enforcer injected by the system. The agent itself must hold
  the discipline ("never end your turn with incomplete todos").
- Mode keywords (ultrawork/ulw, search, analyze) are injected by a userPromptSubmit hook as context.

## Tool name mapping
| omo | kiro |
|---|---|
| delegate_task(category="X", ...) | subagent stage with role="cat-X" |
| delegate_task(subagent_type="explore"/agent="explore") / call_omo_agent | subagent stage with role="explore" (same for librarian, oracle, metis, momus, multimodal-looker) |
| delegate_task(..., run_in_background=true / background=true) | parallel stages in a single subagent call |
| background_output / background_cancel / session_id | remove; explain results come back when the subagent call returns |
| load_skills=[...] | remove |
| todowrite / todoread / TodoWrite | todo_list |
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
- explore (claude-haiku-4.5) — fast contextual grep of the local codebase. Cheap. Fire liberally, several in parallel.
- librarian (glm-5) — external docs / OSS / GitHub research with citations. Cheap.
- oracle (gpt-5.6-sol) — read-only high-IQ consultant: architecture, hard debugging (after 2+ failed fixes), self-review. Expensive.
- multimodal-looker (claude-haiku-4.5) — images/PDFs/diagrams analysis.
- metis (claude-opus-4.5) — pre-planning gap analysis.
- momus (gpt-5.6-sol) — plan reviewer, OKAY/REJECT.
Workers:
- sisyphus-junior (claude-sonnet-4.5) — focused executor, never delegates.
Category workers (sisyphus-junior + category mindset):
- cat-visual-engineering (claude-sonnet-4.5): Frontend, UI/UX, design, styling, animation
- cat-ultrabrain (gpt-5.6-sol): Deep logical reasoning, complex architecture decisions requiring extensive analysis
- cat-artistry (claude-opus-4.5): Highly creative/artistic tasks, novel ideas
- cat-quick (claude-haiku-4.5): Trivial tasks - single file changes, typo fixes, simple modifications (LESS CAPABLE MODEL: prompts must be exhaustively explicit with MUST DO / MUST NOT DO / EXPECTED OUTPUT)
- cat-unspecified-low (claude-sonnet-4.5): Tasks that don't fit other categories, low effort required
- cat-unspecified-high (claude-opus-4.5): Tasks that don't fit other categories, high effort required
- cat-writing (claude-sonnet-4.5): Documentation, prose, technical writing
Orchestrators (user-facing, not spawnable): sisyphus (main), atlas (plan executor), prometheus (planner).

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
