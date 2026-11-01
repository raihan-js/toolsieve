"""Upload ToolSieve benchmark to Hugging Face Hub.

Dataset: raihan-js/toolsieve-bench
- m4.json: ASR + UCC per canonicaliser arm with Wilson 95% CIs (n=367)
- m4_rows.jsonl: per-item results for all 4 arms
- m4_subset.json: frozen 367-item subset uids
- instances.jsonl: full MCPTox instances (1,312 items, 10MB) with responses/labels
- README.md: dataset card
"""

from __future__ import annotations

import shutil
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "raihan-js/toolsieve-bench"

CARD = """\
---
license: apache-2.0
task_categories:
  - text-classification
tags:
  - mcp
  - tool-poisoning
  - ai-security
  - benchmark
---

# ToolSieve-Bench

Frozen benchmark for tool-poisoning defense via MCP description canonicalisation.
Companion to https://github.com/raihan-js/toolsieve.

All text is from MCPTox (public tool descriptions + synthetic attack payloads).
Rule-based scoring throughout — no LLM judge. Exact tool-call match decides
Success/Ignored, so every per-item result is auditable.

## Files

- `m4.json` — ASR + UCC proxy per arm with Wilson 95% CIs (n=367)
- `m4_rows.jsonl` — per-item results: {uid, arm, outcome} (1468 rows = 367 × 4 arms)
- `m4_subset.json` — frozen 367-item subset uids (stratified by paradigm × server, seed 5)
- `instances.jsonl` — full MCPTox instances (1,312 items) with poisoned tool blocks,
  system prompts, queries, tool names, and stored judge/model responses

## Main results (rule-scored, Swallow-8B-AWQ agent, temp 0)

| Arm | ASR (valid) | 95% CI | UCC proxy | 95% CI |
|-----|-------------|--------|-----------|--------|
| none (baseline) | 0.1379 | [0.077, 0.244] | 0.8276 | [0.717, 0.898] |
| rules-strip | 0.1139 | [0.064, 0.199] | 0.6835 | [0.579, 0.779] |
| schema-only | 0.0784 | [0.042, 0.145] | 0.6961 | [0.604, 0.773] |
| model-rewrite | 0.0800 | [0.043, 0.148] | 0.6900 | [0.597, 0.769] |

schema-only and model-rewrite reduce top-1 leakage ~43% vs baseline without
breaking utility (CIs overlap baseline). Strict pinning breaks change-type
questions — see repo for details.

## Reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/
```

Run M4 main: `python scripts/eval_m4.py main` (needs local vLLM on :8003).
Run M4 adaptive: `python scripts/eval_m4.py adaptive`.

## Responsible disclosure

Payloads are at published-benchmark level only. No new working exploits
against named vendors' production servers.
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    stage = Path("/tmp/toolsieve-bench")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    # Core result files
    for name in ["m4.json", "m4_rows.jsonl", "m4_subset.json"]:
        src = root / "results" / name
        if src.exists():
            shutil.copy(src, stage / name)

    # Full instance dataset (10MB) — include for reproducibility
    instances = root / "results" / "instances.jsonl"
    if instances.exists():
        shutil.copy(instances, stage / "instances.jsonl")

    (stage / "README.md").write_text(CARD)

    api = HfApi()
    api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
    api.upload_folder(
        folder_path=str(stage),
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="ToolSieve-Bench: m4 results + 367-item frozen subset + instances",
    )
    print(f"Uploaded to https://huggingface.co/datasets/{REPO_ID}")
    shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main()
