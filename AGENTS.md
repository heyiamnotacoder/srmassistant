# SRM Assistant — Agent Instructions

Harness for title/abstract screening and structured data extraction from research papers for systematic reviews and meta-analyses (SRMA). Works with any capable LLM agent — the workflow logic lives in plain-markdown prompts, not in any vendor's config format. All scripts are Python 3 stdlib only.

**Stage 1 — Screening** (database exports → include/maybe/exclude): follow `prompts/screening-orchestrator.md`. Human drops `.ris`/`.nbib` files in `screening/exports/`; `scripts/parse_citations.py` parses/dedupes/batches; every batch is screened twice independently per `prompts/screener.md` (dual-pass); `scripts/merge_screening.py` adjudicates and emits PRISMA-ready results + a Rayyan-compatible `.ris` of survivors.

**Stage 2 — Extraction** (PDFs → data sheet): follow `prompts/orchestrator.md` (protocol → user-confirmed JSON schema → one extraction per PDF per `prompts/extractor.md` → `scripts/merge_extractions.py`).

Both stages offer three execution modes — pick what your harness supports: parallel (subagents), sequential (single agent, fresh context per unit of work), or manual (human-driven chat UI).

## Layout

| Path | Purpose |
|---|---|
| `prompts/` | Canonical, tool-agnostic workflow + worker prompts (source of truth) |
| `protocol/` | Human drops PROSPERO application, PICO notes, and/or an extraction sheet template (CSV/XLSX) |
| `screening/exports/` | Human drops database search exports (`.ris`, `.nbib`) |
| `screening/` | Generated: criteria.json, records, batches, decisions, results, `included_maybe.ris` |
| `papers/` | PDFs for the current review batch (screening survivors) |
| `schema/extraction_schema.json` | Generated schema — must be human-confirmed before extraction |
| `extractions/` | Per-paper JSON written by extractors (`<pdf-stem>.json`) |
| `output/` | Merged `extraction_sheet.csv`, `confidence_report.csv`, `missing_data_report.md` |
| `scripts/` | `parse_citations.py`, `merge_screening.py`, `merge_extractions.py` (stdlib only) |
| `.claude/` | Claude Code adapters only (skills + project agents); other tools ignore this |

## Conventions

- One review at a time; archive or clear `screening/`, `papers/`, `schema/`, `extractions/`, `output/` before a new review.
- Screening verdicts err toward inclusion: ambiguity → `maybe`, never `exclude`; every exclude carries a PRISMA reason code; dual-pass disagreements demote to `maybe`. Screeners judge title/abstract only — no full-text or web lookups.
- Missing values: `NR` (not reported) vs `NA` (not applicable) — never blank, never guessed.
- Every field gets a confidence score (0–1); papers with overall confidence < 0.70 require human verification.
- Extractors never write to shared files — one JSON per paper; the merge script is the only thing that aggregates.
- To re-run one paper: delete its `extractions/<pdf-stem>.json` and re-run the workflow (already-extracted papers are skipped).
