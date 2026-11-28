#!/usr/bin/env python3
"""Create a review-only OCR pilot from three likely question pages."""
from pathlib import Path
import io, json, re, hashlib
import fitz, pytesseract
from PIL import Image

ROOT = Path(".pyq30")
TARGETS = [("91_m72.pdf", 1), ("271_m72.pdf", 3), ("361_m72.pdf", 10)]
pdfs = {p.name: p for p in ROOT.rglob("*.pdf")}
records = []
for filename, page_no in TARGETS:
    path = pdfs.get(filename)
    if not path:
        continue
    doc = fitz.open(path)
    page = doc[page_no - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), colorspace=fitz.csGRAY, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    raw = pytesseract.image_to_string(img, config="--oem 1 --psm 6")
    doc.close()
    # Split on numbered starts. Keep only blocks with at least three option labels.
    chunks = re.split(r"(?m)(?=^\s*\d{1,3}[.)]\s+)", raw)
    for chunk in chunks:
        chunk = " ".join(chunk.split())
        if not re.match(r"^\d{1,3}[.)]\s+", chunk):
            continue
        labels = re.findall(r"(?i)(?:^|\s)[(]?[A-D][).](?=\s)", chunk)
        if len(labels) < 3:
            continue
        qno = int(re.match(r"^(\d{1,3})", chunk).group(1))
        records.append({
            "id": hashlib.sha256(f"{filename}:{page_no}:{qno}:{chunk[:120]}".encode()).hexdigest()[:20],
            "source_file": filename, "source_page": page_no, "source_question_number": qno,
            "ocr_text": chunk, "detected_option_labels": len(labels),
            "status": "needs_manual_review", "topic_id": None, "answer": None
        })
out = {
    "schema_version": 1,
    "purpose": "Review-only OCR pilot; not approved for app import",
    "source_repository": "https://github.com/manjunath5496/30-Years-NEET-AIPMT-Chapterwise-Paper-and-Solution-Biology",
    "pages_tested": [{"file": f, "page": p} for f,p in TARGETS],
    "records_detected": len(records),
    "records": records
}
Path("public/data").mkdir(parents=True, exist_ok=True)
Path("public/data/pyq30-sample-review.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PYQ_SAMPLE_RECORDS={len(records)}")
print("PYQ_SAMPLE_STATUS=review_only")
