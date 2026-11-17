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
package from base to submission goes to /logs/verifier/submission.diff for the judge. It runs
with / as its working directory, so ``tests/graded/`` is the bundle's own sealed tree.
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
STEERING: list[str] = []
GUARD_VERDICT = Path("/logs/verifier/option_guard.json")
RESULT: dict[str, object] = {"refused": None, "outcomes": {}, "steering": STEERING, "probes": {},
                             "pytest_exit": None, "option_guard": None}
# Cheat checks are anti-cheat conditions no honest partial patch can trip, so a gold-subset trial
# must pass every one; tests/cheat-checks.json declares these names for CRUCIBLE to join.
CHEAT_CHECKS = {"cheat-check/steering-files-absent": lambda: not STEERING}
CTRF_STATUS = {"PASSED": "passed", "FAILED": "failed", "ERROR": "failed", "XPASS": "failed",
               "SKIPPED": "skipped", "XFAIL": "skipped"}


def ctrf(result: dict[str, object]) -> dict[str, object]:
    """A CTRF report of every graded node and every cheat check, each name once."""
    outcomes = result["outcomes"] if isinstance(result["outcomes"], dict) else {}
    tests = [{"name": node, "status": CTRF_STATUS[kind], "duration": 0} for node, kind in sorted(outcomes.items())]
    tests += [{"name": name, "status": "passed" if held() else "failed", "duration": 0}
              for name, held in CHEAT_CHECKS.items()]
    counted = Counter(t["status"] for t in tests)
    summary = {status: counted[status] for status in ("passed", "failed", "skipped")}
    return {"results": {"tool": {"name": "run_graded"},
                        "summary": {"tests": len(tests), **summary, "pending": 0, "other": 0, "start": 0, "stop": 0},
                        "tests": tests}}


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
    """The unified diff of the graded package from base to submission, the judge's only evidence.

    tests/reference.diff is this same text for the reference solution, so the two compare line for line.
    """
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
        os.write(write, json.dumps({**guard, "nonce": nonce, "verdict": str(GUARD_VERDICT)}).encode())
        os.close(write)
        env.update(OPTION_GUARD_FD=str(read), PYTHONPATH="/tests")
        plugin, keep = ["-p", "option_guard"], (read,)
    # -rfEsxXp reports every outcome but never the captured output of passing tests, so text the
    # submission prints cannot reach the log as a report section.
    argv = ["python", "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q", "-rfEsxXp",
            "--tb=no", "-W", "ignore", *plugin, *[a for node in CONFIG.get("deselect", []) for a in ("--deselect", node)],
            *[g["path"] for g in CONFIG["graded_files"]]]
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
    return outcomes, done.returncode, guarded(guard, nonce) if guard else None


def guarded(guard: dict[str, str], nonce: str) -> str | None:
    name = f"{guard['module']}.{guard['options']}[{guard['option']!r}]"
    if not GUARD_VERDICT.is_file():
        return f"the option guard on {name} left no verdict"
    verdict = json.loads(GUARD_VERDICT.read_text())
    GUARD_VERDICT.unlink()
    RESULT["option_guard"] = verdict
    if verdict.get("nonce") != nonce:
        return f"the option guard verdict on {name} does not carry this run's nonce"
    if verdict.get("events"):
        found = "; ".join(verdict["events"][:3])
        return f"the submission moved {name} off {guard['value']!r} during the graded run: {found}"
    if not verdict.get("holds"):
        found = "; ".join(verdict.get("tampered", [])[:3])
        return f"the submission replaced a binding that decides {name} during the graded run: {found}"
    return None


def probe() -> dict[str, dict[str, object]]:
    probes: dict[str, dict[str, object]] = {}
    for entry in CONFIG.get("probes", []):
        done = subprocess.run(entry["argv"], cwd=REPO, env=environment(), capture_output=True, text=True,
                              timeout=CONFIG["timeout_sec"], check=False)
        probes[entry["id"]] = {"returncode": done.returncode, "stdout": done.stdout}
    return probes


GRADING = Path(CONFIG["grading_root"])
BEFORE: dict[str, str | None] = {}


def _ignore(source: Path, label: str):  # noqa: ANN202
    def ignore(directory: str, names: list[str]) -> set[str]:
        steering = sorted(n for n in names if n in REFUSED or n.endswith(".pth"))
        STEERING.extend(f"{label}/{Path(directory, n).relative_to(source)}" for n in steering)
        return {*steering, *(n for n in names if n == "__pycache__")}
    return ignore


def overlay() -> str | None:
    for checkout in CONFIG["checkouts"]:
        for package in checkout["package_src"]:
            source = Path(checkout["artifact"]) / package
            if source.is_symlink() or not (source.is_dir() or source.is_file()):
                return f"the submission carries no {checkout['name']}/{package}"
    BEFORE.update(package_texts())
    for graded in CONFIG["graded_files"]:
        shutil.copyfile(GRADED / graded["sealed"], Path(graded["root"]) / graded["path"])
    return None


def _overlay_checkout(checkout: dict[str, object]) -> None:
    artifact, repo = Path(checkout["artifact"]), Path(checkout["repo"])
    for package in checkout["package_src"]:
        source, target = artifact / package, repo / package
        if source.is_file():
            shutil.copyfile(source, target)
            continue
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, symlinks=False, ignore=_ignore(source, f"{checkout['name']}/{package}"))


