# ToolSieve — does canonicalising MCP tool descriptions stop tool poisoning?

Question: a gateway rewrites every tool description into a fixed schema
(purpose/params/returns/side-effects), stripping free-text instructions.
Does attack success fall without breaking task completion — including
against an adaptive attacker targeting the canonicaliser itself?

Spec: ideas-v3 `toolsieve` (4 wks). Study pack: `05-ai-security-...md`.
Responsible disclosure: no new working exploits against named vendors'
production servers; payloads only at published-benchmark level.

## Milestones
- M0 (done): MCPTox dataset fetched (1,312 valid of 1,348) with SHA verify;
  MCP-TDP code not public (fallback per spec risk #1); MCP SDK 2.3.0.
- M1: reproduce the attack — single-turn protocol, local agent, RULE-BASED
  scoring (no LLM judge: exact tool-call match decides Success/Ignored).
- M2: gateway (2026-07-28 spec surface, pinning + diff alerts, audit log,
  canonicaliser plug-in point).
- M3: three canonicalisers (rules-only strip, small-model JSON rewrite,
  schema-only drop) with unit tests.
- M4: ASR + UCC per agent x canonicaliser with 95% CIs + adaptive attacker
  (payloads in param names/enums/examples, anti-canonicaliser instructions).
  Pre-registered before running.
- M5: release (gateway package, results dataset, article).
