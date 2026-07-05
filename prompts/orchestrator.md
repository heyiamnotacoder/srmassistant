# SRMA Extraction Orchestrator

Canonical workflow for extracting structured data from research paper PDFs for a systematic review / meta-analysis. This document is tool-agnostic: it works with any capable LLM (Claude, GPT, Gemini, ...) running in any harness — an agentic CLI with subagents, a single-agent CLI, or a human driving a chat UI. Tool-specific adapters (e.g., `.claude/skills/`) only add mechanics on top of this file; the logic here is the source of truth.

All paths are relative to the project root. Agents with file access should resolve them to absolute paths.

## Phase A — Schema generation

1. Read every file in `protocol/`:
   - PROSPERO application (PDF/Word/text) — review title, PICO, eligibility criteria, outcome definitions.
   - PICO notes or protocol drafts.
   - Any extraction sheet template (CSV/XLSX) — **if present, its column names and order define the schema fields**.
   - If `protocol/` is empty, stop and ask the human to drop their protocol documents there.

2. Write `schema/extraction_schema.json`:

```json
{
  "review_title": "...",
  "pico": {
    "population": "...",
    "intervention": "...",
    "comparator": "...",
    "outcomes": ["..."]
  },
  "analysis_population_default": "ITT",
  "row_format": "one_row_per_study | long_per_arm | long_per_outcome",
  "fields": [
    {
      "name": "snake_case_column_name",
      "description": "what to extract, exactly as the protocol defines it",
      "type": "text | number | integer | categorical",
      "unit": "optional — required unit; extractors flag conversions",
      "allowed_values": ["only for categorical"],
      "arm_level": false,
      "hint": "where it usually appears, e.g. 'Methods / Table 1'"
    }
  ]
}
```

   - Field order = template column order when a template exists.
   - Always include study-identification fields first (`study_id`, `first_author`, `year`, `trial_registration`, `study_design`) unless the template already has equivalents.
   - Choose `row_format` from the protocol: multi-arm dose comparisons or multiple timepoints usually need a long format.

3. **Present the schema to the human and get explicit confirmation before Phase B.** Summarize the fields, row format, and any judgment calls (inferred units, ITT default). Never extract against an unconfirmed schema.

## Phase B — Extraction (one paper at a time, one extractor per paper)

Each paper is extracted by following `prompts/extractor.md` with exactly three inputs: the PDF, the schema, and the output path `extractions/<pdf-stem>.json`. One extraction context per paper — never let one paper's content bleed into another's extraction.

**Resume/skip**: before extracting, list `papers/*.pdf` and skip any paper that already has a valid `extractions/<pdf-stem>.json`. Report which were skipped. This makes re-runs and mid-review paper additions cheap.

Pick the mode your harness supports:

### Parallel mode (harnesses with subagents — e.g., Claude Code, other multi-agent frameworks)

- Spawn one extractor subagent per remaining PDF, in batches of at most 5; wait for a batch to finish before launching the next.
- Each subagent's prompt: the contents (or path) of `prompts/extractor.md`, the absolute PDF path, the absolute schema path, and the absolute output path. Instruct it to return a summary: study ID, missing (NR) fields, overall confidence + justification, flags for human verification.

### Sequential mode (single-agent CLIs, or any harness without subagents)

- Process papers one at a time, and **reset context between papers** (fresh conversation/session per paper if possible; at minimum, do not carry one paper's extracted values into the next paper's context).
- For each paper, follow `prompts/extractor.md` yourself, write the JSON, then move to the next.

### Manual chat-UI mode (ChatGPT / Gemini / Claude web, no file access)

The human drives:
1. Do Phase A in one chat: attach protocol documents, paste this file's Phase A section, save the returned schema JSON to `schema/extraction_schema.json` locally.
2. Per paper, open a **new chat**: paste `prompts/extractor.md`, attach the schema JSON and the one PDF. Save the returned JSON code block as `extractions/<pdf-stem>.json` locally.
3. Run Phase C locally.

## Validation & retry (all modes)

- After each extraction, verify the output file exists and parses as JSON (`python3 -m json.tool extractions/<file>.json`).
- Re-run a paper once if its output is missing or malformed. If it fails twice, record it as "extraction failed — manual extraction required" in the final report and move on.

## Phase C — Merge & report

1. From the project root, run:

   ```bash
   python3 scripts/merge_extractions.py
   ```

   Requires only Python 3 (standard library — no packages to install). It writes:
   - `output/extraction_sheet.csv` — extracted values, columns in schema order (clean values; safe for RevMan/R import).
   - `output/confidence_report.csv` — per-field confidence scores + overall per paper.
   - `output/missing_data_report.md` — per-paper NR fields, flags, field notes, justifications; batch aggregates; papers below the 0.70 confidence threshold flagged for mandatory human verification.

   If it exits nonzero, it prints the offending extraction files — re-run those papers (see Validation & retry) and merge again.

2. Report to the human: papers processed vs failed, mean overall confidence, papers flagged for human verification, and the fields most frequently NR across the batch. Point them at the three output files.

## Rules

- One review batch at a time. Before a new review, archive or clear `papers/`, `schema/`, `extractions/`, and `output/`.
- Never edit extraction values during merge — the per-paper JSONs are the source of truth; disagreements get flagged, not silently fixed.
- Papers added mid-review: only extract the new ones (resume behavior), then re-merge.
- `NR` = not reported, `NA` = not applicable — never blank, never guessed.
