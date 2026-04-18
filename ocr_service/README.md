# OCR Service

This directory contains an isolated OCR microservice so the main application can keep its current dependency tree while OCR runs in a separate virtual environment.

## Why it exists

- The main application no longer installs `PaddleOCR` locally.
- `PaddleOCR 3.x` works better in a dedicated environment because it pulls `paddlex` and related packages that conflict with the main app stack.
- Running OCR in its own environment avoids that dependency collision entirely.

## Quick start

```powershell
cd ocr_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8016
```

## Main app configuration

Set these variables in the main application's `.env`:

```env
OCR_SERVICE_URL=http://127.0.0.1:8016
OCR_SERVICE_TIMEOUT_SECONDS=30
OCR_LANG=ch
OCR_MIN_SCORE=0.5
```
