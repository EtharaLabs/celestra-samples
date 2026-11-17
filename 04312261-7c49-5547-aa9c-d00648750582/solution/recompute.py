# FORGE-CANARY-BEGIN
# FORGE-CANARY-SLOT-1: a24d69d496e08818fa619e41b58cd9f6d620e8625c0cb10ee96c2f972ed068cf
# FORGE-CANARY-SLOT-2: 587c1b9570e3a135387df57d9adcc2846bbc21e9ec7b10cbf026a5b01c9bcf3a
# FORGE-CANARY-SLOT-3: d261d0b447984f33d20d169edb4ac36db2c2f05e207203b4f1de78187cd83eca
# FORGE-CANARY-END
"""Regenerate every derived bundle artifact from solution/grounding.yaml.

Run from the bundle root. Writes solution/solve.sh, solution/TRUTH.md, solution/provenance.yaml
(keeping any binding block already present), tests/test_output.py, and
tests/graded/config.json, and, when the rubric holds judged items, tests/judge.toml and
tests/reference.diff, each a pure function of the grounding, so the oracle, the truth, the
compiled and judged criteria, and the provenance payload cannot disagree.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pprint
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
BANNER = "GENERATED SECTION. DO NOT HAND-EDIT."
SLOT = re.compile(r"FORGE-CANARY-SLOT-(\d+):[ \t]*([0-9a-f]{64})")


def tokens(text: str) -> list[str]:
    return [value for _, value in sorted((int(n), v) for n, v in SLOT.findall(text))]


def block(open_: str, close: str, values: list[str]) -> str:
    lines = [f"{open_}FORGE-CANARY-BEGIN{close}"]
    lines += [f"{open_}FORGE-CANARY-SLOT-{i}: {v}{close}" for i, v in enumerate(values, 1)]
    lines.append(f"{open_}FORGE-CANARY-END{close}")
    return "\n".join(lines) + "\n"


def solve(g: dict[str, Any], canary: list[str]) -> str:
    files = {path: base64.b64encode(text.encode()).decode() for path, text in g["reference"]["files"].items()}
    payload = json.dumps(files, sort_keys=True)
    return (
        "#!/bin/bash\n"
        + block("# ", "", canary)
        + "# " + BANNER + "\n"
        + "set -euo pipefail\n"
        + f"cd {g['repository']['workdir']}\n"
        + "python3 - <<'PYEOF'\n"
        + "import base64, json, pathlib\n"
        + f"files = json.loads({payload!r})\n"
        + "for path, data in sorted(files.items()):\n"
        + "    target = pathlib.Path(path)\n"
        + "    target.parent.mkdir(parents=True, exist_ok=True)\n"
        + "    target.write_bytes(base64.b64decode(data))\n"
        + "PYEOF\n"
    )


def truth(g: dict[str, Any], canary: list[str]) -> str:
    out = [block("<!-- ", " -->", canary), f"<!-- {BANNER} -->", "", f"# Ground truth: {g['task']['name']}", ""]
    out += [f"Repository {g['repository']['name']} at base commit {g['repository']['base_commit']}.", ""]
    out += ["## Golden path", ""]
    for step in g["steps"]:
        out.append(f"- {step['id']}: {step['action']} Establishes: {step['establishes']}")
        out += [f"  - checker: {c}" for c in step["checkers"]]
    out += ["", "## Rejected routes", ""]
    for route in g["rejected_routes"]:
        out.append(f"- {route['control']}: {route['route']}")
        out += [f"  - rejected by: {c}" for c in route["rejected_by"]]
    out += ["", "## Graded checkers", ""]
    out += [f"- fail-to-pass: {c}" for c in g["graded"]["f2p"]]
    out += [f"- pass-to-pass: {c}" for c in g["graded"]["p2p"]]
    out += [f"- deselected: {e['node']} ({e['reason']})" for e in g["graded"].get("exclude", [])]
    if g["graded"].get("option_guard"):
        guard = g["graded"]["option_guard"]
        out.append(f"- option guard: {guard['module']}.{guard['options']}[{guard['option']!r}] stays "
                   f"{guard['value']!r} for every read and write while a graded test runs ({guard['reason']}); "
                   "a run that moves it is refused and scores 0.")
        out.append(f"- option guard bindings: {', '.join(guard['bindings'])} keep their values for the "
                   f"whole run ({guard['bindings_reason']}); a run that changes one is refused and scores 0.")
    if g.get("rubric"):
        out += ["", "## Rubric", ""]
        for item in g["rubric"]["items"]:
            sign = "prohibition, " if item["negate"] else ""
            out.append(f"- {item['id']} ({item['obligation']}, {item['dimension']}, {sign}weight {item['weight']}, "
                       f"{item['judgment']['outcome_class']}, {item['mode']}"
                       f"{', guard, zeroes and is not averaged' if item['judgment'].get('guard') else ''}): "
                       f"{item['criterion']}")
            if item["mode"] == "judged":
                out.append(f"  - residue: {item['judgment']['residue']}")
        if _two_stage(g):
            judge = g["rubric"]["judge"]
            out += ["", f"Judged items are graded in two stages (ADR 0212) by {judge['judge']} over "
                        f"{', '.join(judge['files'])}, against {judge['reference']} (sha256 "
                        f"{judge['reference_diff_sha256']}). The verifier runs with no network, writes the compiled "
                        "score as the reward, and writes judge-request.json; stage 2 judges it through KeyProxy, and "
                        "stage 3 runs tests/combine.py, whose reward is the compiled score times (compiled weight + "
                        "judged weight x judged score) / total weight, so a judged item only lowers it."]
        elif _items(g, "judged"):
            judge = g["rubric"]["judge"]
            out += ["", f"Judged items are graded in one call by {judge['judge']} over {', '.join(judge['files'])}, "
                        f"against {judge['reference']} (sha256 {judge['reference_diff_sha256']}). The reward is the "
                        "compiled score times (compiled weight + judged weight x judged score) / total weight, so a "
                        "judged item only lowers it. No judge call runs when the compiled score is 0, and with no "
                        "judge credential, or when the judge run fails, the reward is the compiled score."]
    return "\n".join(out) + "\n"


RUBRIC_RUNTIME = """
GRADED = Path("/logs/verifier/graded.json")
PASS = "PASSED"


