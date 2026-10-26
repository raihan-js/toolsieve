# ToolSieve

Does canonicalising MCP tool descriptions stop tool poisoning?

A gateway rewrites every tool description into a fixed schema
(`purpose`/`params`/`returns`/`side-effects`), stripping free-text
instructions where poison payloads hide. Measures attack success rate (ASR)
and utility-completion (UCC) across baseline vs three canonicalisers
(rules-only strip, schema-only drop, model rewrite), plus an adaptive
attacker targeting the canonicaliser itself.

## Results

Rule-scored on MCPTox (FAR/DFARS-adjacent tool set), Swallow-8B-AWQ agent:

| Arm | ASR (top-1) | UCC proxy |
|-----|-------------|-----------|
| none (baseline) | 0.138 | 0.828 |
| rules-strip | 0.114 | 0.684 |
| schema-only | 0.078 | 0.696 |
| model-rewrite | 0.080 | 0.690 |

All arms: 367 instances, Wilson 95% CIs. Adaptive attacks (param-smuggle,
anti-canonicaliser, split) running — see `results/`.

## Reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/
```

Rule-based scoring throughout — no LLM judge. Exact tool-call match decides
Success/Ignored, so per-item results are auditable.

## Responsible disclosure

Payloads are at published-benchmark level only; no new working exploits
against named vendors' production servers.
