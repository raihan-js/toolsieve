"""ToolSieve gateway: registry, pinning, audit, canonicaliser plug-in.

Scope (disclosed): in-process tool registry + FastAPI front (list/call),
description pinning (sha256 + diff alerts), append-only audit log, cached
list results, header policy log (Mcp-Method/Mcp-Name passthrough per the
2026-07-28 stateless surface). Upstream MCP proxying is out of scope for M2
(tools registered from JSON snapshots of real servers).
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def sha(tool: dict[str, Any]) -> str:
    blob = json.dumps({"name": tool.get("name"), "description": tool.get("description"),
                       "schema": tool.get("schema", {})}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class Canonicaliser:
    """Plug-in point: rewrite(tool) -> tool. Identity default."""

    def rewrite(self, tool: dict[str, Any]) -> dict[str, Any]:
        return tool


class Gateway:
    def __init__(self, audit_path: str | Path = "results/audit.jsonl"):
        self.tools: dict[str, dict[str, Any]] = {}
        self.pins: dict[str, str] = {}
        self.alerts: list[dict[str, Any]] = []
        self.audit_path = Path(audit_path)
        self._list_cache: dict[str, list[dict[str, Any]]] = {}
        self.canonicaliser: Canonicaliser = Canonicaliser()

    def audit(self, event: str, **kw: Any) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "event": event, **kw}) + "\n")

    def register(self, tool: dict[str, Any], server: str = "local") -> None:
        tool = dict(tool)
        tool["server"] = server
        digest = sha(tool)
        name = tool["name"]
        if name in self.pins and self.pins[name] != digest:
            self.alerts.append({"tool": name, "old": self.pins[name],
                                "new": digest, "t": time.time()})
            self.audit("pin-diff", tool=name)
        self.pins[name] = digest
        self.tools[name] = tool
        self._list_cache.clear()
        self.audit("register", tool=name, server=server)

    def list_tools(self, use_cache: bool = True) -> list[dict[str, Any]]:
        if use_cache and "all" in self._list_cache:
            return self._list_cache["all"]
        out = [self.canonicaliser.rewrite(dict(t)) for t in self.tools.values()]
        self._list_cache["all"] = out
        self.audit("list", n=len(out), cached=False)
        return out

    def call(self, name: str, args: dict[str, Any],
             handler: Callable[[str, dict[str, Any]], Any] | None = None,
             headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Validate args against the tool schema (required keys present),
        log headers policy (Mcp-Method/Mcp-Name passthrough), dispatch to
        handler or echo-stub. Never executes anything itself."""
        if name not in self.tools:
            self.audit("call-reject", tool=name, reason="unknown")
            return {"ok": False, "error": "unknown tool"}
        schema = self.tools[name].get("schema", {})
        required = schema.get("required", []) if isinstance(schema, dict) else []
        missing = [k for k in required if k not in args]
        self.audit("call", tool=name, headers=headers or {}, missing=missing)
        if missing:
            return {"ok": False, "error": f"missing args: {missing}"}
        if handler is None:
            return {"ok": True, "stub": True, "tool": name, "args": args}
        try:
            return {"ok": True, "result": handler(name, args)}
        except (RuntimeError, ValueError, KeyError) as e:
            self.audit("call-error", tool=name, error=type(e).__name__)
            return {"ok": False, "error": type(e).__name__}
