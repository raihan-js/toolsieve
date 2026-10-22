# toolsieve — decisions (append-only, newest first)

## 2026-10-22 — M0: MCPTox over MCP-TDP, rule-based scoring
- MCP-TDP paper real (arXiv 2605.24069, 32 docker cases) but no public code
  found -> spec risk #1 fallback: MCPTox dataset (response_all.json, pinned
  commit f85189f, SHA-verified, 1,312 valid of 1,348; runtime fetch, never
  redistributed). Upstream carries no explicit licence (noted, eval-use only).
- Scoring will be RULE-BASED (exact tool-call match), not the inspect-eval's
  model judge — house rule, and the single-turn protocol makes it exact.
- MCP Python SDK 2.3.0 installed (2026-07-28 spec surface to verify in M2).
- API spend ($20-40 in spec) NOT approved yet — M1 runs local models only.

## 2026-10-22 — M1 scorer calibrated: 0.81 agreement, conservative direction
- Rule scorer (balanced-span parse + action-verb target + quality-filtered
  evidence) agrees with stored MCPTox judge labels on 10,227 pairs at 0.805
  (diagonals: Ignored 4675+, Direct 2372+, Success 825).
- Bias direction: misses judge-attacks (640+99) more than it invents (300)
  -> rule-measured ASR UNDERSTATES truth (disclosed; safe for defense claims).
- Same scorer grades every arm -> arm comparisons fair regardless. Parser
  bugs caught: greedy-span spanning, flat-match on nested args, NORM default
  swallowing real labels, generic-word evidence.

## 2026-10-22 — M1 llm-jp: model floor (Invalid 1.0, echoes prompts)
- llm-jp-1.8B base cannot follow the single-turn JSON protocol at all
  (echoes prompt / blank). Not a harness bug: protocol needs instruction
  tuning. Moving to Swallow-8B-AWQ (chat + 1-shot). 1.8B result kept as the
  documented capability floor.
- Near-miss: killed an unverified PID alongside vLLM shutdown; owner
  services verified alive after. Rule: PIDs only from same-session ps.

## 2026-10-22 — M1 attack reproduced (Swallow-8B, rule-scored)
- llm-jp-1.8B base: Invalid 1.0 (echoes prompts) — capability floor, kept.
- Swallow-8B-AWQ (chat, 1-shot, n=150 stratified): run1 ASR 0.16 / Invalid
  0.50; run2 (think-strip + full raws) ASR 0.104 / Invalid 0.553.
  Run-to-run gap at temp 0 = reasoning nondeterminism (serve-bench finding
  repeats). UCC-proxy (Ignored/valid) ~0.63. Template-2: 0.0 in run 1.
- Calibration stands: 0.805 judge agreement, conservative direction
  (understates ASR). Same scorer grades all M4 arms.
