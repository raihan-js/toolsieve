"""Tiny IO helpers (shared by scripts)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
