"""Overlay the agent's package source on a pristine checkout and run the sealed graded tests.

Only files under the package source directory are taken from the agent's tree, so test
infrastructure, configuration, and the graded tests themselves stay sealed. Files that would
let the submission steer the test run, conftest.py, sitecustomize.py, usercustomize.py, and any
.pth file, are refused. When the config names a rebuild command, compiled extensions are dropped
from the overlay and rebuilt from the submitted source before the tests run. The outcome of
every graded node id, the steering files dropped from the overlay, and the output of every probe
the config names are written to /logs/verifier/graded.json for the criteria in
/tests/test_output.py to score. When the config names an option guard, the tests run under the
/tests/option_guard.py plugin, and a run in which the submission moved the guarded library option
off its graded value, even for the span of one model build, or replaced a binding that decides it, is refused. When the rubric holds judged items, the unified diff of the graded
package from base to submission goes to /logs/verifier/submission.diff for the judge. Every graded
node and every cheat check the config names is also written as a CTRF report to
/logs/verifier/ctrf.json; a cheat check fails only when the submission tampered with the run,
never because a requirement is unmet. It runs with / as its working directory, so
``tests/graded/`` is the bundle's own sealed tree.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import secrets
import shutil
import subprocess
from collections import Counter
from pathlib import Path

GRADED = Path("tests/graded")
CONFIG = json.loads((GRADED / "config.json").read_text())
# Harbor re-materializes each declared artifact at its original source path in the verifier.
ARTIFACT = Path(CONFIG["artifact"])
REPO = Path("/grading/repo")
REFUSED = {"conftest.py", "sitecustomize.py", "usercustomize.py"}
# An outcome line is found anywhere on its line, so leading indentation, timestamps, and worker
# prefixes such as "[gw0]" do not hide it; the node id must name a sealed graded file. Parametrize
# ids may hold spaces; failures and errors carry " - <message>", and a trailing " #NN" ordinal is
# dropped before matching.
OUTCOME = re.compile(r"(?<!\S)(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) ((?:%s)::.+?)(?: - .*)?$"
                     % "|".join(re.escape(g["path"]) for g in CONFIG["graded_files"]))
ORDINAL = re.compile(r"\s+#\d+\s*$")
RANK = ["ERROR", "FAILED", "XPASS", "SKIPPED", "XFAIL", "PASSED"]
PASSING = {RANK[2], RANK[-1]}
STEERING: list[str] = []
GUARD_VERDICT = Path("/logs/verifier/option_guard.json")
CTRF = Path("/logs/verifier/ctrf.json")
CTRF_STATUS = {"PASSED": "passed", "XPASS": "passed", "FAILED": "failed", "ERROR": "failed",
               "SKIPPED": "skipped", "XFAIL": "skipped"}
CTRF_KEYS = ("passed", "failed", "skipped", "pending", "other")
RESULT: dict[str, object] = {"refused": None, "outcomes": {}, "steering": STEERING, "probes": {},
                             "pytest_exit": None, "option_guard": None}


def overlay() -> str | None:
    source = ARTIFACT / CONFIG["package_src"]
    if not source.is_dir() or source.is_symlink():
        return f"the submission carries no {CONFIG['package_src']} directory"
    target = REPO / CONFIG["package_src"]
    before = package_texts()
    shutil.rmtree(target)

    def ignore(directory: str, names: list[str]) -> set[str]:
        steering = sorted(n for n in names if n in REFUSED or n.endswith(".pth"))
        STEERING.extend(str(Path(directory, n).relative_to(source)) for n in steering)
        dropped = {*steering, *(n for n in names if n == "__pycache__")}
        if CONFIG.get("rebuild"):
            # Compiled extensions are rebuilt from the submitted source, never taken as shipped.
            dropped |= {n for n in names if n.endswith(".so") or (
                n.endswith((".c", ".cpp")) and n.rsplit(".", 1)[0] + ".pyx" in names)}
        return dropped

    shutil.copytree(source, target, symlinks=False, ignore=ignore)
    if CONFIG.get("judged"):
        Path("/logs/verifier/submission.diff").write_text(package_diff(before, package_texts()))
    for graded in CONFIG["graded_files"]:
        shutil.copyfile(GRADED / graded["sealed"], REPO / graded["path"])
    return None


def package_texts() -> dict[str, str | None]:
    texts: dict[str, str | None] = {}
    for path in sorted((REPO / CONFIG["package_src"]).rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            try:
                texts[str(path.relative_to(REPO))] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                texts[str(path.relative_to(REPO))] = None
    return texts


def package_diff(before: dict[str, str | None], after: dict[str, str | None]) -> str:
    """The unified diff of the graded package from base to submission, the judge's only evidence."""
    out: list[str] = []
    for path in sorted(set(before) | set(after)):
        old, new = before.get(path), after.get(path)
        if path in before and path in after and old == new:
            continue
        if (path in before and old is None) or (path in after and new is None):
            out.append(f"Binary file {path} differs\n")
            continue
        out.extend(line + "\n" for line in difflib.unified_diff(
            (old or "").splitlines(), (new or "").splitlines(),
            "a/" + path if path in before else "/dev/null", "b/" + path if path in after else "/dev/null",
            lineterm=""))
    return "".join(out)


def environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "PYTEST"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def rebuild() -> str | None:
    if not CONFIG.get("rebuild"):
        return None
    with open("/logs/verifier/build.log", "w") as log:
        done = subprocess.run(CONFIG["rebuild"], cwd=REPO, env=environment(), stdout=log,
                              stderr=subprocess.STDOUT, timeout=CONFIG["timeout_sec"], check=False)
    return None if done.returncode == 0 else f"the submitted source does not build (exit {done.returncode})"


def run() -> tuple[dict[str, str], int, str | None]:
    env = environment()
    guard, plugin, keep, nonce = CONFIG.get("option_guard"), [], (), ""
    if guard:
        # The spec and nonce travel through a pipe the plugin reads and closes before any
        # submitted code is imported, so neither the environment nor the argv carries the nonce.
        nonce = secrets.token_hex(16)
        read, write = os.pipe()
        tests = [str(REPO / g["path"]) for g in CONFIG["graded_files"] if g.get("collect", True)]
        os.write(write, json.dumps({**guard, "nonce": nonce, "verdict": str(GUARD_VERDICT), "tests": tests,
                                     "package": str(REPO / CONFIG["package_src"])}).encode())
        os.close(write)
        env.update(OPTION_GUARD_FD=str(read), PYTHONPATH="/tests")
        plugin, keep = ["-p", "option_guard"], (read,)
    # -rfEsxXp reports every outcome but never the captured output of passing tests, so text the
    # submission prints cannot reach the log as a report section.
    argv = ["python", "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q", "-rfEsxXp",
            "--tb=no", "-W", "ignore", *plugin, *[a for node in CONFIG.get("deselect", []) for a in ("--deselect", node)],
            *[g["path"] for g in CONFIG["graded_files"] if g.get("collect", True)]]
    try:
        done = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True,
                              timeout=CONFIG["timeout_sec"], check=False, pass_fds=keep)
    finally:
        for descriptor in keep:
            os.close(descriptor)
    seen: dict[str, set[str]] = {}
    for line in done.stdout.splitlines():
        found = OUTCOME.search(ORDINAL.sub("", line))
        if found:
            seen.setdefault(found.group(2), set()).add(found.group(1))
    # A node seen with more than one outcome keeps the worst, so a forged PASSED line beside the
    # real report never upgrades it.
    outcomes = {node: min(kinds, key=RANK.index) for node, kinds in seen.items()}
    return outcomes, done.returncode, guarded(guard, nonce, outcomes) if guard else None


