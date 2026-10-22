[analyze-mode]
ANALYSIS MODE. Gather context before diving deep:

CONTEXT GATHERING (parallel — put independent stages in a single `subagent` call that returns all results at once):
- 1-2 explore subagents (codebase patterns, implementations)
- 1-2 librarian subagents (if external library involved — cite URLs)
- Direct tools: grep, the code tool's pattern_search (AST-grep) and symbol/reference lookups (search_symbols, find_references) for targeted searches

IF COMPLEX (architecture, multi-system, debugging after 2+ failures):
- Consult oracle for strategic guidance

SYNTHESIZE findings before proceeding.