def _described(stdout, option):
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if line == option + ":":
            for follow in lines[index + 1:]:
                if not follow.startswith(" "):
                    break
                if follow.strip().startswith("Description:"):
                    return bool(follow.strip()[len("Description:"):].strip())
    return False


def _passed(data, spec):
    outcomes = data.get("outcomes", {})
    return [outcomes.get(node) == PASS for node in spec.get("nodes", [])]


RELATIONS = {
    "pass_share": lambda spec, data: sum(_passed(data, spec)) / len(spec["nodes"]),
    "all_pass": lambda spec, data: float(all(_passed(data, spec))),
    "none_pass": lambda spec, data: float(not any(_passed(data, spec))),
    "any_fail": lambda spec, data: float(not all(_passed(data, spec))),
    "steering_present": lambda spec, data: float(bool(data.get("steering"))),
    "option_described": lambda spec, data: float(
        _described(data.get("probes", {}).get(spec["probe"], {}).get("stdout", ""), spec["option"])),
    "probe_succeeds": lambda spec, data: float(
        not data.get("probes", {}).get(spec["probe"], {}).get("returncode", 1)),
}


def _relation(spec, data):
    return RELATIONS[spec["relation"]](spec, data)


@criterion
def rubric_item(workspace: Path, item: str) -> float:
    data = json.loads(GRADED.read_text())
    if data.get("refused") or _relation(GATE, data):
        return 0.0
    spec = ITEMS[item]
    value = _relation(spec, data)
    return 1.0 - value if spec["negate"] else value
