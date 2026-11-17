"""Score the graded run with Reward Kit's compiled criteria; stage 1 of two-stage judging.

run_graded.py has already written /logs/verifier/graded.json. Reward Kit scores tests/test_output.py
under tests/reward.toml with no network and no credential. A scoring failure leaves reward 0, and every
path leaves its reason in reward-details.json beside the reward file test.sh names as the argument.
When the rubric holds judged items and the compiled score is above 0, it also writes
judge-request.json (trinity.judge-request/v1) beside the reward for stage 2 on the host; the reward
it writes stays the compiled score, which tests/combine.py lowers in stage 3.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

LOGS = Path("/logs/verifier")
TESTS = Path("/tests")
CONFIG = json.loads((TESTS / "graded" / "config.json").read_text())


def reward_kit(name: str, files: tuple[str, ...]) -> tuple[float | None, object, str]:
    # Reward Kit imports every .py file and reads every .toml file it scans, and treats a child
    # directory as a group, so it reads a fresh directory holding only these files and writes elsewhere.
    scan, out = Path("/tmp") / name, Path("/tmp") / f"{name}-out"
    for directory in (scan, out):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    for file in files:
        shutil.copyfile(TESTS / file, scan / file)
    done = subprocess.run(["rewardkit", str(scan), "--workspace", "/grading/repo", "--output", str(out / "reward.json")],
                          capture_output=True, text=True, check=False)
    error = f"exit {done.returncode}: {done.stderr[-2000:]}"
    try:
        reward = float(json.loads((out / "reward.json").read_text())["reward"])
        details = json.loads((out / "reward-details.json").read_text())
    except (OSError, ValueError, KeyError, TypeError):
        return None, None, error
    return (reward, details, error) if done.returncode == 0 else (None, details, error)


def item_scores(details: object) -> dict[str, float]:
    components = details["reward"]["components"]  # type: ignore[index]
    return {row["name"]: float(row["value"]) for part in components for row in part["detail"]["criteria"]}


def judge_request(target: Path, compiled: float, details: object) -> dict[str, object]:
    judged = CONFIG.get("judged")
    if not judged:
        return {}
    if compiled <= 0:
        return {"judged": {"status": "skipped", "reason": "the compiled score is 0, so no judge request is written"}}
    controls = TESTS / "judge-controls"
    items = [{"id": item["id"], "criterion": item["criterion"],
              "controls": [{"caseId": row["case"], "referenceLabel": row["label"],
                            "output": (controls / f"{row['case']}.diff").read_text()}
                           for row in judged["controls"].get(item["id"], [])]}
             for item in judged["items"]]
    request = {"schemaVersion": "trinity.judge-request/v1", **judged["pinned"],
               "prompt": (TESTS / "judge" / "prompt.md").read_text(), "items": items,
               "output": (LOGS / "submission.diff").read_text(), "compiled": item_scores(details)}
    path = target.parent / "judge-request.json"
    path.write_text(json.dumps(request, sort_keys=True, ensure_ascii=False))
    return {"judged": {"status": "requested", "request": str(path)}}


def combine(target: Path) -> tuple[float, dict[str, object]]:
    compiled, details, error = reward_kit("compiled", ("test_output.py", "reward.toml"))
    detail: dict[str, object] = {"compiled": {"score": compiled, "details": details}}
    if compiled is None:
        return 0.0, {**detail, "reason": "the compiled criteria did not score: " + error}
    try:
        detail |= judge_request(target, compiled, details)
    except Exception as failure:  # a request failure must never cost the compiled score
        detail["judged"] = {"status": "failed", "reason": f"no judge request: {type(failure).__name__}: {failure}"}
    return compiled, detail


def main() -> None:
    target = Path(sys.argv[1])
    try:
        reward, detail = combine(target)
    except Exception as error:  # any scoring failure must still leave a reward and its reason
        reward, detail = 0.0, {"reason": f"scoring failed: {type(error).__name__}: {error}"}
    target.write_text(json.dumps({"reward": reward}, indent=2))
    (target.parent / "reward-details.json").write_text(json.dumps({"reward": reward, **detail}, indent=2))


# A script run has no module spec; an import (as Reward Kit scans do) does, so it runs nothing.
if __spec__ is None:
    main()
