#!/usr/bin/env python3
"""Run a line-numbered PubMed search strategy against NCBI E-utilities and record hit counts.

Strategy file format — one line per search line, `N|query`:

    # database: PubMed (MEDLINE)   <- lines starting with '#' are metadata, not searches
    1|"Dermatitis, Atopic"[Mesh]
    2|"atopic dermatitis"[tiab] OR "atopic eczema"[tiab]
    3|#1 OR #2

`#N` references are resolved on NCBI's history server (`usehistory=y` + `WebEnv`), the same way a database
search interface holds numbered result sets. Lines must be numbered from 1 and are executed in order.
Expanding references textually instead produces multi-kilobyte URLs that E-utilities rejects with a 502.

Usage:
    python3 scripts/run_pubmed_strategy.py protocol/search/strategy_pubmed.txt
    python3 scripts/run_pubmed_strategy.py <file> --csv protocol/search/pubmed_counts.csv

Standard library only. Respects NCBI's 3-requests-per-second guidance.
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
REF = re.compile(r"#(\d+)")


def parse_strategy(path):
    lines = {}
    order = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.rstrip("\n")
            if not raw.strip() or raw.lstrip().startswith("#") or raw.lstrip().startswith("//"):
                continue
            num, _, query = raw.partition("|")
            num = num.strip()
            if not num.isdigit():
                sys.exit(f"Malformed line (expected 'N|query'): {raw[:80]!r}")
            lines[int(num)] = query.strip()
            order.append(int(num))
    return lines, order


def run(strategy_lines, order, delay=0.4, retries=3):
    """Execute lines in order on the history server, resolving #N against prior query keys."""
    webenv = None
    keys = {}
    rows = []
    for num in order:
        query = REF.sub(lambda m: "#" + str(keys[int(m.group(1))]), strategy_lines[num])
        params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": "0", "usehistory": "y"}
        if webenv:
            params["WebEnv"] = webenv
        payload = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    ESEARCH,
                    data=urllib.parse.urlencode(params).encode(),
                    headers={"User-Agent": "srmassistant/1.0"},
                )
                with urllib.request.urlopen(req, timeout=90) as resp:
                    payload = json.load(resp)
                break
            except urllib.error.HTTPError as exc:
                if attempt == retries - 1:
                    sys.exit(f"Line #{num}: HTTP {exc.code} from E-utilities after {retries} attempts")
                time.sleep(2 ** attempt)
        time.sleep(delay)
        result = payload.get("esearchresult", {})
        if "ERROR" in result:
            sys.exit(f"Line #{num}: {result['ERROR']}")
        webenv = result.get("webenv", webenv)
        keys[num] = int(result["querykey"])
        warn = result.get("warninglist", {}).get("outputmessages")
        rows.append({
            "line": num,
            "query": strategy_lines[num],
            "results": int(result.get("count", 0)),
            "note": warn[0] if warn else "",
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strategy", help="line-numbered strategy file")
    ap.add_argument("--csv", help="write results to this CSV as well as stdout")
    args = ap.parse_args()

    lines, order = parse_strategy(args.strategy)
    if order != sorted(order) or order[0] != 1:
        sys.exit("Strategy lines must be numbered from 1 and appear in ascending order.")
    rows = run(lines, order)
    for row in rows:
        print(f"#{row['line']:<3} {row['results']:>9,}  {row['query'][:88]}")
        if row["note"]:
            print(f"       note: {row['note']}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["line", "query", "results", "note"])
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote {args.csv}")


if __name__ == "__main__":
    main()
