---
name: srma-screen
description: AI-assisted title/abstract screening of database search exports (.ris/.nbib) for a systematic review / meta-analysis. Generates screening criteria from the protocol, parses and deduplicates citation records, dual-pass screens every record (include/maybe/exclude with reason codes) via parallel batch subagents, and produces PRISMA-ready results plus a Rayyan-compatible .ris of survivors. Use when the user wants to screen search results, before extraction.
---

# SRMA Screening (Claude Code adapter)

The canonical workflow lives in `prompts/screening-orchestrator.md` at the project root. **Read that file first and execute it in PARALLEL mode.** This adapter only adds the Claude Code mechanics:

- **Phase S-A**: read protocol files with the Read tool; confirm the generated `screening/criteria.json` with the user (AskUserQuestion or plain review) before any screening.
- **Phase S-B**: run `python3 scripts/parse_citations.py` via Bash; relay the printed PRISMA counts.
- **Phase S-C**: spawn `srma-screener` agents via the Agent tool (project-scoped definition at `.claude/agents/srma-screener.md`). One agent per batch-pass; launch each wave (≤5 agents) in a single message; wait for the wave before the next. Give every agent **absolute** paths (batch file, `screening/criteria.json`, output `screening/decisions/<batch-stem>_<pass>.json`) and its pass label `A` or `B`. Never tell an agent anything about the other pass's verdicts.
- **Validation**: `python3 -m json.tool` on each decisions file via Bash; retry a failed batch-pass once, then let the merge error listing drive further retries.
- **Phase S-D**: run `python3 scripts/merge_screening.py` via Bash and deliver the summary described in the orchestrator.

All rules in `prompts/screening-orchestrator.md` (criteria confirmation, pass independence, resume/skip, title/abstract only, human reviews maybes) apply verbatim.
