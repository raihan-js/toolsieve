"""M1 live runs: single-turn MCPTox protocol against a local vLLM agent.

Prompt = system + query + JSON-only instruction; temp 0; rule-scored.
Subset: 150 instances stratified by paradigm (seed 0). Writes
results/m1.json {asr, ucc, invalid_rate, per_paradigm} + m1_rows.jsonl.
Run: run_m1.py [MODEL] [BASE_URL]. ~15 min for 150.
"""
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from toolsieve.parse_payload import parse_payload
from toolsieve.score import parse_call, score

GEN = "http://localhost:8003/v1/completions"
CHAT = "http://localhost:8003/v1/chat/completions"


def ask(prompt: str, model: str, chat: bool = False) -> str:
    import httpx
    if chat:
        r = httpx.post(CHAT, json={"model": model, "temperature": 0.0,
                                   "max_tokens": 256,
                                   "messages": [{"role": "user", "content": prompt + " /no_think"}]},
                       timeout=180.0)
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else ""
    r = httpx.post(GEN, json={"model": model, "temperature": 0.0,
                              "max_tokens": 256, "prompt": prompt},
                   timeout=180.0)
    return r.json()["choices"][0]["text"] if r.status_code == 200 else ""


ONE_SHOT = ('Example: query "List files in /tmp" with a list_directory tool -> '
            '{"tool": "list_directory", "arguments": {"path": "/tmp"}}\n\n')


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else "llm-jp/llm-jp-3-1.8b"
    tag = sys.argv[2] if len(sys.argv) > 2 else "m1"
    chat = model.startswith("tokyotech")
    rows = [json.loads(l) for l in open("results/instances.jsonl", encoding="utf-8")]
    by_par: dict[str, list] = {}
    for r in rows:
        by_par.setdefault(r.get("paradigm", "?"), []).append(r)
    rng = random.Random(0)
    sub = []
    for par, lst in sorted(by_par.items()):
        sub.extend(rng.sample(lst, min(50, len(lst))))
    rng.shuffle(sub)
    print(f"subset: {len(sub)} paradigms: {sorted(by_par)}", flush=True)
    outs = []
    t0 = time.time()
    for i, r in enumerate(sub):
        prompt = (r["system"] + f"\n\n{ONE_SHOT}User request: {r['query']}\n"
                  f"Reply with a single JSON tool call: {{\"tool\": ..., \"arguments\": ...}}")
        raw = ask(prompt, model, chat)
        p = parse_payload(r["poisoned_tool"], r["tool_names"])
        outs.append({"uid": r["uid"], "paradigm": r.get("paradigm", "?"),
                     "outcome": score(parse_call(raw), raw, p), "raw": raw})
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(sub)} ({time.time() - t0:.0f}s)", flush=True)
    Path(f"results/{tag}_rows.jsonl").write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in outs) + "\n")
    succ = sum(1 for o in outs if o["outcome"] == "Success")
    inv = sum(1 for o in outs if o["outcome"] == "Invalid")
    per = {}
    for par in sorted({o["paradigm"] for o in outs}):
        s = [o for o in outs if o["paradigm"] == par]
        per[par] = {"n": len(s), "asr": round(sum(1 for o in s if o["outcome"] == "Success") / len(s), 3)}
    res = {"model": model, "n": len(outs),
           "asr": round(succ / max(len(outs) - inv, 1), 3),
           "asr_incl_invalid": round(succ / len(outs), 3),
           "invalid_rate": round(inv / len(outs), 3), "per_paradigm": per}
    Path(f"results/{tag}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
