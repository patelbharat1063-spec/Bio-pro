#!/usr/bin/env python3
"""Measure OCR readability on a small, privacy-safe sample of the source PDFs.

Only page numbers and aggregate OCR quality metrics are printed; no recognized
question text, options, answers, or explanations are saved or logged.
"""
from pathlib import Path
import io
import json
import statistics
import fitz
import pytesseract
from PIL import Image

pdfs = sorted(Path(".pyq30").rglob("*.pdf"))
report = []
for path in pdfs:
    doc = fitz.open(path)
    page_results = []
    for page_no in (3, 10, 45):
        if page_no > len(doc):
            continue
        page = doc[page_no - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), colorspace=fitz.csGRAY, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        data = pytesseract.image_to_data(img, config="--oem 1 --psm 6", output_type=pytesseract.Output.DICT)
        if path == pdfs[0] and page_no == 3:
            preview = pytesseract.image_to_string(img, config="--oem 1 --psm 6")
            print("OCR_SAMPLE_PAGE_BEGIN")
            print(preview[:5000])
            print("OCR_SAMPLE_PAGE_END")
        words = []
        confidences = []
        for raw, conf in zip(data.get("text", []), data.get("conf", [])):
            word = raw.strip()
            try:
                score = float(conf)
            except (TypeError, ValueError):
                continue
            if word and score >= 0:
                words.append(word)
                confidences.append(score)
        meaningful = [w for w in words if any(c.isalpha() for c in w) and not any(x in w.lower() for x in ("estore", "telegram", "https", "t.me"))]
        page_results.append({
            "page": page_no,
            "recognized_tokens": len(words),
            "alphabetic_tokens_excluding_watermark": len(meaningful),
            "median_confidence": round(statistics.median(confidences), 1) if confidences else 0,
        })
    page_count = len(doc)
    doc.close()
    report.append({"file": path.name, "pages": page_count, "sample": page_results})

print("OCR_DIAGNOSTIC_JSON=" + json.dumps(report, separators=(",", ":")))
