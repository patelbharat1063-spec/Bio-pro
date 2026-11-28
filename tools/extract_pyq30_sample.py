#!/usr/bin/env python3
"""Create a review-only OCR pilot; process two-column pages one column at a time."""
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
    pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), colorspace=fitz.csGRAY, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    # The source uses two columns; OCR each column separately to avoid mixing rows.
    w, h = img.size
    for col_no, crop in enumerate((img.crop((0, 0, w // 2, h)), img.crop((w // 2, 0, w, h))), start=1):
        raw = pytesseract.image_to_string(crop, config="--oem 1 --psm 6")
        chunks = re.split(r"(?m)(?=^\s*\d{1,3}[.)]\s+)", raw)
        for chunk in chunks:
            chunk = " ".join(chunk.split())
            match = re.match(r"^(\d{1,3})[.)]\s+", chunk)
            if not match:
                continue
            qno = int(match.group(1))
            labels = re.findall(r"(?i)(?:^|\s)[(]?[A-D][).](?=\s)", chunk)
            # Reject blocks that likely continue into another question or are not full MCQs.
            if len(labels) < 3 or len(chunk) < 45:
                continue
            records.append({
                "id": hashlib.sha256(f"{filename}:{page_no}:{col_no}:{qno}:{chunk[:120]}".encode()).hexdigest()[:20],
                "source_file": filename, "source_page": page_no, "source_column": col_no,
                "source_question_number": qno, "ocr_text": chunk,
                "detected_option_labels": len(labels),
                "status": "needs_manual_review", "topic_id": None, "answer": None
            })
out = {
    "schema_version": 1,
    "purpose": "Review-only OCR pilot; column-separated; not approved for app import",
    "source_repository": "https://github.com/manjunath5496/30-Years-NEET-AIPMT-Chapterwise-Paper-and-Solution-Biology",
    "pages_tested": [{"file": f, "page": p} for f,p in TARGETS],
    "records_detected": len(records),
    "records": records
}
Path("public/data").mkdir(parents=True, exist_ok=True)
Path("public/data/pyq30-sample-review.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PYQ_SAMPLE_RECORDS={len(records)}")
print("PYQ_SAMPLE_STATUS=review_only")
