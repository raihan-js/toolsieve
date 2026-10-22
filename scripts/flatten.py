"""Flatten MCPTox to instances (CPU). Skips wrong_data. Writes
results/instances.jsonl {uid, server, paradigm, risk, query, system,
poisoned_tool, tool_names, labels, response}."""
import json


def main() -> None:
    with open("data/response_all.json", encoding="utf-8") as _f:
        d = json.load(_f)
    n = 0
    with open("results/instances.jsonl", "w", encoding="utf-8") as f:
        for sname, s in d["servers"].items():
            for mi in s.get("malicious_instance", []):
                if mi.get("wrong_data", 0):
                    continue
                meta = mi.get("metadata", {}) or {}
                for x in mi.get("datas", []):
                    f.write(json.dumps({
                        "uid": f"{sname}:{x.get('id')}",
                        "server": sname,
                        "paradigm": meta.get("paradigm", "?"),
                        "risk": meta.get("security risk", "?"),
                        "query": x.get("query", ""),
                        "system": x.get("system", ""),
                        "poisoned_tool": x.get("poisoned_tool", ""),
                        "tool_names": s.get("tool_names", []),
                        "labels": x.get("label", {}),
                        "response": x.get("response", {}),
                    }, ensure_ascii=False) + "\n")
                    n += 1
    print("instances:", n)


if __name__ == "__main__":
    main()
