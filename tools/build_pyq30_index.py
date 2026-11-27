#!/usr/bin/env python3
"""Create a metadata-only index from the public 30-year NEET Biology source.

Only PDF filenames, page numbers, and short candidate headings are emitted.
Question text, options, answer keys, and explanations are deliberately excluded.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import fitz

ROOT = Path(".pyq30")
OUT = Path("public/data/pyq30-index.json")
SOURCE_REPO = "https://github.com/manjunath5496/30-Years-NEET-AIPMT-Chapterwise-Paper-and-Solution-Biology"
PDFS = sorted(ROOT.rglob("*.pdf"))
HEADINGS: dict[str, dict] = {}

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" •·\t-")

def page_lines(page: fitz.Page):
    data = page.get_text("dict")
    rows = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = clean("".join(s.get("text", "") for s in spans))
            if not text or len(text) > 100:
                continue
            size = max((s.get("size", 0) for s in spans), default=0)
            flags = max((s.get("flags", 0) for s in spans), default=0)
            rows.append((text, size, flags))
    return rows

for pdf_path in PDFS:
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        continue
    for page_no, page in enumerate(doc, start=1):
        rows = page_lines(page)
        if not rows:
            continue
        sizes = sorted(size for _, size, _ in rows if size > 0)
        median = sizes[len(sizes)//2] if sizes else 0
        for text, size, flags in rows:
            # Keep only visually prominent, short lines likely to be section headings.
            if size < median + 1.5 and not (flags & 16 and size >= median + 0.5):
                continue
            if len(text) < 3 or re.fullmatch(r"[\d\W]+", text):
                continue
            # Exclude common running headers and question/answer material.
            if re.search(r"(?i)\b(question|answer|solution|option|aipmt|neet\s*\d{4})\b", text):
                continue
            key = text.casefold()
            entry = HEADINGS.setdefault(key, {"heading": text, "sources": []})
            source = {"file": pdf_path.name, "page": page_no}
            if source not in entry["sources"]:
                entry["sources"].append(source)
    doc.close()

payload = {
    "schema_version": 1,
    "generated_by": "tools/build_pyq30_index.py",
    "source_repository": SOURCE_REPO,
    "content_policy": "Metadata-only index. No question text, options, answer keys, or explanations are stored.",
    "extraction": {
        "pdf_files_found": len(PDFS),
        "candidate_heading_count": len(HEADINGS),
        "status": "review_required" if HEADINGS else "no_headings_detected",
        "note": "Automated heading candidates require human verification before being treated as official chapter names."
    },
    "headings": sorted(HEADINGS.values(), key=lambda x: (x["heading"].casefold(), x["heading"]))
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUT}: {len(PDFS)} PDFs, {len(HEADINGS)} candidate headings")
