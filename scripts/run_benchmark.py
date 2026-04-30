from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def resolve_output_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()

    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.parent.exists():
        return cwd_candidate
    return (ROOT_DIR / candidate).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline QA benchmark from MongoDB QA data.")
    parser.add_argument(
        "--export-path",
        type=str,
        default=None,
        help="Optional JSON export path for the benchmark summary.",
    )
    return parser.parse_args()


def run_benchmark() -> dict[str, Any]:
    from src.rag.rag_service import rag_service

    return rag_service.benchmark()


def write_export_payload(output_path: str | None, summary: dict[str, Any]) -> str | None:
    if not output_path:
        return None

    resolved_path = resolve_output_path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(resolved_path)


def main() -> None:
    args = parse_args()
    summary = run_benchmark()
    export_path = write_export_payload(args.export_path, summary)
    if export_path:
        summary = dict(summary)
        summary["export_path"] = export_path
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
