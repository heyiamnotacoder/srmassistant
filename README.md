# SRM Assistant

An LLM-agnostic harness for **systematic reviews and meta-analyses (SRMA)**: title/abstract screening of database search results, then structured data extraction from the surviving PDFs.

```
STAGE 1 — SCREENING                      STAGE 2 — EXTRACTION
database exports (.ris / .nbib)          protocol docs (PICO / PROSPERO / template)
        │                                        │
        ▼                                        ▼
  parse + dedupe + batch                   JSON extraction schema ←— you confirm it
  (scripts/parse_citations.py)                   │
        │                                        ▼
        ▼                                  one extraction agent per PDF
  screening criteria ←— you confirm        each → extractions/<paper>.json
        │                                  with per-field confidence
        ▼                                        │
  DUAL-PASS screening: every batch               ▼
  judged by 2 independent agents           merge_extractions.py
  agree → verdict; disagree → maybe              │
        │                                        ▼
        ▼                                  extraction_sheet.csv (RevMan/R-ready)
  merge_screening.py                       confidence_report.csv
        │                                  missing_data_report.md
        ▼
  screening_results.csv + PRISMA counts
  included_maybe.ris  ──→ retrieve PDFs ──→ papers/ (feeds Stage 2)
```

The workflow logic lives in plain markdown under `prompts/` — so **any capable LLM can run it**: Claude, GPT, Gemini, or whatever comes next. Vendor-specific files are thin adapters.

## Requirements

- Python 3 (standard library only — no packages) for the merge step.
- An LLM that can read PDFs (natively/visually is best — that also covers scanned PDFs without OCR software).

## Quickstart

**1. Drop your files in:**
- `protocol/` — PROSPERO application, PICO notes, and/or an existing extraction sheet template (its columns become the schema).
- `screening/exports/` — database search exports (`.ris` from Embase/Scopus/WoS/CENTRAL, `.nbib` from PubMed) if you want AI-assisted screening.
- `papers/` — the PDFs for extraction (descriptive names, e.g. `smith_2023.pdf`). If you screened first, these are the include/maybe survivors.

**2. Run the workflows with your tool of choice:**

### Claude Code
```
/srma-screen     # Stage 1: screen titles/abstracts (skip if you screened in Rayyan)
/srma-extract    # Stage 2: extract data from PDFs
```
Both run with parallel subagents (project agents ship in `.claude/agents/`, `model: inherit` so they use whatever model you run).

### Other agentic CLIs (Codex, Gemini CLI, Cursor, aider, ...)
These pick up `AGENTS.md` automatically. Just ask:
> Run the SRMA screening workflow in prompts/screening-orchestrator.md
> Run the SRMA extraction workflow in prompts/orchestrator.md

Tools without subagents use the workflows' **sequential mode** (one unit of work at a time, fresh context each) — same outputs, just not parallel.

### Chat UIs (ChatGPT, Gemini, Claude web)
No file access needed — you drive it manually. Screening: run `python3 scripts/parse_citations.py` locally, then one chat per batch-pass (paste `prompts/screener.md`, attach `criteria.json` + the batch file, save the returned JSON into `screening/decisions/`), then `python3 scripts/merge_screening.py`. Extraction: one chat for the schema (Phase A of `prompts/orchestrator.md` + protocol docs), then one chat per paper (`prompts/extractor.md` + schema + ONE PDF → save JSON to `extractions/`), then `python3 scripts/merge_extractions.py`.

**3. Review the outputs:**
- Screening: `screening/screening_report.md` — PRISMA counts, A/B conflicts, low-confidence excludes to spot-check; import `screening/included_maybe.ris` into Rayyan/EndNote/Zotero for full-text retrieval.
- Extraction: `output/missing_data_report.md` — papers under 0.70 confidence are flagged for mandatory human verification, and every value carries a source pin (e.g. "Table 2, p.5") so spot-checking is fast.

## Why batches for screening? (cost vs context rot)

One agent per record would mean thousands of agent spawns for a typical search (slow, expensive). One agent screening everything degrades silently as its context fills with hundreds of abstracts ("context rot"). A title+abstract is only ~300 tokens, so the sweet spot is **one agent per batch of ~40 records** — a 2,000-record search becomes ~50 fresh-context batch runs per pass instead of 2,000, with no batch ever near context limits. Dual-pass (every batch judged twice, independently; disagreements demoted to `maybe`) mirrors Cochrane dual screening and catches individual judgment slips.

## Why per-paper JSON files?

Parallel extractors writing to one shared CSV corrupt each other. One JSON per paper means no write conflicts, cheap single-paper retries (delete the JSON, re-run — everything else is skipped), and a deterministic merge you can re-run any time.

## Data integrity rules

- Screening errs toward inclusion: ambiguous or abstract-less records become `maybe`, never `exclude`; every exclude carries a PRISMA reason code; screeners see title/abstract only (no full-text peeking, no web lookups).
- AI screening is a screening aid — humans review the maybes, spot-check excludes, and report its use in the methods section.
- Values are extracted **exactly as reported** — derived values (e.g., SD from SE) are flagged with the formula used.
- `NR` (not reported) vs `NA` (not applicable) — never blank, never guessed.
- ITT data by default; tables trump text trump abstract when sources conflict.
- Extraction sheet cells stay clean (no annotations) — notes and flags live in the missing-data report.

## License

MIT — see [LICENSE](LICENSE).

## What's tracked in git

The harness only. Papers (copyrighted), protocol documents, schemas, extractions, and outputs are gitignored — your review data never leaves your machine.
