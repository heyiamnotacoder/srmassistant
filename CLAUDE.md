# SRM Assistant — Claude Code notes

SRMA data extraction harness. See `AGENTS.md` for the layout and conventions, `README.md` for the human-facing overview. The canonical workflow logic is in `prompts/orchestrator.md` and `prompts/extractor.md` — treat those as the source of truth; the Claude files below are adapters.

- Run `/srma-extract` to start or continue an extraction batch (parallel mode: one subagent per PDF, batches of ≤5).
- The project-scoped extractor agent is `.claude/agents/srma-data-extractor.md` with `model: inherit` — it runs on whatever model the session uses. Pin an explicit `model:` there if you need to fix extraction quality/cost independent of the session model.
- Merge step: `python3 scripts/merge_extractions.py` (stdlib only).
- Never edit files in `prompts/` for a Claude-specific need — put Claude mechanics in the skill or agent adapter so the prompts stay tool-agnostic.
