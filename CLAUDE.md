# SRM Assistant — SRMA Data Extraction Harness

Harness for extracting structured data from research paper PDFs for systematic reviews and meta-analyses. Run `/srma-extract` to start or continue an extraction batch — it drives the full pipeline: protocol → JSON schema (user-confirmed) → one `srma-data-extractor` subagent per PDF in parallel → merged outputs.

## Layout

| Path | Purpose |
|---|---|
| `protocol/` | User drops PROSPERO application, PICO notes, and/or an extraction sheet template (CSV/XLSX) here |
| `papers/` | The PDFs to extract, one review batch at a time |
| `schema/extraction_schema.json` | Generated extraction schema — must be user-confirmed before extraction |
| `extractions/` | Per-paper JSON written by subagents (`<pdf-stem>.json`) |
| `output/` | Merged `extraction_sheet.csv`, `confidence_report.csv`, `missing_data_report.md` |
| `scripts/merge_extractions.py` | Deterministic merge (stdlib only): `python3 scripts/merge_extractions.py` |

## Conventions

- One review at a time. Archive or clear `papers/`, `schema/`, `extractions/`, `output/` before starting a new review.
- Missing values are `NR` (not reported) vs `NA` (not applicable) — never blank, never guessed.
- Papers with overall confidence < 0.70 require human verification (listed in the missing-data report).
- The per-PDF extractor agent lives at `~/.claude/agents/srma-data-extractor.md` (user scope). Its `model:` field (currently `sonnet`) is the knob to turn if extraction quality is insufficient.
- To re-run one paper: delete its `extractions/<pdf-stem>.json`, re-run `/srma-extract` (it skips papers that already have valid extractions), then re-merge.
