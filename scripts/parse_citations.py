#!/usr/bin/env python3
"""Parse database citation exports (.ris / .nbib) for title/abstract screening.

Reads every .ris and .nbib file in screening/exports/, normalizes and
deduplicates the records (DOI, then PMID, then normalized title), then writes:

  screening/records.jsonl        - all unique records
  screening/batches/batch_NNN.json - screening batches (default 40 records)
  screening/dedup_log.csv        - which records merged into which
  screening/parse_summary.json   - PRISMA counts (identified per source, dups)

Usage: python3 scripts/parse_citations.py [--batch-size N] [--force]

Refuses to rebuild batches while screening/decisions/ has content, unless
--force, so existing screening decisions can't be silently orphaned.
Stdlib only.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = PROJECT_ROOT / "screening" / "exports"
SCREENING_DIR = PROJECT_ROOT / "screening"
BATCHES_DIR = SCREENING_DIR / "batches"
DECISIONS_DIR = SCREENING_DIR / "decisions"

RIS_TAG = re.compile(r"^([A-Z][A-Z0-9])  -\s?(.*)$")
NBIB_TAG = re.compile(r"^([A-Z]{1,4})\s{0,3}- (.*)$")


def parse_ris(path):
    """Yield raw tag-dicts from a RIS file (tag -> list of values)."""
    records, current, last_tag = [], {}, None
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = RIS_TAG.match(line)
        if m:
            tag, value = m.group(1), m.group(2).strip()
            if tag == "ER":
                if current:
                    records.append(current)
                current, last_tag = {}, None
            else:
                current.setdefault(tag, []).append(value)
                last_tag = tag
        elif line.strip() and last_tag:
            current[last_tag][-1] += " " + line.strip()
    if current:
        records.append(current)
    return records


def parse_nbib(path):
    """Yield raw tag-dicts from an NBIB (PubMed/MEDLINE) file."""
    records, current, last_tag = [], {}, None
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            if current:
                records.append(current)
            current, last_tag = {}, None
            continue
        if line.startswith("      ") and last_tag:
            current[last_tag][-1] += " " + line.strip()
            continue
        m = NBIB_TAG.match(line)
        if m:
            tag, value = m.group(1), m.group(2).strip()
            current.setdefault(tag, []).append(value)
            last_tag = tag
    if current:
        records.append(current)
    return records


def first(raw, *tags):
    for tag in tags:
        if raw.get(tag) and raw[tag][0]:
            return raw[tag][0]
    return ""


def extract_year(value):
    m = re.search(r"\b(19|20)\d{2}\b", value)
    return m.group(0) if m else ""


def extract_doi(value):
    m = re.search(r"\b10\.\d{4,9}/\S+", value)
    return m.group(0).rstrip(".,;") if m else ""


def normalize_ris(raw, source):
    return {
        "source_file": source,
        "title": first(raw, "TI", "T1"),
        "abstract": first(raw, "AB", "N2"),
        "authors": raw.get("AU", raw.get("A1", [])),
        "year": extract_year(first(raw, "PY", "Y1", "DA")),
        "journal": first(raw, "JO", "JF", "T2", "JA"),
        "doi": extract_doi(first(raw, "DO", "DI")).lower(),
        "pmid": first(raw, "AN") if first(raw, "AN").isdigit() else "",
        "pub_types": raw.get("TY", []),
    }


def normalize_nbib(raw, source):
    doi = ""
    for tag in ("AID", "LID", "SO"):
        for value in raw.get(tag, []):
            if "[doi]" in value or tag == "SO":
                doi = extract_doi(value)
                if doi:
                    break
        if doi:
            break
    return {
        "source_file": source,
        "title": first(raw, "TI"),
        "abstract": first(raw, "AB"),
        "authors": raw.get("FAU", raw.get("AU", [])),
        "year": extract_year(first(raw, "DP")),
        "journal": first(raw, "JT", "TA"),
        "doi": doi.lower(),
        "pmid": first(raw, "PMID"),
        "pub_types": raw.get("PT", []),
    }


def norm_title(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())


def dedupe(records):
    """Merge duplicates by DOI, then PMID, then normalized title."""
    unique, by_doi, by_pmid, by_title = [], {}, {}, {}
    merges = []
    for rec in records:
        target = None
        if rec["doi"] and rec["doi"] in by_doi:
            target, key = by_doi[rec["doi"]], f"doi:{rec['doi']}"
        elif rec["pmid"] and rec["pmid"] in by_pmid:
            target, key = by_pmid[rec["pmid"]], f"pmid:{rec['pmid']}"
        elif norm_title(rec["title"]) and norm_title(rec["title"]) in by_title:
            target, key = by_title[norm_title(rec["title"])], "title-match"
        if target is not None:
            if len(rec["abstract"]) > len(target["abstract"]):
                target["abstract"] = rec["abstract"]
            for field in ("doi", "pmid", "year", "journal"):
                if not target[field]:
                    target[field] = rec[field]
            target["source_file"] += f"; {rec['source_file']}"
            merges.append((rec["title"][:80], rec["source_file"], target["title"][:80], key))
        else:
            unique.append(rec)
            if rec["doi"]:
                by_doi[rec["doi"]] = rec
            if rec["pmid"]:
                by_pmid[rec["pmid"]] = rec
            if norm_title(rec["title"]):
                by_title[norm_title(rec["title"])] = rec
    return unique, merges


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch-size", type=int, default=40)
    ap.add_argument("--force", action="store_true",
                    help="rebuild batches even if screening/decisions/ has content")
    args = ap.parse_args()

    if DECISIONS_DIR.exists() and any(DECISIONS_DIR.glob("*.json")) and not args.force:
        sys.exit(
            "ERROR: screening/decisions/ already contains decision files.\n"
            "Rebuilding batches would orphan them. Archive/clear decisions first, "
            "or re-run with --force."
        )

    export_files = sorted(
        list(EXPORTS_DIR.glob("*.ris")) + list(EXPORTS_DIR.glob("*.nbib"))
    )
    if not export_files:
        sys.exit(f"ERROR: no .ris or .nbib files found in {EXPORTS_DIR}")

    all_records, per_source = [], {}
    for path in export_files:
        raws = parse_ris(path) if path.suffix == ".ris" else parse_nbib(path)
        normalizer = normalize_ris if path.suffix == ".ris" else normalize_nbib
        recs = [normalizer(r, path.name) for r in raws]
        recs = [r for r in recs if r["title"]]
        per_source[path.name] = len(recs)
        all_records.extend(recs)

    unique, merges = dedupe(all_records)

    # Deterministic IDs: same exports always yield the same record_id
    unique.sort(key=lambda r: (norm_title(r["title"]), r["year"], r["doi"]))
    for i, rec in enumerate(unique, 1):
        rec["record_id"] = f"R{i:04d}"

    SCREENING_DIR.mkdir(exist_ok=True)
    BATCHES_DIR.mkdir(exist_ok=True)
    for old in BATCHES_DIR.glob("batch_*.json"):
        old.unlink()

    with open(SCREENING_DIR / "records.jsonl", "w") as f:
        for rec in unique:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    batch_count = 0
    for start in range(0, len(unique), args.batch_size):
        batch_count += 1
        name = f"batch_{batch_count:03d}.json"
        with open(BATCHES_DIR / name, "w") as f:
            json.dump(
                {"batch_file": name, "records": unique[start:start + args.batch_size]},
                f, indent=1, ensure_ascii=False,
            )

    with open(SCREENING_DIR / "dedup_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dropped_title", "dropped_source", "kept_title", "matched_on"])
        writer.writerows(merges)

    summary = {
        "identified_per_source": per_source,
        "records_identified": len(all_records),
        "duplicates_removed": len(merges),
        "records_to_screen": len(unique),
        "batch_size": args.batch_size,
        "batches": batch_count,
    }
    with open(SCREENING_DIR / "parse_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Identified: {len(all_records)} records from {len(export_files)} file(s)")
    for src, n in per_source.items():
        print(f"  - {src}: {n}")
    print(f"Duplicates removed: {len(merges)} (see screening/dedup_log.csv)")
    print(f"To screen: {len(unique)} records in {batch_count} batch(es) of ≤{args.batch_size}")


if __name__ == "__main__":
    main()