"""
GATED = '    if data.get("refused") or _relation(GATE, data):\n'
GUARDED = '    if data.get("refused") or _relation(GATE, data) or any(_relation(guard, data) for guard in GUARDS):\n'


def _nodes(g: dict[str, Any], judgment: dict[str, Any]) -> list[str]:
    steps = {step["id"]: step["checkers"] for step in g["steps"]}
    nodes = list(judgment.get("nodes", []))
    for step in judgment.get("steps", []):
        nodes += [node for node in steps[step] if node not in nodes]
    return [node for node in nodes if node not in judgment.get("exclude", [])]


def _spec(g: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    judgment = item["judgment"]
    spec: dict[str, Any] = {"relation": judgment["relation"], "negate": item["negate"]}
    if "steps" in judgment or "nodes" in judgment:
        spec["nodes"] = _nodes(g, judgment)
    if "option" in judgment:
        spec["option"] = judgment["option"]
    if "probe" in judgment:
        spec["probe"] = judgment["probe"]["id"]
    return spec


def _scored(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # A guard only zeroes the reward; averaging its constant pass value would lift every submission that keeps it,
    # the empty one included, off the share the scored items define.
    return [item for item in items if not item["judgment"].get("guard")]


def _items(g: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    items = g.get("rubric", {}).get("items", [])
    if any(item["mode"] not in ("compiled", "judged") or item["weight"] not in (1, 3, 5) for item in items):
        raise ValueError("every rubric item is compiled or judged with a weight of 1, 3, or 5")
    return [item for item in items if item["mode"] == mode]


def rubric(g: dict[str, Any]) -> str:
    items = _items(g, "compiled")
    gates = [item for item in items if item["judgment"].get("gate")]
    if len(gates) != 1:
        raise ValueError("the rubric names exactly one gate item")
    scored = _scored(items)
    if not scored:
        raise ValueError("the rubric scores at least one compiled item")
    specs = {item["id"]: _spec(g, item) for item in scored}
    gate = {**_spec(g, gates[0]), "negate": False}
    guards = [{**_spec(g, item), "negate": False} for item in items
              if item["judgment"].get("guard") and item is not gates[0]]
    calls = "".join(f'rk.rubric_item({item["id"]!r}, weight={item["weight"]}.0, name={item["id"]!r})\n'
                    for item in scored)
    runtime = RUBRIC_RUNTIME.replace(GATED, GUARDED) if guards else RUBRIC_RUNTIME
    return (
        f'"""{BANNER} Compiled from the bundle grounding."""\n\n'
        "import json\nfrom pathlib import Path\n\nimport rewardkit as rk\nfrom rewardkit import criterion\n\n"
        f"GATE = {pprint.pformat(gate, width=110)}\n"
        + (f"GUARDS = {pprint.pformat(guards, width=110)}\n" if guards else "")
        + f"ITEMS = {pprint.pformat(specs, width=110)}\n"
        + runtime + "\n\n" + calls
    )


def criteria(g: dict[str, Any]) -> str:
    if g.get("rubric"):
        return rubric(g)
    return (
        f'"""{BANNER} Compiled from the bundle grounding."""\n\n'
        "import json\nfrom pathlib import Path\n\nfrom rewardkit import criterion\n\n"
        f"F2P = {json.dumps(g['graded']['f2p'], indent=4)}\n"
        f"P2P = {json.dumps(g['graded']['p2p'], indent=4)}\n"
        "PASS = \"PASSED\"\n\n\n"
        '@criterion(description="share of required behaviours fixed, zero unless every regression test still passes")\n'
        "def graded(workspace: Path) -> float:\n"
        '    data = json.loads(Path("/logs/verifier/graded.json").read_text())\n'
        '    if data.get("refused"):\n'
        "        return 0.0\n"
        '    outcomes = data.get("outcomes", {})\n'
        '    if any(outcomes.get(node) != PASS for node in P2P):\n'
        "        return 0.0\n"
        '    return sum(outcomes.get(node) == PASS for node in F2P) / len(F2P)\n'
    )


def _toml(value: Any) -> str:
    # JSON strings, lists of strings, integers, and booleans are valid TOML values as written.
    return json.dumps(value)


def judge_toml(g: dict[str, Any]) -> str:
    judge = g["rubric"]["judge"]
    out = [f"# {BANNER}", "", "[judge]"]
    out += [f"{key} = {_toml(judge[key])}" for key in ("judge", "files", "reference")]
    for item in _items(g, "judged"):
        out += ["", "[[criterion]]", f"id = {_toml(item['id'])}", f"description = {_toml(item['criterion'])}",
                'type = "binary"', f"weight = {_toml(item['weight'])}", f"negate = {_toml(item['negate'])}",
                "", "[criterion.annotations]", 'mode = "judged"',
                f"type = {_toml(item['judgment']['outcome_class'])}", f"obligation = {_toml(item['obligation'])}",
                f"dimension = {_toml(item['dimension'])}", f"evidence = {_toml(item['evidence'])}",
                f"residue = {_toml(item['judgment']['residue'])}"]
    return "\n".join(out) + "\n"


def reference_diff(g: dict[str, Any]) -> str:
    judge = g["rubric"]["judge"]
    text = judge["reference_diff"]
    if hashlib.sha256(text.encode()).hexdigest() != judge["reference_diff_sha256"]:
        raise SystemExit("the reference diff does not match the digest the grounding binds")
    return text


def _two_stage(g: dict[str, Any]) -> bool:
    return bool(_items(g, "judged")) and g["rubric"]["judge"].get("mode") == "two-stage"


def stages_json(g: dict[str, Any]) -> str:
    """ADR 0212 declaration in trinity.judge-stages/v2, written as canonical JSON with one final LF."""
    judge = g["rubric"]["judge"]
    body = {"schemaVersion": "trinity.judge-stages/v2", "provider": judge["provider"], "model": judge["model"],
            "temperature": judge["temperature"], "seed": judge["seed"], "trials": judge["trials"],
            "passLabel": judge["pass_label"], "judgments": judge["judgments"], "combine": "tests/combine.py"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def prompt_md(g: dict[str, Any]) -> str:
    return g["rubric"]["judge"]["prompt"].replace("{{reference}}", reference_diff(g))


COMBINE = '''#!/usr/bin/env python3
"""Stage 3 of two-stage judging: combine the compiled score with the judged score, offline.

