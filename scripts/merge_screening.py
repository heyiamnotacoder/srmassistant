#!/usr/bin/env python3
"""Adjudicate dual-pass screening decisions and produce screening outputs.

Reads screening/records.jsonl, screening/batches/*.json, and all
screening/decisions/<batch>_<A|B>.json, then writes:

  screening/screening_results.csv - per record: both passes + final verdict
  screening/screening_report.md   - PRISMA counts, conflicts, spot-check list
  screening/included_maybe.ris    - include+maybe records for Rayyan/EndNote

Adjudication: passes agree -> that verdict (confidence = mean);
passes disagree -> 'maybe' with a conflict flag, both rationales preserved.

Exits nonzero listing missing/malformed decision files or records without
decisions, so the orchestrator knows exactly what to re-run. Stdlib only.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

LOW_CONF_EXCLUDE_THRESHOLD = 0.80
VERDICTS = {"include", "maybe", "exclude"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENING_DIR = PROJECT_ROOT / "screening"
BATCHES_DIR = SCREENING_DIR / "batches"
DECISIONS_DIR = SCREENING_DIR / "decisions"


def load_records():
    path = SCREENING_DIR / "records.jsonl"
    if not path.exists():
        sys.exit(f"ERROR: {path} not found — run scripts/parse_citations.py first")
    records = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            records[rec["record_id"]] = rec
    return records


def load_decisions(records):
    """Return ({record_id: {pass: decision}}, problems)."""
    batches = sorted(BATCHES_DIR.glob("batch_*.json"))
    if not batches:
        sys.exit(f"ERROR: no batch files in {BATCHES_DIR} — run scripts/parse_citations.py first")

    problems, decisions = [], {}
    for batch_path in batches:
        with open(batch_path) as f:
            batch_ids = [r["record_id"] for r in json.load(f)["records"]]

        for pass_name in ("A", "B"):
            dec_path = DECISIONS_DIR / f"{batch_path.stem}_{pass_name}.json"
            if not dec_path.exists():
                problems.append(f"missing decision file: {dec_path.name}")
                continue
            try:
                with open(dec_path) as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                problems.append(f"invalid JSON in {dec_path.name}: {e}")
                continue

            seen = set()
            for d in data.get("decisions", []):
                rid = d.get("record_id")
                if rid not in records:
                    problems.append(f"{dec_path.name}: unknown record_id {rid}")
                    continue
                if rid in seen:
                    problems.append(f"{dec_path.name}: duplicate decision for {rid}")
                    continue
                if d.get("verdict") not in VERDICTS:
                    problems.append(f"{dec_path.name}: {rid} has invalid verdict {d.get('verdict')!r}")
                    continue
                seen.add(rid)
                decisions.setdefault(rid, {})[pass_name] = d

            missing = set(batch_ids) - seen
            if missing:
                problems.append(
                    f"{dec_path.name}: no decision for {len(missing)} record(s): {sorted(missing)[:5]}"
                    + (" ..." if len(missing) > 5 else "")
                )
    return decisions, problems


def adjudicate(a, b):
    """Return (final_verdict, confidence, conflict)."""
    conf_a, conf_b = a.get("confidence", 0.5), b.get("confidence", 0.5)
    mean_conf = round((conf_a + conf_b) / 2, 2)
    if a["verdict"] == b["verdict"]:
        return a["verdict"], mean_conf, False
    return "maybe", mean_conf, True


def write_results_csv(records, decisions):
    path = SCREENING_DIR / "screening_results.csv"
    finals = {}
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id", "title", "year", "journal", "doi", "pmid",
            "passA_verdict", "passA_reason", "passA_confidence", "passA_rationale",
            "passB_verdict", "passB_reason", "passB_confidence", "passB_rationale",
            "final_verdict", "final_confidence", "conflict",
        ])
        for rid in sorted(records):
            rec = records[rid]
            a, b = decisions[rid]["A"], decisions[rid]["B"]
            verdict, conf, conflict = adjudicate(a, b)
            finals[rid] = {"verdict": verdict, "confidence": conf, "conflict": conflict,
                           "passes": (a, b)}
            writer.writerow([
                rid, rec["title"], rec["year"], rec["journal"], rec["doi"], rec["pmid"],
                a["verdict"], a.get("reason_code", ""), a.get("confidence", ""), a.get("rationale", ""),
                b["verdict"], b.get("reason_code", ""), b.get("confidence", ""), b.get("rationale", ""),
                verdict, conf, "yes" if conflict else "no",
            ])
    return path, finals


def write_ris(records, finals):
    path = SCREENING_DIR / "included_maybe.ris"
    with open(path, "w") as f:
        for rid in sorted(finals):
            if finals[rid]["verdict"] == "exclude":
                continue
            rec = records[rid]
            f.write("TY  - JOUR\n")
            f.write(f"ID  - {rid}\n")
            f.write(f"TI  - {rec['title']}\n")
            for au in rec.get("authors", []):
                f.write(f"AU  - {au}\n")
            if rec["year"]:
                f.write(f"PY  - {rec['year']}\n")
            if rec["journal"]:
                f.write(f"JO  - {rec['journal']}\n")
            if rec["doi"]:
                f.write(f"DO  - {rec['doi']}\n")
            if rec["pmid"]:
                f.write(f"AN  - {rec['pmid']}\n")
            if rec["abstract"]:
                f.write(f"AB  - {rec['abstract']}\n")
            f.write(
                f"N1  - srmassistant verdict: {finals[rid]['verdict']} "
                f"(confidence {finals[rid]['confidence']}"
                f"{', A/B conflict' if finals[rid]['conflict'] else ''})\n"
            )
            f.write("ER  - \n\n")
    return path


def write_report(records, finals):
    path = SCREENING_DIR / "screening_report.md"
    summary_path = SCREENING_DIR / "parse_summary.json"
    parse_summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    verdict_counts = Counter(f["verdict"] for f in finals.values())
    conflicts = [rid for rid, f in finals.items() if f["conflict"]]
    exclude_reasons = Counter()
    low_conf_excludes = []
    for rid, f in finals.items():
        if f["verdict"] == "exclude":
            a, b = f["passes"]
            exclude_reasons[a.get("reason_code") or b.get("reason_code") or "unspecified"] += 1
            if f["confidence"] < LOW_CONF_EXCLUDE_THRESHOLD:
                low_conf_excludes.append((rid, f["confidence"]))

    lines = ["# Screening Report (dual-pass, AI-assisted)", ""]

    lines.append("## PRISMA counts")
    lines.append("")
    if parse_summary:
        for src, n in parse_summary.get("identified_per_source", {}).items():
            lines.append(f"- Records identified from `{src}`: {n}")
        lines.append(f"- Total records identified: {parse_summary.get('records_identified')}")
        lines.append(f"- Duplicates removed: {parse_summary.get('duplicates_removed')}")
    lines.append(f"- Records screened: {len(finals)}")
    lines.append(f"- Excluded: {verdict_counts.get('exclude', 0)}")
    for code, n in exclude_reasons.most_common():
        lines.append(f"  - {code}: {n}")
    lines.append(f"- Maybe (needs human review): {verdict_counts.get('maybe', 0)}")
    lines.append(f"- Included: {verdict_counts.get('include', 0)}")
    lines.append("")

    lines.append("## Dual-pass agreement")
    lines.append("")
    rate = (len(finals) - len(conflicts)) / len(finals) * 100 if finals else 0
    lines.append(f"- Agreement rate: {rate:.1f}% ({len(conflicts)} conflict(s), demoted to 'maybe')")
    for rid in sorted(conflicts):
        a, b = finals[rid]["passes"]
        lines.append(
            f"  - {rid} \"{records[rid]['title'][:70]}\": "
            f"A={a['verdict']} ({a.get('rationale', '')}) vs B={b['verdict']} ({b.get('rationale', '')})"
        )
    lines.append("")

    lines.append(f"## Low-confidence excludes (< {LOW_CONF_EXCLUDE_THRESHOLD}) — human spot-check advised")
    lines.append("")
    if low_conf_excludes:
        for rid, conf in sorted(low_conf_excludes):
            lines.append(f"- {rid} (confidence {conf}): {records[rid]['title'][:80]}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Next steps")
    lines.append("")
    lines.append("1. Human-review the 'maybe' records (and spot-check low-confidence excludes).")
    lines.append("2. Import `screening/included_maybe.ris` into your reference manager / Rayyan for full-text retrieval.")
    lines.append("3. Drop retrieved PDFs into `papers/` and run the extraction workflow.")
    lines.append("")
    lines.append("*AI screening is a screening aid, not a replacement for the review team's*")
    lines.append("*final judgment — report its use in your methods section.*")

    path.write_text("\n".join(lines))
    return path


def main():
    records = load_records()
    decisions, problems = load_decisions(records)

    undecided = [rid for rid in records if len(decisions.get(rid, {})) < 2]
    if problems or undecided:
        print("ERROR: screening is incomplete — fix/re-run the following, then re-merge:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        if undecided and not problems:
            print(f"  - {len(undecided)} record(s) lack both passes: {sorted(undecided)[:5]}", file=sys.stderr)
        sys.exit(1)

    results_csv, finals = write_results_csv(records, decisions)
    ris = write_ris(records, finals)
    report = write_report(records, finals)

    counts = Counter(f["verdict"] for f in finals.values())
    print(f"Screened {len(finals)} records: "
          f"{counts.get('include', 0)} include / {counts.get('maybe', 0)} maybe / "
          f"{counts.get('exclude', 0)} exclude")
    print(f"  {results_csv}")
    print(f"  {report}")
    print(f"  {ris}")


if __name__ == "__main__":
    main()
