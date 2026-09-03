# protocol/search/

The search strategy and its results — one folder per review, written during Stage 0 (`/srma-protocol`,
Phase P-C) and updated again when the formal search is run.

A search strategy is a registrable, reportable artefact: PROSPERO asks for the full strategy for at least
one database, and PRISMA 2020 (items 6–7) and PRISMA-S require the exact strings, the databases, the
platform, the date run, and the yield per line. Keeping the strategy and its line-by-line counts here means
those items are transcribed from a record, not reconstructed from memory.

| File | What it is |
|---|---|
| `strategy_<db>.txt` | The line-numbered strategy for one database, `N\|query` per line (see below) |
| `<db>_counts.csv` | Hit count per strategy line — `line,query,results,note` — produced by the runner |
| `search_log.md` | Per-database run record: platform/interface, date run, final yield, deduplication notes, who ran it |
| `search_strategies.csv` | All strategies flattened to one machine-readable table |
| `search_strategies.docx` | The strategies as a Word appendix — the format PROSPERO's "Link to search strategy" field and journal PRISMA-S supplements expect |

Scoping-search yields also land in `protocol/pico.json` under `scoping_search`; this folder holds the full
strings and the per-line arithmetic behind those numbers.

## Strategy file format

One search line per row, numbered from 1, in execution order. `#N` refers to an earlier line's result set:

```
1|"Dermatitis, Atopic"[Mesh]
2|"atopic dermatitis"[tiab] OR "atopic eczema"[tiab]
3|#1 OR #2
4|#3 AND randomized controlled trial[pt]
```

Blank lines are ignored. Lines starting `#` are metadata (`# database:`, `# interface:`, `# date_run:`,
`# final_line:`, `# final_results:`, and repeated `# note:`) and are rendered into the DOCX header block;
lines starting `//` are comments and are dropped entirely.

## Running it

```bash
python3 scripts/run_pubmed_strategy.py protocol/search/strategy_pubmed.txt \
  --csv protocol/search/pubmed_counts.csv
```

The runner resolves `#N` on NCBI's history server, the way a database interface holds numbered result sets.
It is PubMed-only; for Embase, Scopus, Web of Science and CENTRAL, record the strategy here in the same
format and paste the counts the platform reports into `<db>_counts.csv` by hand.

Then produce the deliverables:

```bash
python3 scripts/export_search_csv.py --out protocol/search/search_strategies.csv \
  protocol/search/strategy_*.txt

python3 scripts/make_search_docx.py --out protocol/search/search_strategies.docx \
  --title "Search strategies" protocol/search/strategy_*.txt
```

`make_search_docx.py` writes OOXML with the standard library only — no python-docx dependency. Pass a
single strategy file to produce a per-database document to hand to an information specialist.

Contents of this folder other than this README are gitignored — your review's working data stays local.
