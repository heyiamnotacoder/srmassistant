# SRM Assistant

An LLM-agnostic harness for **systematic reviews and meta-analyses (SRMA)**: develop and register the protocol, screen database search results, then extract structured data from the surviving PDFs.

```
STAGE 0 — PROTOCOL              STAGE 1 — SCREENING                STAGE 2 — EXTRACTION
your research question          database exports (.ris/.nbib)      the retrieved PDFs
        │                               │                                  │
        ▼                               ▼                                  ▼
  sharpen the question            parse + dedupe + batch            extraction schema
  (what kind of review?)          (parse_citations.py)              ←— you confirm it
        │                               │                            outcomes bound to
        ▼                               ▼                            the registered ones
  ELIGIBILITY CHECKLIST           DUAL-PASS screening:                     │
  every decision forced:          every batch judged by                    ▼
  designs (prospective?),         2 independent agents               one agent per PDF
  age bounds, comparator,         agree → verdict                    each → its own JSON
  outcomes + timepoints,          disagree → maybe                   with per-field
  language, dates, grey lit             │                            confidence
        │                               ▼                                  │
        ▼                         merge_screening.py                       ▼
  scoping search: how many              │                          merge_extractions.py
  records? which designs                ▼                                  │
  exist? is it feasible?          screening_results.csv                    ▼
        │                         + PRISMA counts                   extraction_sheet.csv
        ▼                         included_maybe.ris                 confidence_report.csv
  pico.json ────────────────────────────┴──→ retrieve PDFs ──→       missing_data_report.md
  prospero_draft.md                              papers/
  (paste-ready, field by field)
        │
        ▼
  you register → CRD number → registration.json
```

The workflow logic lives in plain markdown under `prompts/` — so **any capable LLM can run it**: Claude, GPT, Gemini, or whatever comes next. Vendor-specific files are thin adapters.

## Requirements

- Python 3 (standard library only — no packages) for the merge step.
- An LLM that can read PDFs (natively/visually is best — that also covers scanned PDFs without OCR software).

## Quickstart

**1. Start where you actually are.**

Most reviews start with a question, not a registration — a PROSPERO record is the *output* of protocol
development, not its input. So Stage 0 takes the question and produces the registration. If you already have
a registered protocol, skip Stage 0 and drop the record in `protocol/`.

Files you supply as you go:
- `protocol/` — an existing PROSPERO record and/or an extraction sheet template (its columns become the schema). Stage 0 writes the rest of this folder for you.
- `screening/exports/` — database search exports (`.ris` from Embase/Scopus/WoS/CENTRAL, `.nbib` from PubMed).
- `papers/` — the PDFs for extraction (descriptive names, e.g. `smith_2023.pdf`) — the include/maybe survivors of screening.

**2. Run the workflows with your tool of choice:**

### Claude Code
```
/srma-protocol   # Stage 0: question → decisions → paste-ready PROSPERO draft
/srma-screen     # Stage 1: screen titles/abstracts (skip if you screened in Rayyan)
/srma-extract    # Stage 2: extract data from PDFs
```
Both run with parallel subagents (project agents ship in `.claude/agents/`, `model: inherit` so they use whatever model you run).

### Other agentic CLIs (Codex, Gemini CLI, Cursor, aider, ...)
These pick up `AGENTS.md` automatically. Just ask:
> Run the SRMA protocol builder in prompts/protocol-builder.md
> Run the SRMA screening workflow in prompts/screening-orchestrator.md
> Run the SRMA extraction workflow in prompts/orchestrator.md

Tools without subagents use the workflows' **sequential mode** (one unit of work at a time, fresh context each) — same outputs, just not parallel.

### Chat UIs (ChatGPT, Gemini, Claude web)
No file access needed — you drive it manually. Screening: run `python3 scripts/parse_citations.py` locally, then one chat per batch-pass (paste `prompts/screener.md`, attach `criteria.json` + the batch file, save the returned JSON into `screening/decisions/`), then `python3 scripts/merge_screening.py`. Extraction: one chat for the schema (Phase A of `prompts/orchestrator.md` + protocol docs), then one chat per paper (`prompts/extractor.md` + schema + ONE PDF → save JSON to `extractions/`), then `python3 scripts/merge_extractions.py`.

**3. Review the outputs:**
- Screening: `screening/screening_report.md` — PRISMA counts, A/B conflicts, low-confidence excludes to spot-check; import `screening/included_maybe.ris` into Rayyan/EndNote/Zotero for full-text retrieval.
- Extraction: `output/missing_data_report.md` — papers under 0.70 confidence are flagged for mandatory human verification, and every value carries a source pin (e.g. "Table 2, p.5") so spot-checking is fast.

## Why protocol development is a stage, not a prerequisite

The eligibility decision that sinks a review is usually the one nobody made. "Prospective studies only, or
are retrospective cohorts eligible?" is easy to answer on day one and expensive to answer halfway through
screening — by then, changing it means a PROSPERO amendment, and changing criteria *after seeing results* is
the bias reviewers check for when they compare your registration date against your search date.

So Stage 0 forces each decision explicitly, before any record is judged: population bounds, intervention
thresholds, whether a comparator is required at all, which designs are in, minimum follow-up and sample size,
language and date limits, grey literature, and each outcome's definition, instrument, unit and timepoint. It
runs a scoping search first, so those decisions are made knowing what the literature actually holds — how
many records the question returns, which designs exist, what each restriction costs you. That is feasibility
information, not study-level cherry-picking, and the distinction is enforced throughout: criteria are revised
for methodological precision, never to change which studies survive.

The output is `protocol/prospero_draft.md`, generated against a field reference
(`prompts/reference/prospero-fields.md`) verified directly against the live register. PROSPERO's current form
(rebuilt February 2025) splits every eligibility element into Included and Excluded boxes, and a good half of
its fields are dropdowns with fixed wording rather than free text — so the draft marks each field **free**
(paste this), **pick** (select this option, quoted exactly), **struct** (per-entry values) or **auto**
(PROSPERO fills it). Anything it cannot fill is marked `⚠ NEEDS INPUT` rather than invented.

## Why batches for screening? (cost vs context rot)

One agent per record would mean thousands of agent spawns for a typical search (slow, expensive). One agent screening everything degrades silently as its context fills with hundreds of abstracts ("context rot"). A title+abstract is only ~300 tokens, so the sweet spot is **one agent per batch of ~40 records** — a 2,000-record search becomes ~50 fresh-context batch runs per pass instead of 2,000, with no batch ever near context limits. Dual-pass (every batch judged twice, independently; disagreements demoted to `maybe`) mirrors Cochrane dual screening and catches individual judgment slips.

## Why per-paper JSON files?

Parallel extractors writing to one shared CSV corrupt each other. One JSON per paper means no write conflicts, cheap single-paper retries (delete the JSON, re-run — everything else is skipped), and a deterministic merge you can re-run any time.

## Data integrity rules

- Every criterion and every outcome traces to the protocol. Criteria are never tuned to change which studies survive; outcome fields are never built from what the PDFs happen to report (that is selective outcome reporting). Genuine changes are protocol amendments, recorded in `protocol/amendments/` with the reason — PRISMA 2020 item 24c.
- The PROSPERO review-stage matrix is filled from what actually happened, never optimistically: if screening already started, the record says so.
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
