#!/usr/bin/env python3
"""Measure OCR readability and identify likely MCQ pages without logging source text."""
from pathlib import Path
import io
import json
import re
import statistics
import fitz
import pytesseract
from PIL import Image

pdfs = sorted(Path(".pyq30").rglob("*.pdf"))
report = []
for path in pdfs:
    doc = fitz.open(path)
    page_results = []
    sample_pages = sorted(set(p for p in (1, 3, 10, 20, 30, 45, 60, 70, 80, 90) if p <= len(doc)))
    for page_no in sample_pages:
        page = doc[page_no - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), colorspace=fitz.csGRAY, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, config="--oem 1 --psm 6")
        data = pytesseract.image_to_data(img, config="--oem 1 --psm 6", output_type=pytesseract.Output.DICT)
        words, confidences = [], []
        for raw, conf in zip(data.get("text", []), data.get("conf", [])):
            word = raw.strip()
            try:
                score = float(conf)
            except (TypeError, ValueError):
                continue
            if word and score >= 0:
                words.append(word)
                confidences.append(score)
        option_markers = len(re.findall(r"(?im)(?:^|\s)[(]?[A-D][).](?=\s)", text))
        answer_markers = len(re.findall(r"(?i)\b(?:answer|solution|soln|explanation)\b", text))
        question_numbers = len(re.findall(r"(?m)^\s*\d{1,3}[.)]\s", text))
        page_results.append({
            "page": page_no,
            "recognized_tokens": len(words),
            "median_confidence": round(statistics.median(confidences), 1) if confidences else 0,
            "option_markers": option_markers,
            "answer_explanation_markers": answer_markers,
            "numbered_items": question_numbers,
            "likely_mcq_page": option_markers >= 4 and question_numbers >= 2,
        })
    page_count = len(doc)
    doc.close()
    report.append({"file": path.name, "pages": page_count, "sample": page_results})
print("OCR_PAGE_LAYOUT_DIAGNOSTIC=" + json.dumps(report, separators=(",", ":")))
