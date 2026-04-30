from __future__ import annotations

import threading

import cv2
import httpx
import numpy as np

from core.settings import settings


_ocr_request_limiter: threading.BoundedSemaphore | None = None
_ocr_request_limiter_size: int | None = None


def _get_ocr_request_limiter() -> threading.BoundedSemaphore:
    global _ocr_request_limiter, _ocr_request_limiter_size

    limiter_size = max(1, settings.ocr_client_max_concurrency)
    if _ocr_request_limiter is None or _ocr_request_limiter_size != limiter_size:
        _ocr_request_limiter = threading.BoundedSemaphore(limiter_size)
        _ocr_request_limiter_size = limiter_size
    return _ocr_request_limiter


def _maybe_resize_for_remote(img: np.ndarray) -> np.ndarray:
    max_side = max(1, settings.ocr_max_image_side)
    height, width = img.shape[:2]
    longest_side = max(height, width)
    if longest_side <= max_side:
        return img

    scale = max_side / float(longest_side)
    resized_width = max(1, int(round(width * scale)))
    resized_height = max(1, int(round(height * scale)))
    return cv2.resize(img, (resized_width, resized_height), interpolation=cv2.INTER_AREA)


def _encode_png(img: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".png", img)
    if not success:
        raise RuntimeError("无法为 OCR 服务请求编码图片负载。")
    return encoded.tobytes()


def _build_timeout() -> httpx.Timeout:
    total_timeout = max(1.0, settings.ocr_service_timeout_seconds)
    connect_timeout = min(5.0, total_timeout)
    return httpx.Timeout(
        connect=connect_timeout,
        read=total_timeout,
        write=total_timeout,
        pool=connect_timeout,
    )


def _format_failure_context(
    *,
    endpoint: str,
    original_shape: tuple[int, int],
    payload_shape: tuple[int, int],
    attempts: int,
) -> str:
    return (
        f"endpoint={endpoint}, timeout={settings.ocr_service_timeout_seconds}s, "
        f"attempts={attempts}, image={original_shape[1]}x{original_shape[0]}, "
        f"payload={payload_shape[1]}x{payload_shape[0]}"
    )


def remote_ocr_image(
    img: np.ndarray,
    *,
    min_score: float,
    language: str | None,
) -> str:
    service_url = (settings.ocr_service_url or "").strip()
    if not service_url:
        raise RuntimeError("无法执行远程 OCR：OCR_BACKEND 已设置为 remote，但 OCR_SERVICE_URL 为空。")

    endpoint = f"{service_url.rstrip('/')}/ocr"
    payload = {
        "min_score": str(min_score),
    }
    if language:
        payload["lang"] = language

    prepared_img = _maybe_resize_for_remote(img)
    payload_shape = prepared_img.shape[:2]
    original_shape = img.shape[:2]
    encoded_payload = _encode_png(prepared_img)
    attempts = max(1, settings.ocr_inference_recovery_retries + 1)
    limiter = _get_ocr_request_limiter()

    limiter.acquire()
    try:
        last_exception: httpx.HTTPError | None = None
        response: httpx.Response | None = None
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=_build_timeout()) as client:
                    response = client.post(
                        endpoint,
                        data=payload,
                        files={
                            "file": ("ocr.png", encoded_payload, "image/png"),
                        },
                    )
                    response.raise_for_status()
                break
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exception = exc
                if attempt >= attempts:
                    context = _format_failure_context(
                        endpoint=endpoint,
                        original_shape=original_shape,
                        payload_shape=payload_shape,
                        attempts=attempts,
                    )
                    raise RuntimeError(f"远程 OCR 请求失败: {context}: {exc}") from exc
                continue
            except httpx.HTTPStatusError as exc:
                context = _format_failure_context(
                    endpoint=endpoint,
                    original_shape=original_shape,
                    payload_shape=payload_shape,
                    attempts=attempt,
                )
                raise RuntimeError(f"远程 OCR 请求失败: {context}: {exc}") from exc
            except httpx.HTTPError as exc:
                context = _format_failure_context(
                    endpoint=endpoint,
                    original_shape=original_shape,
                    payload_shape=payload_shape,
                    attempts=attempt,
                )
                raise RuntimeError(f"远程 OCR 请求失败: {context}: {exc}") from exc
        else:
            context = _format_failure_context(
                endpoint=endpoint,
                original_shape=original_shape,
                payload_shape=payload_shape,
                attempts=attempts,
            )
            detail = last_exception or "unknown error"
            raise RuntimeError(f"远程 OCR 请求失败: {context}: {detail}")
    finally:
        limiter.release()

    if response is None:
        raise RuntimeError("服务返回了空的 OCR 响应。")

    data = response.json()
    text = data.get("text")
    if not isinstance(text, str):
        raise RuntimeError("服务返回了无效的 OCR 响应负载。")
    return text
