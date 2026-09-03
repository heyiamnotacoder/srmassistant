#!/usr/bin/env python3
"""Render line-numbered search strategy files as a .docx appendix.

Search strategies have to leave this repo as Word documents: that is what PROSPERO's "Link to search
strategy" field accepts, what journals want as a PRISMA-S supplementary appendix, and what an information
specialist expects to be handed. This writes a minimal, valid OOXML document with the standard library
only -- no python-docx dependency.

Usage:
    python3 scripts/make_search_docx.py --out protocol/search/search_strategies.docx \\
        --title "Search strategies" protocol/search/strategy_*.txt

    python3 scripts/make_search_docx.py --out protocol/search/strategy_embase.docx \\
        protocol/search/strategy_embase.txt

Each input file may carry `# key: value` metadata lines before its numbered search lines; `database`,
`interface`, `date_run`, `final_line`, `final_results` and repeated `note` keys are rendered as a header
block above the strategy table.
"""
import argparse
import pathlib
import zipfile
from xml.sax.saxutils import escape

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {NS}>
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/>
</w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/></w:style>
</w:styles>"""


def para(text, *, bold=False, size=22, mono=False, space_after=80, indent=0):
    font = "Consolas" if mono else "Calibri"
    return (
        f'<w:p><w:pPr><w:spacing w:after="{space_after}"/>'
        f'{f'<w:ind w:left="{indent}"/>' if indent else ""}</w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>'
        f'{"<w:b/>" if bold else ""}<w:sz w:val="{size}"/></w:rPr>'
        f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    )


def parse(path):
    meta, notes, lines = {}, [], []
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        raw = raw.rstrip()
        if not raw.strip() or raw.lstrip().startswith("//"):
            continue
        if raw.lstrip().startswith("#") and "|" not in raw.split("#", 1)[1][:4]:
            key, _, value = raw.lstrip("# ").partition(":")
            key, value = key.strip().lower(), value.strip()
            (notes.append(value) if key == "note" else meta.setdefault(key, value))
            continue
        num, _, query = raw.partition("|")
        if num.strip().isdigit():
            lines.append((num.strip(), query.strip()))
    return meta, notes, lines


def render(paths, title):
    body = [para(title, bold=True, size=32, space_after=200)]
    for path in paths:
        meta, notes, lines = parse(path)
        body.append(para(meta.get("database", pathlib.Path(path).stem), bold=True, size=26, space_after=60))
        for key, label in (("interface", "Interface"), ("date_run", "Date run"),
                           ("final_line", "Final line"), ("final_results", "Records retrieved")):
            if key in meta:
                body.append(para(f"{label}: {meta[key]}", size=20, space_after=20))
        for note in notes:
            body.append(para(f"Note: {note}", size=18, space_after=20, indent=200))
        body.append(para("", size=12, space_after=60))
        for num, query in lines:
            body.append(para(f"{num}.  {query}", mono=True, size=18, space_after=40, indent=280))
        body.append(para("", space_after=280))

    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>'
           + "".join(body)
           + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
             '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr>'
             "</w:body></w:document>")
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strategies", nargs="+", help="line-numbered strategy files")
    ap.add_argument("--out", required=True, help="output .docx path")
    ap.add_argument("--title", default="Search strategies", help="document title")
    args = ap.parse_args()

    document = render(args.strategies, args.title)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", document)
    print(f"Wrote {args.out} ({len(args.strategies)} strateg{'y' if len(args.strategies) == 1 else 'ies'})")


if __name__ == "__main__":
    main()
