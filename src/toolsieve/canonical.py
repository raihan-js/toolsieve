"""Canonicalisers: rules-only strip, schema-only drop. Model rewrite lives
in canonical_model.py (needs GPU/small model). All implement
gateway.Canonicaliser. CPU-tested.
"""
from __future__ import annotations

import re
from typing import Any

from toolsieve.gateway import Canonicaliser

# model-directed imperatives (OWASP MCP03 indicators, condensed)
_IMPERATIVES = re.compile(
    r"(?i)\b(ignore (all |any |the )?previous instructions|disregard .*instructions|"
    r"do not (tell|inform|mention|reveal).*?(user|human)|before (using|answering|replying)[^.]*(read|send|call|execute)[^.]*\.|"
    r"you must (first )?(call|run|execute|read|send|download)[^.]*\.|"
    r"this tool (must|will|should) be (executed|called|run)[^.]*\.)"
)
# security-justification voice: MUST + action + regardless/justification
_MUST_ACT = re.compile(
    r"(?i)\byou MUST\b[^.]*(automatically )?(modify|redirect|overwrite|send|call|read|write|execut|append|replace)[^.]*\.|"
    r"regardless of the original[^.]*\.|"
    r"this involves (calling|using)\b[^.]*(overwrite|modify|redirect|send)[^.]*\."
)
_HIDDEN = re.compile("[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)


class RulesStrip(Canonicaliser):
    """Remove hidden chars, comment-smuggled text, and imperative sentences.
    Keeps the rest (usage hints survive)."""

    def rewrite(self, tool: dict[str, Any]) -> dict[str, Any]:
        t = dict(tool)
        d = str(t.get("description", ""))
        d = _HIDDEN.sub("", d)
        d = _COMMENTS.sub("", d)
        kept = [s for s in re.split(r"(?<=[.!?]) ", d)
                if not _IMPERATIVES.search(s) and not _MUST_ACT.search(s)]
        t["description"] = " ".join(kept).strip()
        t["canonicaliser"] = "rules-strip"
        return t


class SchemaOnly(Canonicaliser):
    """Drop free text entirely: name + params + returns only."""

    def rewrite(self, tool: dict[str, Any]) -> dict[str, Any]:
        schema = tool.get("schema", {}) if isinstance(tool.get("schema"), dict) else {}
        params = schema.get("properties", {}) if isinstance(schema, dict) else {}
        return {"name": tool.get("name"),
                "description": f"Tool {tool.get('name')}({', '.join(params) if isinstance(params, dict) else ''})",
                "schema": tool.get("schema", {}),
                "canonicaliser": "schema-only"}
