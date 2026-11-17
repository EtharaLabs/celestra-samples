"""Score the graded run with Reward Kit: the compiled criteria, then any judged items, combined so a
judged item only ever lowers the reward.

run_graded.py has already written /logs/verifier/graded.json. The compiled criteria score first, and
a compiled score of 0 is final: no judge call runs. With no judge credential in the environment
(ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN, passed from the grader's host through [verifier.env])
the judged items are not run and the reward is the compiled score. Otherwise Reward Kit grades
tests/judge.toml in one call; a judge run that fails, such as an outage, also leaves the compiled
score. The reward is compiled x (compiled weight + judged weight x judged) / (compiled weight + judged
weight). A two-stage bundle (ADR 0212) makes no judge call here: it writes the compiled score and
judge-request.json, and its tests/combine.py applies the judged score later. Every path
leaves its reason in reward-details.json beside the reward file test.sh names as the argument.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

LOGS = Path("/logs/verifier")
TESTS = Path("/tests")
CONFIG = json.loads((TESTS / "graded" / "config.json").read_text())
CREDENTIALS = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")


def reward_kit(name: str, files: tuple[str, ...], env: dict[str, str]) -> tuple[float | None, object, str]:
    # Reward Kit imports every .py file and reads every .toml file it scans, and treats a child
    # directory as a group, so it reads a fresh directory holding only these files and writes elsewhere.
    scan, out = Path("/tmp") / name, Path("/tmp") / f"{name}-out"
    for directory in (scan, out):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    for file in files:
        shutil.copyfile(TESTS / file, scan / file)
    done = subprocess.run(["rewardkit", str(scan), "--workspace", "/grading/repo", "--output", str(out / "reward.json")],
                          env=env, capture_output=True, text=True, check=False)
    error = f"exit {done.returncode}: {done.stderr[-2000:]}"
    try:
        reward = float(json.loads((out / "reward.json").read_text())["reward"])
        details = json.loads((out / "reward-details.json").read_text())
    except (OSError, ValueError, KeyError, TypeError):
        return None, None, error
    return (reward, details, error) if done.returncode == 0 else (None, details, error)


def criterion_scores(details: object) -> dict[str, float]:
    """Every compiled criterion's value from Reward Kit's details, by criterion name."""
    found: dict[str, float] = {}
    pending = [details]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if isinstance(node.get("criteria"), list):
                found.update({str(c["name"]): float(c["value"]) for c in node["criteria"] if isinstance(c, dict)})
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    return found


def write_request(stage: dict[str, object], compiled: dict[str, float]) -> None:
    """ADR 0212 stage 1: the trinity.judge-request/v1 record stage 2 reads, among the verifier artifacts."""
    request = {
        "schemaVersion": "trinity.judge-request/v1",
        **{key: stage[key] for key in ("provider", "model", "temperature", "seed", "trials", "passLabel")},
        "prompt": (TESTS / "judge" / "prompt.md").read_text(),
        "items": stage["items"],
        "output": (LOGS / "submission.diff").read_text(),
        "compiled": compiled,
    }
    (LOGS / "judge-request.json").write_text(json.dumps(request, sort_keys=True, ensure_ascii=False))


def combine() -> tuple[float, dict[str, object]]:
    env = dict(os.environ)
    for key in CREDENTIALS:
        if not env.get(key):
            env.pop(key, None)
    compiled, details, error = reward_kit("compiled", ("test_output.py", "reward.toml"), env)
    detail: dict[str, object] = {"compiled": {"score": compiled, "details": details}}
    judged = CONFIG.get("judged")
    if compiled is None:
        return 0.0, {**detail, "reason": "the compiled criteria did not score: " + error}
    if not judged:
        return compiled, detail
    if judged.get("two_stage"):
        write_request(judged["two_stage"], criterion_scores(details))
        return compiled, {**detail, "judged": {"status": "pending", "reason": "two-stage judging: the verifier writes "
                                               "the compiled score and judge-request.json; stages 2 and 3 run outside it"}}
    if not compiled:
        return 0.0, {**detail, "judged": {"status": "skipped", "reason": "the compiled score is 0, so no judge call runs"}}
    if not any(env.get(key) for key in CREDENTIALS):
        return compiled, {**detail, "judged": {"status": "not run", "reason": "no judge credential "
                                               "(ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN) is set; the reward is the compiled score"}}
    score, details, error = reward_kit("judged", ("judge.toml",), env)
    if score is None:
        return compiled, {**detail, "judged": {"status": "failed", "details": details,
                                               "reason": "the judge run did not score; the reward is the compiled score: " + error}}
    status: dict[str, object] = {"status": "run", "score": score, "details": details}
    weights = judged["compiled_weight"], judged["judged_weight"]
    reward = round(compiled * (weights[0] + weights[1] * score) / (weights[0] + weights[1]), 4)
    return reward, {**detail, "judged": status,
                    "formula": f"compiled x ({weights[0]} + {weights[1]} x judged) / {weights[0] + weights[1]}"}


def main() -> None:
    target = Path(sys.argv[1])
    try:
        reward, detail = combine()
    except Exception as error:  # any scoring failure must still leave a reward and its reason
        reward, detail = 0.0, {"reason": f"scoring failed: {type(error).__name__}: {error}"}
    target.write_text(json.dumps({"reward": reward}, indent=2))
    (target.parent / "reward-details.json").write_text(json.dumps({"reward": reward, **detail}, indent=2))


# A script run has no module spec; an import (as Reward Kit scans do) does, so it runs nothing.
if __spec__ is None:
    main()
