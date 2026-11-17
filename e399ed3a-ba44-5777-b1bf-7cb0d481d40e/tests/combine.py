#!/usr/bin/env python3
"""Stage 3 of two-stage judging: combine the compiled scores and the judged scores into the reward.

trinity's judge_combine.py runs this file in the pinned verifier image with no network and a
read-only root, mounting the stage 1 request at /judge/judge-request.json, the stage 2 scores at
/judge/judge-scores.json, and /logs/verifier as the only writable directory. A judge score of 1
means the judge found the criterion's statement true, so a prohibition contributes 1 minus it.
reward = compiled x (compiled weight + judged weight x judged score) / total weight.
"""

from __future__ import annotations

import json
from pathlib import Path

TESTS, JUDGE, OUT = Path("/tests"), Path("/judge"), Path("/logs/verifier")


def weighted(pairs: list[tuple[float, float]]) -> float:
    return sum(weight * value for weight, value in pairs) / sum(weight for weight, _ in pairs)


def main() -> None:
    judged_plan = json.loads((TESTS / "graded" / "config.json").read_text())["judged"]
    request = json.loads((JUDGE / "judge-request.json").read_text())
    scores = json.loads((JUDGE / "judge-scores.json").read_text())
    compiled_weight = sum(judged_plan["compiled"].values())
    compiled = weighted([(weight, request["compiled"][item]) for item, weight in judged_plan["compiled"].items()])
    scored = {row["id"]: row for row in scores["items"]}
    pairs, missing = [], []
    for item in judged_plan["items"]:
        holds = scored.get(item["id"], {}).get("score")
        if holds is None:
            missing.append(item["id"])
            continue
        pairs.append((item["weight"], 1.0 - holds if item["negate"] else holds))
    judged_weight = sum(item["weight"] for item in judged_plan["items"])
    if missing:
        reward, judged = compiled, None
        reason = f"stage 2 scored no verdict for {missing}, so the reward is the compiled score"
    else:
        judged = weighted(pairs)
        reward = compiled * (compiled_weight + judged_weight * judged) / (compiled_weight + judged_weight)
        reason = "compiled x (compiled weight + judged weight x judged score) / total weight"
    reward = round(reward, 4)
    (OUT / "reward.json").write_text(json.dumps({"reward": reward}, indent=2))
    (OUT / "reward-details.json").write_text(json.dumps(
        {"reward": reward, "compiled": compiled, "judged": judged, "reason": reason,
         "items": {item: scored[item] for item in scored}}, indent=2))


# A script run has no module spec; an import (as Reward Kit scans do) does, so it runs nothing.
if __spec__ is None:
    main()
