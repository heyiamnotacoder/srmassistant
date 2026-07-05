---
name: srma-extract
description: Orchestrate structured data extraction from research paper PDFs for a systematic review / meta-analysis. Generates a JSON extraction schema from the review protocol (PICO, PROSPERO, extraction template), spawns one srma-data-extractor agent per PDF in parallel, then merges results into an extraction sheet with confidence and missing-data reports. Use when the user wants to start or continue an SRMA extraction batch.
---

# SRMA Extraction (Claude Code adapter)

The canonical workflow lives in `prompts/orchestrator.md` at the project root. **Read that file first and execute it in PARALLEL mode.** This adapter only adds the Claude Code mechanics:

- **Phase A**: read protocol files with the Read tool (it renders PDFs natively). Confirm the generated schema with the user via AskUserQuestion (or plain review) before any extraction.
- **Phase B (parallel mode)**: spawn `srma-data-extractor` agents via the Agent tool — the project-scoped definition at `.claude/agents/srma-data-extractor.md` is picked up automatically. Launch each batch (≤5 agents) in a single message so they run in parallel; wait for the batch before launching the next. Give every agent **absolute** paths: its one PDF, `schema/extraction_schema.json`, and `extractions/<pdf-stem>.json`.
- **Validation**: check each output with `python3 -m json.tool` via Bash; retry a failed paper once, then flag it.
- **Phase C**: run `python3 scripts/merge_extractions.py` via Bash from the project root and deliver the run summary described in the orchestrator.

All rules in `prompts/orchestrator.md` (schema confirmation, resume/skip, one review at a time, never editing extracted values) apply verbatim.