def guarded(guard: dict[str, str], nonce: str, outcomes: dict[str, str]) -> str | None:
    name = f"{guard['module']}.{guard['options']}[{guard['option']!r}]"
    if not GUARD_VERDICT.is_file():
        return f"the option guard on {name} left no verdict"
    verdict = json.loads(GUARD_VERDICT.read_text())
    GUARD_VERDICT.unlink()
    raised = verdict.pop("raised", None)
    RESULT["option_guard"] = verdict
    if verdict.get("nonce") != nonce:
        return f"the option guard verdict on {name} does not carry this run's nonce"
    if verdict.get("events"):
        found = "; ".join(verdict["events"][:3])
        return f"the submission moved {name} off {guard['value']!r} during the graded run: {found}"
    if verdict.get("runner_tampered"):
        found = "; ".join(verdict["runner_tampered"][:3])
        return f"the submission altered the test runner or an assertion helper during the graded run: {found}"
    if not verdict.get("holds"):
        found = "; ".join(verdict.get("tampered", [])[:3])
        return f"the submission replaced a binding that decides {name} during the graded run: {found}"
    # The log is what pytest printed; the guard's record is what each test raised. A node the log
    # calls passed must be one the guard saw run and raise nothing.
    if not isinstance(raised, dict):
        return "the option guard verdict carries no record of what the graded tests raised"
    forged = sorted(node for node, kind in outcomes.items() if kind in PASSING and raised.get(node) is not False)
    if forged:
        verdict["holds"] = False
        verdict["forged"] = forged[:20]
        verdict["forged_count"] = len(forged)
        return f"the log reports {len(forged)} graded test(s) passed that raised or never ran: {', '.join(forged[:3])}"
    return None


def probe() -> dict[str, dict[str, object]]:
    probes: dict[str, dict[str, object]] = {}
    for entry in CONFIG.get("probes", []):
        done = subprocess.run(entry["argv"], cwd=REPO, env=environment(), capture_output=True, text=True,
                              timeout=CONFIG["timeout_sec"], check=False)
        probes[entry["id"]] = {"returncode": done.returncode, "stdout": done.stdout}
    return probes


def cheat_checks(result: dict[str, object]) -> dict[str, str]:
    """Each declared cheat check's CTRF status; "other" when the run never reached it."""
    verdict = result["option_guard"]
    held = isinstance(verdict, dict) and not verdict.get("events") and not verdict.get("tampered")
    honest = isinstance(verdict, dict) and not verdict.get("runner_tampered") and not verdict.get("forged")
    status = {
        "option_guard": ("passed" if held else "failed") if verdict is not None else "other",
        "runner": ("passed" if honest else "failed") if verdict is not None else "other",
        "steering": "failed" if STEERING else "passed",
    }
    return {name: status[kind] for name, kind in CONFIG.get("cheat_checks", {}).items()}


def ctrf(result: dict[str, object]) -> None:
    outcomes = result["outcomes"] if isinstance(result["outcomes"], dict) else {}
    tests = [{"name": node, "status": CTRF_STATUS.get(kind, "other"), "duration": 0}
             for node, kind in sorted(outcomes.items())]
    tests += [{"name": name, "status": status, "duration": 0}
              for name, status in cheat_checks(result).items()]
    counts = Counter(t["status"] for t in tests)
    summary = {"tests": len(tests), **{key: counts[key] for key in CTRF_KEYS}, "start": 0, "stop": 0}
    CTRF.write_text(json.dumps({"results": {"tool": {"name": "pytest"}, "summary": summary,
                                            "tests": tests}}, indent=1))


def main() -> None:
    # Every path that ends in a zero score leaves its reason in "refused"; a submission that is
    # graded but fails the gate is explained by the per-item scores Reward Kit writes.
    result = RESULT
    try:
        result["refused"] = overlay()
        if result["refused"] is None:
            result["refused"] = rebuild()
        if result["refused"] is None:
            result["outcomes"], result["pytest_exit"], result["refused"] = run()
            if result["refused"] is None and not result["outcomes"]:
                result["refused"] = f"pytest reported no graded outcome (exit {result['pytest_exit']})"
        if result["refused"] is None:
            result["probes"] = probe()
    except subprocess.TimeoutExpired:
        result["refused"] = "the build or the graded tests exceeded their time limit"
    except Exception as error:  # any other verifier failure must still leave its reason
        result["refused"] = f"the verifier failed before scoring: {type(error).__name__}: {error}"
    Path("/logs/verifier/graded.json").write_text(json.dumps(result, indent=1, sort_keys=True))
    ctrf(result)


# A script run has no module spec; an import (as Reward Kit scans do) does, so it runs nothing.
if __spec__ is None:
    main()
