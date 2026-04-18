from __future__ import annotations

import os

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

app = FastAPI(title="OCR Service", version="1.0.0")

_ocr_instances: dict[str, object] = {}


def _get_ocr(lang: str):
    cached = _ocr_instances.get(lang)
    if cached is not None:
        return cached

    from paddleocr import PaddleOCR

    instance = PaddleOCR(lang=lang)
    _ocr_instances[lang] = instance
    return instance


def _preprocess_image(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ocr")
async def run_ocr(
    file: UploadFile = File(...),
    min_score: float = Form(0.0),
    lang: str = Form("ch"),
) -> dict[str, object]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file payload.")

    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise HTTPException(status_code=400, detail="Unsupported image payload.")

    ocr = _get_ocr(lang or "ch")
    result = ocr.ocr(_preprocess_image(img))

    lines = []
    for line in result[0] if result and result[0] else []:
        try:
            text, score = line[1]
        except Exception:
            continue
        normalized_text = text.replace("\n", " ").strip()
        normalized_score = float(score)
        if normalized_text and normalized_score >= min_score:
            lines.append(
                {
                    "text": normalized_text,
                    "score": normalized_score,
                }
            )

    return {
        "text": "\n".join(item["text"] for item in lines),
        "lines": lines,
        "lang": lang or "ch",
    }
