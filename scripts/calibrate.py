"""Calibrate rule scorer vs stored judge labels (CPU).

Replays every stored model response through parse_payload+score, compares
with the dataset's label for that (instance, model). Writes
results/calibration.json {agreement, confusion, per_model, no_target_rate}.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from toolsieve.parse_payload import parse_payload
from toolsieve.score import parse_call, score

NORM = {"Failure-Direct Execution": "Failure-Direct", "None": "Invalid",
        "null": "Invalid", None: "Invalid"}


def norm_label(lab: str | None) -> str:
    if lab in NORM:
        return NORM[lab]  # type: ignore[index]
    return lab if lab in ("Success", "Failure-Ignored", "Failure-Direct",
                          "Failure-Refused", "Invalid") else "Invalid"


def main() -> None:
    rows = [json.loads(l) for l in open("results/instances.jsonl", encoding="utf-8")]
    agree = tot = no_target = 0
    conf: Counter = Counter()
    per_model: dict[str, Counter] = {}
    for r in rows:
        p = parse_payload(r["poisoned_tool"], r["tool_names"])
        if p["target_tool"] is None:
            no_target += 1
        for model, raw in (r.get("response") or {}).items():
            gold = norm_label((r.get("labels") or {}).get(model))
            mine = score(parse_call(raw or ""), raw or "", p)
            # Invalid-vs-Invalid agreement is vacuous; track separately
            conf[(gold, mine)] += 1
            tot += 1
            agree += int(gold == mine)
            pm = per_model.setdefault(model, Counter())
            pm[(gold, mine)] += 1
    res = {"pairs": tot, "agreement": round(agree / tot, 3),
           "no_target_rate": round(no_target / len(rows), 3),
           "confusion": {f"{g}>{m}": n for (g, m), n in conf.most_common(12)}}
    Path("results/calibration.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
