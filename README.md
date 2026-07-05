# SRM Assistant

An LLM-agnostic harness for extracting structured data from research paper PDFs for **systematic reviews and meta-analyses (SRMA)**.

```
protocol docs (PICO / PROSPERO / extraction template)
        │
        ▼
  JSON extraction schema  ←— you confirm it before anything runs
        │
        ▼
  one extraction per PDF (parallel agents, or sequential, or manual chat)
  each produces extractions/<paper>.json with per-field confidence scores
        │
        ▼
  python3 scripts/merge_extractions.py
        │
        ▼
  output/extraction_sheet.csv        ←— clean values, ready for RevMan / R
  output/confidence_report.csv      ←— per-field 0–1 confidence
  output/missing_data_report.md     ←— NR fields, flags, papers needing human review
```

The workflow logic lives in plain markdown — `prompts/orchestrator.md` and `prompts/extractor.md` — so **any capable LLM can run it**: Claude, GPT, Gemini, or whatever comes next. Vendor-specific files are thin adapters.

## Requirements

- Python 3 (standard library only — no packages) for the merge step.
- An LLM that can read PDFs (natively/visually is best — that also covers scanned PDFs without OCR software).

## Quickstart

**1. Drop your files in:**
- `protocol/` — PROSPERO application, PICO notes, and/or an existing extraction sheet template (its columns become the schema).
- `papers/` — the PDFs for this review batch (descriptive names, e.g. `smith_2023.pdf`).

**2. Run the workflow with your tool of choice:**

### Claude Code
```
/srma-extract
```
That's it — the skill runs the full pipeline with one parallel subagent per PDF (project agent ships in `.claude/agents/`, `model: inherit` so it uses whatever model you run).

### Other agentic CLIs (Codex, Gemini CLI, Cursor, aider, ...)
These pick up `AGENTS.md` automatically. Just ask:
> Run the SRMA extraction workflow in prompts/orchestrator.md

Tools without subagents use the workflow's **sequential mode** (one paper at a time, fresh context per paper) — same outputs, just not parallel.

### Chat UIs (ChatGPT, Gemini, Claude web)
No file access needed — you drive it manually:
1. **Schema**: new chat → attach your protocol documents → paste Phase A of `prompts/orchestrator.md` → save the returned JSON as `schema/extraction_schema.json`.
2. **Per paper**: new chat → paste `prompts/extractor.md` → attach the schema + ONE PDF → save the returned JSON code block as `extractions/<pdf-name>.json`. (One chat per paper — don't mix papers.)
3. **Merge**: `python3 scripts/merge_extractions.py` → outputs land in `output/`.

**3. Review the outputs** — especially `output/missing_data_report.md`: papers with overall confidence below 0.70 are flagged for mandatory human verification, and every extracted value carries a source pin (e.g. "Table 2, p.5") so spot-checking is fast.

## Why per-paper JSON files?

Parallel extractors writing to one shared CSV corrupt each other. One JSON per paper means no write conflicts, cheap single-paper retries (delete the JSON, re-run — everything else is skipped), and a deterministic merge you can re-run any time.

## Data integrity rules

- Values are extracted **exactly as reported** — derived values (e.g., SD from SE) are flagged with the formula used.
- `NR` (not reported) vs `NA` (not applicable) — never blank, never guessed.
- ITT data by default; tables trump text trump abstract when sources conflict.
- Extraction sheet cells stay clean (no annotations) — notes and flags live in the missing-data report.

## What's tracked in git

The harness only. Papers (copyrighted), protocol documents, schemas, extractions, and outputs are gitignored — your review data never leaves your machine.