Reads the stage 1 request and the stage 2 scores mounted under /judge and writes one reward.json, in
which a judged item only ever lowers the compiled score.
"""

import json
from pathlib import Path


def main() -> None:
    stage = json.loads((Path(__file__).parent / "graded" / "config.json").read_text())["judged"]
    request = json.loads(Path("/judge/judge-request.json").read_text())
    items = {item["id"]: item for item in json.loads(Path("/judge/judge-scores.json").read_text())["items"]}
    weights = stage["two_stage"]["weights"]
    compiled = sum(weight * request["compiled"][name] for name, weight in weights.items()) / sum(weights.values())
    judged = stage["two_stage"]["judged_weights"]
    score = sum(weight * items[name]["score"] for name, weight in judged.items()) / sum(judged.values())
    total = stage["compiled_weight"] + stage["judged_weight"]
    reward = round(compiled * (stage["compiled_weight"] + stage["judged_weight"] * score) / total, 4)
    Path("/logs/verifier/reward.json").write_text(json.dumps({"reward": reward}))


if __spec__ is None:
    main()
'''


CHEAT_CHECK_IDS = ("cheat-check/steering-files-absent",)


def cheat_checks() -> str:
    return json.dumps({"schema": "trinity.cheat-checks/v1", "ids": list(CHEAT_CHECK_IDS)}, indent=1, sort_keys=True) + "\n"


def config(g: dict[str, Any]) -> str:
    graded = g["graded"]
    body = {"artifact": g["repository"]["workdir"], "package_src": g["repository"]["package_src"],
            "graded_files": [{"path": f["path"], "sealed": f["sealed"]} for f in graded["files"]], "timeout_sec": graded["timeout_sec"]}
    if g["repository"].get("rebuild"):
        body["rebuild"] = g["repository"]["rebuild"]
    if graded.get("option_guard"):
        body["option_guard"] = graded["option_guard"]
    if graded.get("exclude"):
        body["deselect"] = [entry["node"] for entry in graded["exclude"]]
    probes = [item["judgment"]["probe"] for item in g.get("rubric", {}).get("items", []) if "probe" in item["judgment"]]
    if probes:
        body["probes"] = probes
    if _items(g, "judged"):
        judged: dict[str, Any] = {"compiled_weight": sum(item["weight"] for item in _scored(_items(g, "compiled"))),
                                  "judged_weight": sum(item["weight"] for item in _items(g, "judged"))}
        if _two_stage(g):
            judge = g["rubric"]["judge"]
            judged["two_stage"] = {
                **{key: judge[key] for key in ("provider", "model", "temperature", "seed", "trials")},
                "passLabel": judge["pass_label"],
                "weights": {item["id"]: item["weight"] for item in _scored(_items(g, "compiled"))},
                "judged_weights": {item["id"]: item["weight"] for item in _items(g, "judged")},
                "items": [{"id": item["id"], "criterion": item["criterion"], "controls": judge["controls"][item["id"]]}
                          for item in _items(g, "judged")],
            }
        body["judged"] = judged
    return json.dumps(body, indent=1, sort_keys=True) + "\n"


def provenance(g: dict[str, Any], canary: list[str], existing: str | None) -> str:
    payload = yaml.safe_dump(g["provenance"], sort_keys=True, default_flow_style=False, width=100)
    text = block("# ", "", canary) + f"# {BANNER}\n" + payload
    if existing:
        lines = existing.split("\n")
        start = next((i for i, line in enumerate(lines) if line == "binding:"), None)
        if start is not None:
            kept = [lines[start]]
            for line in lines[start + 1:]:
                if line and line[0] not in " \t":
                    break
                kept.append(line)
            text += "\n".join(kept).rstrip("\n") + "\n"
    return text


def sealed(g: dict[str, Any]) -> None:
    for entry in g["graded"]["files"]:
        actual = hashlib.sha256((ROOT / "tests" / "graded" / entry["sealed"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise SystemExit(f"sealed graded file {entry['sealed']} is {actual}, grounding binds {entry['sha256']}")


def main() -> None:
    source = (ROOT / "solution" / "grounding.yaml").read_text()
    g = yaml.safe_load(source)
    sealed(g)
    canary = tokens(source)
    held = ROOT / "solution" / "provenance.yaml"
    outputs = {
        "solution/solve.sh": solve(g, canary),
        "solution/TRUTH.md": truth(g, canary),
        "solution/provenance.yaml": provenance(g, canary, held.read_text() if held.is_file() else None),
        "tests/test_output.py": criteria(g),
        "tests/graded/config.json": config(g),
        "tests/cheat-checks.json": cheat_checks(),
    }
    if _items(g, "judged"):
        outputs["tests/judge.toml"] = judge_toml(g)
        outputs["tests/reference.diff"] = reference_diff(g)
    if _two_stage(g):
        outputs["tests/judge/stages.json"] = stages_json(g)
        outputs["tests/judge/prompt.md"] = prompt_md(g)
        outputs["tests/combine.py"] = COMBINE
    for relative, text in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (ROOT / "solution" / "solve.sh").chmod(0o755)
    if _two_stage(g):
        (ROOT / "tests" / "combine.py").chmod(0o755)


if __name__ == "__main__":
    main()
