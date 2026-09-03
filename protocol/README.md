# protocol/

**If you already have a registered protocol**, drop it here before running the workflows:

- PROSPERO record or application (PDF, Word, or text)
- PICO criteria / protocol notes
- An existing data extraction sheet template (CSV or XLSX) — if provided, its columns define the extraction
  schema fields

**If you don't** — which is the normal case, since a registration is the *output* of protocol development,
not its input — run Stage 0 (`/srma-protocol`, or `prompts/protocol-builder.md`) instead. It starts from your
research question and writes into this folder:

| File | What it is |
|---|---|
| `pico.json` | Every eligibility and methods decision, machine-readable — the source of truth for both later stages |
| `prospero_draft.md` | Paste-ready PROSPERO registration, field by field, marking which fields are free text and which are dropdown selections |
| `search/` | The search strategy and its results — line-numbered strategy per database, per-line hit counts, run log. See `search/README.md` |
| `registration.json` | Your CRD number and registration date, recorded after you register |
| `amendments/` | Any post-registration change, with the reason (PRISMA 2020 item 24c) |

Contents of this folder are gitignored (apart from the two READMEs) — your review's working data stays local.
