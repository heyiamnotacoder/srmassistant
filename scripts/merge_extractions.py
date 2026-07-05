#!/usr/bin/env python3
"""Merge per-paper extraction JSONs into the final SRMA outputs.

Reads schema/extraction_schema.json and every extractions/*.json, then writes:
  output/extraction_sheet.csv   - extracted values, columns in schema order
  output/confidence_report.csv  - per-field confidence + overall per paper
  output/missing_data_report.md - NR fields, flags, and batch aggregates

Exits nonzero listing the offending files if any extraction JSON is malformed
or fails validation, so the orchestrator knows which papers to re-run.
Stdlib only.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

CONFIDENCE_REVIEW_THRESHOLD = 0.70

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schema" / "extraction_schema.json"
EXTRACTIONS_DIR = PROJECT_ROOT / "extractions"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_schema():
    if not SCHEMA_PATH.exists():
        sys.exit(f"ERROR: schema not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    field_names = [field["name"] for field in schema.get("fields", [])]
    if not field_names:
        sys.exit("ERROR: schema has no fields")
    return schema, field_names


def load_extractions(field_names):
    """Return (extractions, bad_files, warnings). Each extraction is the parsed JSON."""
    extractions, bad_files, warnings = [], [], []
    files = sorted(EXTRACTIONS_DIR.glob("*.json"))
    if not files:
        sys.exit(f"ERROR: no extraction files found in {EXTRACTIONS_DIR}")

    schema_set = set(field_names)
    for path in files:
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            bad_files.append(f"{path.name}: invalid JSON ({e})")
            continue

        rows = data.get("rows")
        if not isinstance(rows, list) or not rows:
            bad_files.append(f"{path.name}: missing or empty 'rows' array")
            continue

        ok = True
        for i, row in enumerate(rows):
            fields = row.get("fields")
            if not isinstance(fields, dict):
                bad_files.append(f"{path.name}: row {i} missing 'fields' object")
                ok = False
                break
            missing = schema_set - set(fields)
            extra = set(fields) - schema_set
            if missing:
                warnings.append(
                    f"{path.name} row {i}: schema fields absent from extraction: {sorted(missing)}"
                )
            if extra:
                warnings.append(
                    f"{path.name} row {i}: fields not in schema (ignored): {sorted(extra)}"
                )
        if ok:
            data["_file"] = path.name
            extractions.append(data)

    extractions.sort(key=lambda d: str(d.get("study_id", d["_file"])))
    return extractions, bad_files, warnings


def cell(field_obj, key, default=""):
    if isinstance(field_obj, dict):
        return field_obj.get(key, default)
    return default


def write_extraction_sheet(extractions, field_names):
    path = OUTPUT_DIR / "extraction_sheet.csv"
    header = ["study_id", "row_id", "paper_file"] + field_names
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for ext in extractions:
            for row in ext["rows"]:
                fields = row["fields"]
                writer.writerow(
                    [ext.get("study_id", ""), row.get("row_id", ""), ext.get("paper_file", ext["_file"])]
                    + [cell(fields.get(name), "value", "NR") for name in field_names]
                )
    return path


def write_confidence_report(extractions, field_names):
    path = OUTPUT_DIR / "confidence_report.csv"
    header = ["study_id", "row_id", "overall_confidence"] + field_names
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for ext in extractions:
            for row in ext["rows"]:
                fields = row["fields"]
                writer.writerow(
                    [ext.get("study_id", ""), row.get("row_id", ""), ext.get("overall_confidence", "")]
                    + [cell(fields.get(name), "confidence", "") for name in field_names]
                )
    return path


def write_missing_data_report(extractions, field_names, warnings):
    path = OUTPUT_DIR / "missing_data_report.md"
    nr_counter = Counter()
    low_confidence = []

    lines = ["# Missing Data & Confidence Report", ""]

    lines.append("## Per-paper details")
    lines.append("")
    for ext in extractions:
        study = ext.get("study_id", ext["_file"])
        conf = ext.get("overall_confidence")
        lines.append(f"### {study} ({ext.get('paper_file', ext['_file'])})")
        lines.append("")
        lines.append(f"- **Overall confidence**: {conf}")
        justification = ext.get("confidence_justification", "")
        if justification:
            lines.append(f"- **Justification**: {justification}")

        nr_fields = ext.get("missing_fields")
        if nr_fields is None:
            nr_fields = sorted(
                {
                    name
                    for row in ext["rows"]
                    for name in field_names
                    if str(cell(row["fields"].get(name), "value", "NR")).upper() == "NR"
                }
            )
        lines.append(f"- **Not reported (NR)**: {', '.join(nr_fields) if nr_fields else 'none'}")
        nr_counter.update(nr_fields)

        flags = ext.get("flags") or []
        if flags:
            lines.append(f"- **Flags**: {'; '.join(flags)}")

        field_notes = []
        for row in ext["rows"]:
            for name in field_names:
                obj = row["fields"].get(name)
                parts = []
                if cell(obj, "derived", False):
                    parts.append("derived")
                note = cell(obj, "note", "")
                if note:
                    parts.append(note)
                if parts:
                    field_notes.append(f"`{row.get('row_id', '?')}.{name}`: {'; '.join(parts)}")
        if field_notes:
            lines.append("- **Field notes**:")
            for fn in field_notes:
                lines.append(f"  - {fn}")
        summary = ext.get("summary", "")
        if summary:
            lines.append(f"- **Agent summary**: {summary}")
        lines.append("")

        if isinstance(conf, (int, float)) and conf < CONFIDENCE_REVIEW_THRESHOLD:
            low_confidence.append((study, conf))

    lines.append("## Batch aggregates")
    lines.append("")
    lines.append(f"- Papers merged: {len(extractions)}")
    confs = [
        e["overall_confidence"]
        for e in extractions
        if isinstance(e.get("overall_confidence"), (int, float))
    ]
    if confs:
        lines.append(f"- Mean overall confidence: {sum(confs) / len(confs):.2f}")
    lines.append("")

    lines.append(f"### Papers below {CONFIDENCE_REVIEW_THRESHOLD} confidence (mandatory human verification)")
    lines.append("")
    if low_confidence:
        for study, conf in low_confidence:
            lines.append(f"- {study}: {conf}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("### Most frequently missing fields")
    lines.append("")
    if nr_counter:
        for name, count in nr_counter.most_common(15):
            lines.append(f"- `{name}`: NR in {count}/{len(extractions)} papers")
    else:
        lines.append("- none")
    lines.append("")

    if warnings:
        lines.append("### Validation warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    path.write_text("\n".join(lines))
    return path


def main():
    schema, field_names = load_schema()
    extractions, bad_files, warnings = load_extractions(field_names)

    if bad_files:
        print("ERROR: the following extraction files are malformed — re-run these papers:", file=sys.stderr)
        for b in bad_files:
            print(f"  - {b}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    sheet = write_extraction_sheet(extractions, field_names)
    conf = write_confidence_report(extractions, field_names)
    report = write_missing_data_report(extractions, field_names, warnings)

    row_count = sum(len(e["rows"]) for e in extractions)
    print(f"Merged {len(extractions)} papers ({row_count} rows) using schema '{schema.get('review_title', '?')}'")
    print(f"  {sheet}")
    print(f"  {conf}")
    print(f"  {report}")
    if warnings:
        print(f"  {len(warnings)} validation warning(s) — see report")


if __name__ == "__main__":
    main()