def package_texts() -> dict[str, str | None]:
    texts: dict[str, str | None] = {}
    for checkout in CONFIG["checkouts"]:
        repo = Path(checkout["repo"])
        for package in checkout["package_src"]:
            target = repo / package
            for path in sorted([target] if target.is_file() else target.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    key = f"{checkout['name']}/{path.relative_to(repo)}"
                    try:
                        texts[key] = path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        texts[key] = None
    return texts


def _run_root(root: str, files: list[dict[str, object]]) -> tuple[dict[str, str], int]:
    paths = [str(graded["path"]) for graded in files]
    env = {**environment(), **{k: str(v) for graded in files for k, v in graded.get("env", {}).items()}}
    prefix = Path(root).relative_to(GRADING).as_posix() + "/"
    pattern = re.compile(r"(?<!\S)(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) ((?:%s)::.+?)(?: - .*)?$"
                         % "|".join(re.escape(path) for path in paths))
    deselect = [node[len(prefix):] for node in CONFIG.get("deselect", []) if node.startswith(prefix)]
    argv = ["python", "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q", "-rfEsxXp",
            "--tb=no", "-W", "ignore", *[a for node in deselect for a in ("--deselect", node)], *paths]
    done = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True,
                          timeout=CONFIG["timeout_sec"], check=False)
    seen: dict[str, set[str]] = {}
    for line in done.stdout.splitlines():
        found = pattern.search(ORDINAL.sub("", line))
        if found:
            seen.setdefault(prefix + found.group(2), set()).add(found.group(1))
    return {node: min(kinds, key=RANK.index) for node, kinds in seen.items()}, done.returncode


def run() -> tuple[dict[str, str], int, str | None]:
    outcomes: dict[str, str] = {}
    status = 0
    for checkout in CONFIG["checkouts"]:
        _overlay_checkout(checkout)
        roots: dict[str, list[dict[str, object]]] = {}
        for graded in CONFIG["graded_files"]:
            if graded["repository"] == checkout["name"]:
                roots.setdefault(graded["root"], []).append(graded)
        for root, files in roots.items():
            found, returncode = _run_root(root, files)
            outcomes.update(found)
            status = status or returncode
    if CONFIG.get("judged"):
        Path("/logs/verifier/submission.diff").write_text(package_diff(BEFORE, package_texts()))
    return outcomes, status, None


def probe() -> dict[str, dict[str, object]]:
    probes: dict[str, dict[str, object]] = {}
    for entry in CONFIG.get("probes", []):
        done = subprocess.run(entry["argv"], cwd=GRADING, env=environment(), capture_output=True, text=True,
                              timeout=CONFIG["timeout_sec"], check=False)
        probes[entry["id"]] = {"returncode": done.returncode, "stdout": done.stdout}
    return probes


VGUARD_DIR = Path("/logs/verifier/vguard")
VGUARD_NONCE = secrets.token_hex(16)
DENIED = re.compile(r"(?<![\w.])(_pytest|pytest|pluggy)\b")
_environment_unguarded, _overlay_unguarded, _run_unguarded = environment, overlay, run


def environment() -> dict[str, str]:
    env = _environment_unguarded()
    env["PYTHONPATH"] = ":".join(p for p in ("/tests", env.get("PYTHONPATH", "")) if p)
    env.update(PYTEST_ADDOPTS="-p vguard", VGUARD_DIR=str(VGUARD_DIR), VGUARD_NONCE=VGUARD_NONCE)
    return env


def _submitted() -> dict[str, str | None]:
    if "checkouts" in CONFIG:
        pairs = [(Path(c["artifact"]) / p, f"{c['name']}/{p}") for c in CONFIG["checkouts"] for p in c["package_src"]]
    else:
        pairs = [(ARTIFACT / CONFIG["package_src"], CONFIG["package_src"])]
    texts: dict[str, str | None] = {}
    for source, label in pairs:
        for path in sorted([source] if source.is_file() else source.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                key = label if path == source else f"{label}/{path.relative_to(source)}"
                try:
                    texts[key] = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    texts[key] = None
    return texts


def _denied(before: dict[str, str | None], after: dict[str, str | None]) -> list[str]:
    hits: list[str] = []
    for key, new in sorted(after.items()):
        if new is None:
            continue
        old = (before.get(key) or "").splitlines()
        for line in difflib.unified_diff(old, new.splitlines(), lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++") and DENIED.search(line):
                hits.append(f"{key}: {line[1:].strip()[:80]}")
    return hits


def overlay() -> str | None:
    hits = _denied(package_texts(), _submitted())
    if hits:
        return "the submission's package source names pytest internals: " + "; ".join(hits[:3])
    return _overlay_unguarded()


def _report_guard() -> str | None:
    verdicts = sorted(VGUARD_DIR.glob("*.json")) if VGUARD_DIR.is_dir() else []
    if not verdicts:
        return "the report guard left no verdict"
    findings: list[str] = []
    for path in verdicts:
        verdict = json.loads(path.read_text())
        if verdict.get("nonce") != VGUARD_NONCE:
            return f"report guard verdict {path.name} does not carry this run's nonce"
        findings += verdict.get("findings", [])
    RESULT["report_guard"] = findings
    return "the graded run tampered with outcome reporting: " + "; ".join(findings[:3]) if findings else None


def run() -> tuple[dict[str, str], int, str | None]:
    shutil.rmtree(VGUARD_DIR, ignore_errors=True)
    outcomes, status, refused = _run_unguarded()
    return outcomes, status, refused or _report_guard()


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
    Path("/logs/verifier/ctrf.json").write_text(json.dumps(ctrf(result), indent=1, sort_keys=True))


# A script run has no module spec; an import (as Reward Kit scans do) does, so it runs nothing.
if __spec__ is None:
    main()
