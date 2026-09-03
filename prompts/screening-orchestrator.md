# SRMA Screening Orchestrator

Canonical workflow for AI-assisted title/abstract screening of database search exports (.ris / .nbib) for a systematic review / meta-analysis. Tool-agnostic: works with any capable LLM in any harness — parallel subagents, a single agent, or a human driving a chat UI. This file is the source of truth; vendor adapters only add mechanics.

Screening happens AFTER protocol development (`prompts/protocol-builder.md`) and BEFORE extraction: it triages hundreds-to-thousands of citation records into `exclude` / `maybe` / `include`, so only plausible studies proceed to full-text retrieval and the extraction workflow (`prompts/orchestrator.md`).

**Architecture note — why batches?** One agent per record would mean thousands of expensive spawns; one agent for all records rots its context after ~100 records and quality degrades silently. Records are small (~300 tokens of title+abstract), so the unit of work is a **batch of ~40 records screened in one fresh context**. Deterministic Python does parsing/dedup/splitting/merging; the LLM only judges.

All paths are relative to the project root.

## Phase S-A — Screening criteria

Criteria come from the review's protocol. Take the first branch that applies:

- **`protocol/pico.json` exists** (Stage 0 ran) — `screening/criteria.json` was already derived from it and
  confirmed by the human. Verify it exists and is consistent with `pico.json`; if so, report that and go
  straight to Phase S-B. Do **not** re-elicit criteria the human has already settled.
- **A registered protocol exists in `protocol/`** (PROSPERO record, PDF/Word/text) — derive the criteria from
  it, changing nothing. Registered eligibility criteria are fixed; if they look wrong, that is an amendment
  for the human to make on the register, not an edit to make here.
- **`protocol/` is empty** — stop. Do not invent criteria. Point the human at `prompts/protocol-builder.md`
  (Stage 0), which exists precisely to produce them.

**Registration check.** Read `protocol/registration.json`. If it is missing, warn the human that screening is
proceeding without a prospective registration, and that any later PROSPERO record must tick
"Screening search results against inclusion criteria" as already started. Proceed only if they confirm. If it
is present, record its CRD number in the screening report so the results carry their registration.

When deriving criteria (branches 2 and 3 above), write `screening/criteria.json`:

```json
{
  "review_title": "...",
  "pico": {"population": "...", "intervention": "...", "comparator": "...", "outcomes": ["..."]},
  "include_criteria": ["adults ≥18 with condition Y", "randomized controlled trial", "..."],
  "exclude_criteria": [
    {"code": "E1_population", "description": "wrong population (e.g., children, animal studies)"},
    {"code": "E2_intervention", "description": "does not evaluate the protocol intervention"},
    {"code": "E3_comparator", "description": "no eligible comparator"},
    {"code": "E4_outcomes", "description": "reports none of the protocol outcomes"},
    {"code": "E5_design", "description": "ineligible design (narrative review, editorial, case report, protocol-only)"},
    {"code": "E6_duplicate", "description": "duplicate publication of an already-included study"}
  ]
}
```

   Order `exclude_criteria` by how decisively they can be judged from an abstract (design and population first, outcomes last) — screeners assign the FIRST failing code, and these codes feed the PRISMA flow diagram.

**Present the criteria to the human and get explicit confirmation.** Never screen against unconfirmed criteria. (Skipped when Stage 0 already confirmed them — one confirmation is enough; asking twice invites second-guessing of settled decisions.)

## Phase S-B — Parse, dedupe, batch

The human drops database exports (`.ris`, `.nbib`) into `screening/exports/`. Then run:

```bash
python3 scripts/parse_citations.py            # default 40 records/batch
python3 scripts/parse_citations.py --batch-size 25   # smaller batches if desired
```

Requires only Python 3 stdlib. It parses all exports, deduplicates across databases (DOI → PMID → normalized title; log in `screening/dedup_log.csv`), and writes `screening/records.jsonl` + `screening/batches/batch_NNN.json`. Report the printed counts (identified per source, duplicates removed, records to screen) to the human — these are their PRISMA numbers.

If it refuses to run because `screening/decisions/` is non-empty, existing decisions would be orphaned — ask the human before using `--force`.

## Phase S-C — Dual-pass screening

Every batch is screened TWICE, independently: pass `A` and pass `B`, each following `prompts/screener.md`, each writing its own `screening/decisions/<batch-stem>_<pass>.json`. **Passes must not see each other's output** — that independence is what makes the later agreement check meaningful (this mirrors human dual screening in Cochrane reviews).

**Resume/skip**: before screening, list the batches and skip any `<batch-stem>_<pass>` whose decisions file already exists and parses. Report skips.

Pick the mode your harness supports:

- **Parallel mode** (harnesses with subagents): one subagent per batch-pass, at most 5 concurrent; each gets the contents (or path) of `prompts/screener.md`, the batch file path, the criteria path, its pass label, and its output path. Wait for a wave before launching the next.
- **Sequential mode** (single-agent harnesses): same units of work, one at a time, resetting context between batch-passes. Do pass A of all batches, then pass B — maximizes separation between the two judgments of the same records.
- **Manual chat-UI mode**: the human opens one chat per batch-pass: paste `prompts/screener.md`, attach `criteria.json` + the batch file, state the pass label, save the returned JSON code block into `screening/decisions/`.

**Validation** (all modes): each decisions file must exist and parse (`python3 -m json.tool`). Re-run a failed batch-pass once; if it fails twice, note it and let the merge step's error listing drive the retry.

## Phase S-D — Adjudicate & report

```bash
python3 scripts/merge_screening.py
```

Adjudication: passes agree → verdict stands (confidence = mean); passes disagree → `maybe` with a conflict flag (a disagreement between independent screeners is by definition a close call — a human decides). Outputs:

- `screening/screening_results.csv` — full audit: both passes + final verdict per record.
- `screening/screening_report.md` — PRISMA counts (identified, deduplicated, excluded by reason code, maybe, included), A/B agreement rate, and low-confidence excludes (< 0.80) for human spot-check.
- `screening/included_maybe.ris` — include + maybe records as a valid RIS file for import into Rayyan/EndNote/Zotero for full-text retrieval.

If it exits nonzero it lists exactly which decision files are missing/malformed — re-run those batch-passes and merge again.

Report to the human: final counts, agreement rate, and the reminder that `maybe` records and low-confidence excludes need human eyes. Retrieved PDFs of the survivors go into `papers/` for the extraction workflow.

## Rules

- AI screening is a **screening aid**: the human reviews all `maybe` records and spot-checks excludes; its use should be reported in the review's methods section.
- Never let screeners fetch full text or search the web for a record — title/abstract only, or the stage's methodology (and PRISMA counts) is invalidated.
- Never edit verdicts during merge; conflicts get flagged, not resolved silently.
- One review batch at a time; archive `screening/` (except `exports/README.md`) before a new review.
- Criteria are the protocol's, not the screener's. If screening reveals a genuine problem with the criteria,
  stop and raise it as a protocol amendment — never quietly widen or narrow them mid-run.
