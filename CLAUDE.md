# SRM Assistant — Claude Code notes

SRMA data extraction harness. See `AGENTS.md` for the layout and conventions, `README.md` for the human-facing overview. The canonical workflow logic is in `prompts/orchestrator.md` and `prompts/extractor.md` — treat those as the source of truth; the Claude files below are adapters.

- Run `/srma-screen` for title/abstract screening (dual-pass, one `srma-screener` subagent per batch-pass) and `/srma-extract` for data extraction (one `srma-data-extractor` subagent per PDF). Waves of ≤5 parallel agents.
- Project-scoped agents live in `.claude/agents/` with `model: inherit` — they run on whatever model the session uses. Pin an explicit `model:` there to fix quality/cost independent of the session model.
- Scripts (all stdlib only): `python3 scripts/parse_citations.py`, `scripts/merge_screening.py`, `scripts/merge_extractions.py`.
- Never edit files in `prompts/` for a Claude-specific need — put Claude mechanics in the skill or agent adapter so the prompts stay tool-agnostic.
