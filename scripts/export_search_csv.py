#!/usr/bin/env python3
"""Export line-numbered search strategy files as one flat CSV.

One row per search line across every database, so the strategy can be reviewed in a spreadsheet, pasted
into a PRISMA-S appendix table, or diffed after an amendment.

Columns: database, interface, line, query, results, note

`results` is filled from `<db>_counts.csv` if one sits beside the strategy file (written by
`scripts/run_pubmed_strategy.py`); otherwise it is left blank for whoever runs the search to complete.

Usage:
    python3 scripts/export_search_csv.py --out protocol/search/search_strategies.csv \\
        protocol/search/strategy_*.txt
"""
import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_search_docx import parse  # noqa: E402


def counts_for(path):
    """Load per-line results from a sibling <stem>_counts.csv, if present."""
    stem = pathlib.Path(path).stem.replace("strategy_", "")
    candidate = pathlib.Path(path).parent / f"{stem}_counts.csv"
    if not candidate.exists():
        return {}
    with candidate.open(encoding="utf-8") as fh:
        return {row["line"]: row["results"] for row in csv.DictReader(fh)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strategies", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for path in args.strategies:
        meta, notes, lines = parse(path)
        results = counts_for(path)
        database = meta.get("database", pathlib.Path(path).stem)
        for num, query in lines:
            rows.append({
                "database": database,
                "interface": meta.get("interface", ""),
                "line": num,
                "query": query,
                "results": results.get(num, ""),
                "note": "; ".join(notes) if num == lines[-1][0] else "",
            })

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["database", "interface", "line", "query", "results", "note"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.out} — {len(rows)} search lines across {len(args.strategies)} databases")


if __name__ == "__main__":
    main()
