# SRM Assistant — Agent Instructions

Harness for extracting structured data from research paper PDFs for systematic reviews and meta-analyses (SRMA). Works with any capable LLM agent — the workflow logic lives in plain-markdown prompts, not in any vendor's config format.

**To run an extraction batch**: follow `prompts/orchestrator.md` (protocol → user-confirmed JSON schema → one extraction per PDF → merge). Pick the Phase B mode matching your capabilities: parallel (subagents), sequential (single agent, fresh context per paper), or manual (human-driven chat UI).

**To extract a single paper**: follow `prompts/extractor.md` with three inputs — one PDF, `schema/extraction_schema.json`, output to `extractions/<pdf-stem>.json`.

**To merge results**: `python3 scripts/merge_extractions.py` from the project root (Python 3 stdlib only, no packages).

## Layout

| Path | Purpose |
|---|---|
| `prompts/` | Canonical, tool-agnostic workflow + extraction prompts (source of truth) |
| `protocol/` | Human drops PROSPERO application, PICO notes, and/or an extraction sheet template (CSV/XLSX) |
| `papers/` | PDFs for the current review batch |
| `schema/extraction_schema.json` | Generated schema — must be human-confirmed before extraction |
| `extractions/` | Per-paper JSON written by extractors (`<pdf-stem>.json`) |
| `output/` | Merged `extraction_sheet.csv`, `confidence_report.csv`, `missing_data_report.md` |
| `scripts/merge_extractions.py` | Deterministic merge + validation |
| `.claude/` | Claude Code adapters only (skill + project agent); other tools ignore this |

## Conventions

- One review at a time; archive or clear `papers/`, `schema/`, `extractions/`, `output/` before a new review.
- Missing values: `NR` (not reported) vs `NA` (not applicable) — never blank, never guessed.
- Every field gets a confidence score (0–1); papers with overall confidence < 0.70 require human verification.
- Extractors never write to shared files — one JSON per paper; the merge script is the only thing that aggregates.
- To re-run one paper: delete its `extractions/<pdf-stem>.json` and re-run the workflow (already-extracted papers are skipped).
