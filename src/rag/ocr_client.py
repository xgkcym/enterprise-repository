from __future__ import annotations

import cv2
import httpx
import numpy as np

from core.settings import settings


def _encode_png(img: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".png", img)
    if not success:
        raise RuntimeError("Failed to encode image payload for OCR service request.")
    return encoded.tobytes()


def remote_ocr_image(
    img: np.ndarray,
    *,
    min_score: float,
    language: str | None,
) -> str:
    service_url = (settings.ocr_service_url or "").strip()
    if not service_url:
        raise RuntimeError("OCR_BACKEND is set to remote but OCR_SERVICE_URL is empty.")

    endpoint = f"{service_url.rstrip('/')}/ocr"
    payload = {
        "min_score": str(min_score),
    }
    if language:
        payload["lang"] = language

    try:
        with httpx.Client(timeout=settings.ocr_service_timeout_seconds) as client:
            response = client.post(
                endpoint,
                data=payload,
                files={
                    "file": ("ocr.png", _encode_png(img), "image/png"),
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Remote OCR request failed: {exc}") from exc

    data = response.json()
    text = data.get("text")
    if not isinstance(text, str):
        raise RuntimeError("OCR service returned an invalid response payload.")
    return text
