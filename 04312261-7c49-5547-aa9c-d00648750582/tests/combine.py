#!/usr/bin/env python3
"""Stage 3 of two-stage judging: combine the compiled score with the judged score, offline.

trinity's judge_combine.py runs this file in the pinned verifier image with no network and a
read-only root, mounting the stage 1 request at /judge/judge-request.json, the stage 2 scores at
/judge/judge-scores.json, and /logs/verifier as the only writable directory. It writes one
reward.json, in which a judged item only ever lowers the compiled score.
"""

import json
from pathlib import Path

JUDGE, OUT = Path("/judge"), Path("/logs/verifier")


def main() -> None:
    stage = json.loads((Path(__file__).parent / "graded" / "config.json").read_text())["judged"]
    request = json.loads((JUDGE / "judge-request.json").read_text())
    items = {item["id"]: item for item in json.loads((JUDGE / "judge-scores.json").read_text())["items"]}
    weights = stage["two_stage"]["weights"]
    compiled = sum(weight * request["compiled"][name] for name, weight in weights.items()) / sum(weights.values())
    judged = stage["two_stage"]["judged_weights"]
    score = sum(weight * items[name]["score"] for name, weight in judged.items()) / sum(judged.values())
    total = stage["compiled_weight"] + stage["judged_weight"]
    reward = round(compiled * (stage["compiled_weight"] + stage["judged_weight"] * score) / total, 4)
    (OUT / "reward.json").write_text(json.dumps({"reward": reward}))


if __spec__ is None:
    main()
