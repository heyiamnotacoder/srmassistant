---
name: srma-extract
description: Orchestrate structured data extraction from research paper PDFs for a systematic review / meta-analysis. Generates a JSON extraction schema from the review protocol (PICO, PROSPERO, extraction template), spawns one srma-data-extractor agent per PDF in parallel, then merges results into an extraction sheet with confidence and missing-data reports. Use when the user wants to start or continue an SRMA extraction batch.
---

# SRMA Extraction Orchestrator

You are orchestrating data extraction for a systematic review / meta-analysis. Work through the three phases below in order. All paths are relative to the project root (the directory containing this `.claude/` folder); always pass **absolute** paths to subagents.

## Phase A — Schema generation

1. Read every file in `protocol/`:
   - PROSPERO application (PDF/Word/text) — review title, PICO, eligibility criteria, outcome definitions.
   - PICO notes or protocol drafts.
   - Any extraction sheet template (CSV/XLSX) — **if present, its column names and order define the schema fields**. Read XLSX via Python (openpyxl if available, else `unzip -p file.xlsx` + parse XML, or ask the user for CSV).
   - If `protocol/` is empty, stop and ask the user to drop their protocol documents there.

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
      "unit": "optional — required unit; agents flag conversions",
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

3. **Present the schema to the user and get explicit confirmation before Phase B.** Summarize the fields, row format, and any judgment calls you made (e.g., inferred units, ITT default). Never extract against an unconfirmed schema.

## Phase B — Parallel extraction

1. List `papers/*.pdf`. Skip papers that already have a valid `extractions/<pdf-stem>.json` (allows resuming a batch); tell the user which are being skipped.

2. Spawn one `srma-data-extractor` agent per remaining PDF via the Agent tool, **in parallel batches of at most 5** (launch a batch in a single message, wait for all to finish, then launch the next).

3. Each agent prompt must contain:
   - Absolute path to the one PDF it owns.
   - Absolute path to `schema/extraction_schema.json`.
   - Absolute output path: `extractions/<pdf-stem>.json`.
   - Instruction: follow the per-paper JSON output contract in your agent definition; return a summary with study ID, missing (NR) fields, overall confidence with justification, and any flags requiring human verification.

4. As each batch finishes, verify the output file exists and is valid JSON (`python3 -m json.tool <file>`). Re-run the agent once for any missing/malformed output; if it fails twice, record the paper in the final report as "extraction failed — manual extraction required" and move on.

## Phase C — Merge & report

1. Run the merge script from the project root:

   ```bash
   python3 scripts/merge_extractions.py
   ```

   It writes:
   - `output/extraction_sheet.csv` — extracted values, columns in schema order.
   - `output/confidence_report.csv` — per-field confidence scores + overall per paper.
   - `output/missing_data_report.md` — per-paper NR fields, flags, justifications, plus batch-level aggregates and papers below the 0.70 confidence threshold.

   If it exits nonzero, it prints the offending extraction files — fix or re-run those papers (Phase B step 4) and re-merge.

2. Report to the user: number of papers processed vs. failed, mean overall confidence, papers flagged for mandatory human verification (confidence < 0.70 or agent flags), and the fields most frequently NR across the batch. Point them to the three output files.

## Rules

- One review batch at a time. Before starting a *new* review, ask the user to archive or clear `papers/`, `schema/`, `extractions/`, and `output/`.
- Never edit extraction values yourself during merge — the agents' JSON is the source of truth; disagreements get flagged, not silently fixed.
- If the user adds papers mid-review, only extract the new ones (Phase B resume behavior) and re-run the merge.
