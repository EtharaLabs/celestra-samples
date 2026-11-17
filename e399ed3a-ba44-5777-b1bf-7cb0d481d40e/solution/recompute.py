# FORGE-CANARY-BEGIN
# FORGE-CANARY-SLOT-1: 73b5715e3a3344b92f9e8336f4466bd8ea9e8a52bd72a07f25b54164643168c5
# FORGE-CANARY-SLOT-2: f3d6e91b1bf5449e55e818ea65d8802713e91d1859883c9d1062ba55d21d07ff
# FORGE-CANARY-SLOT-3: db1ec1e4ec9a89b9f5415674d13a4384f5ca4c30fda6338fe39352e1cce639bb
# FORGE-CANARY-END
"""Regenerate every derived bundle artifact from solution/grounding.yaml.

Run from the bundle root. Writes solution/solve.sh, one solution/alternates/<name>/solve.sh per
alternate solution, solution/TRUTH.md, solution/provenance.yaml
(keeping any binding block already present), tests/test_output.py, and
tests/graded/config.json, and, when the rubric holds judged items, tests/judge.toml and the
two-stage packet tests/judge/{stages.json,prompt.md}, each a pure function of the grounding, so the oracle, the truth, the
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


def solve(g: dict[str, Any], canary: list[str], source: dict[str, str] | None = None) -> str:
    source = g["reference"]["files"] if source is None else source
    files = {path: base64.b64encode(text.encode()).decode() for path, text in source.items()}
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


def discovery(g: dict[str, Any]) -> list[str]:
    weights = {item["id"]: item["weight"] for item in g["rubric"]["items"]}
    found = g["discovery"]
    dependent = sorted({i for value in found["values"] for i in value["items"]})
    share = sum(weights[i] for i in dependent) / sum(weights.values())
    floor = found["floor"]
    if share < floor["value"]:
        raise SystemExit(f"discovery-dependent weight share {share:.4f} is below {floor['name']} {floor['value']}")
    out = [f"- {v['id']}: {v['value']}. Established at: {', '.join(v['established_at']) or v['source']}. "
           f"Graded items: {', '.join(v['items'])}." for v in found["values"]]
    out.append(f"- {floor['name']} {floor['value']} ({floor['source']}): items {', '.join(dependent)} carry "
               f"{sum(weights[i] for i in dependent)} of {sum(weights.values())} graded weight ({share:.4f}).")
    return out


def truth(g: dict[str, Any], canary: list[str]) -> str:
    out = [block("<!-- ", " -->", canary), f"<!-- {BANNER} -->", "", f"# Ground truth: {g['task']['name']}", ""]
    out += [f"Repository {g['repository']['name']} at base commit {g['repository']['base_commit']}.", ""]
    out += ["## Golden path", ""]
    for step in g["steps"]:
        out.append(f"- {step['id']}: {step['action']} Establishes: {step['establishes']}")
        out += [f"  - checker: {c}" for c in step["checkers"]]
    if g["reference"].get("alternates"):
        out += ["", "## Alternate solutions", ""]
        for name, alternate in g["reference"]["alternates"].items():
            out.append(f"- {name} (solution/alternates/{name}/solve.sh): {alternate['differs']}")
    out += ["", "## Rejected routes", ""]
    for route in g["rejected_routes"]:
        out.append(f"- {route['control']}: {route['route']}")
        out += [f"  - rejected by: {c}" for c in route["rejected_by"]]
    if g.get("discovery"):
        out += ["", "## Discovery", ""]
        out += discovery(g)
    out += ["", "## Graded checkers", ""]
    out += [f"- fail-to-pass: {c}" for c in g["graded"]["f2p"]]
    out += [f"- pass-to-pass: {c}" for c in g["graded"]["p2p"]]
    out += [f"- prohibition: {c}" for c in g["graded"].get("prohibitions", [])]
    if g["graded"].get("fixtures"):
        fixtures = g["graded"]["fixtures"]
        if fixtures.get("sealed"):
            out.append(f"- fixtures: sealed graded files {', '.join(fixtures['sealed'])}, written by "
                       f"`{fixtures['argv']}` from the base checkout ({fixtures['reason']})")
        else:
            out.append(f"- fixtures: `{fixtures['argv']}` at verifier image build ({fixtures['reason']})")
    out += [f"- deselected: {e['node']} ({e['reason']})" for e in g["graded"].get("exclude", [])]
    if g["graded"].get("runner_guard"):
        guard = g["graded"]["runner_guard"]
        out.append(f"- runner integrity: {', '.join(guard['runner'])}, every builtin and the import machinery "
                   f"keep their identity and code for the whole run, and the sealed helpers {', '.join(guard['helpers'])} "
                   f"come from {guard['helper_file']} ({guard['reason']}); a test the log reports passed must be one "
                   "the guard saw raise nothing, and a run that breaks either is refused and scores 0.")
    if g.get("rubric"):
        out += ["", "## Rubric", ""]
        for item in g["rubric"]["items"]:
            sign = "prohibition, " if item["negate"] else ""
            out.append(f"- {item['id']} ({item['obligation']}, {item['dimension']}, {sign}weight {item['weight']}, "
                       f"{item['judgment']['outcome_class']}, {item['mode']}): {item['criterion']}")
            if item["mode"] == "judged":
                out.append(f"  - residue: {item['judgment']['residue']}")
        if _items(g, "judged"):
            judge = g["rubric"]["judge"]
            out += ["", f"Judged items are graded in two stages (tests/judge/stages.json): the verifier writes "
                        f"/logs/verifier/judge-request.json, {judge['provider']} {judge['model']} judges it on the host "
                        f"over {judge['trials']} trials per item, and {judge['combine']} sets the reward to the compiled "
                        "score times (compiled weight + judged weight x judged score) / total weight, so a judged item "
                        "only lowers it. No request is written when the compiled score is 0, and a grader without "
                        "stage 2 keeps the compiled score."]
            controls = judge.get("controls")
            if controls:
                out += ["", "### Judged controls", ""]
                for item, rows in controls["items"].items():
                    out.append(f"- {item}: " + ", ".join(f"{row['case']} ({row['label']})" for row in rows))
                out += [f"- case {case}: {entry['note']}" for case, entry in controls["cases"].items()]
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
}


def _relation(spec, data):
    return RELATIONS[spec["relation"]](spec, data)


@criterion
def rubric_item(workspace: Path, item: str) -> float:
    data = json.loads(GRADED.read_text())
    share = 0.0 if data.get("refused") else _relation(GATE, data)
    if share < GATE["threshold"]:
        return 0.0
    spec = ITEMS[item]
    value = _relation(spec, data)
    value = 1.0 - value if spec["negate"] else value
    return value * share if spec.get("scaled") else value
"""


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
        spec["option"], spec["probe"] = judgment["option"], judgment["probe"]["id"]
    if judgment.get("scale"):
        spec["scaled"] = True
    return spec


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
    specs = {item["id"]: _spec(g, item) for item in items}
    # The gate opens once the share item reaches its threshold; every scaled item scales by that share.
    opening = gates[0]["judgment"]["gate"]
    if any(item["judgment"].get("scale", opening["share"]) != opening["share"] for item in items):
        raise ValueError("every scaled item scales by the gate's share item")
    gate = {**specs[opening["share"]], "negate": False, "threshold": float(opening["threshold"])}
    calls = "".join(f'rk.rubric_item({item["id"]!r}, weight={item["weight"]}.0, name={item["id"]!r})\n'
                    for item in items)
    return (
        f'"""{BANNER} Compiled from the bundle grounding."""\n\n'
        "import json\nfrom pathlib import Path\n\nimport rewardkit as rk\nfrom rewardkit import criterion\n\n"
        f"GATE = {pprint.pformat(gate, width=110)}\n"
        f"ITEMS = {pprint.pformat(specs, width=110)}\n"
        + RUBRIC_RUNTIME + "\n\n" + calls
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
    # Two-stage judging pins the judge in tests/judge/stages.json, so this file holds only criteria.
    out = [f"# {BANNER}"]
    for item in _items(g, "judged"):
        out += ["", "[[criterion]]", f"id = {_toml(item['id'])}", f"description = {_toml(item['criterion'])}",
                'type = "binary"', f"weight = {_toml(item['weight'])}", f"negate = {_toml(item['negate'])}",
                "", "[criterion.annotations]", 'mode = "judged"',
                f"type = {_toml(item['judgment']['outcome_class'])}", f"obligation = {_toml(item['obligation'])}",
                f"dimension = {_toml(item['dimension'])}", f"evidence = {_toml(item['evidence'])}",
                f"residue = {_toml(item['judgment']['residue'])}"]
    return "\n".join(out) + "\n"


def judgment_id(g: dict[str, Any], item: dict[str, Any]) -> str:
    return f"{g['task']['name']}/{item['id']}"


def stages(g: dict[str, Any]) -> str:
    judge = g["rubric"]["judge"]
    body = {"schemaVersion": "trinity.judge-stages/v2", "provider": judge["provider"], "model": judge["model"],
            "temperature": judge["temperature"], "seed": judge["seed"], "trials": judge["trials"],
            "passLabel": judge["pass_label"], "combine": judge["combine"],
            "judgments": {item["id"]: judgment_id(g, item) for item in _items(g, "judged")}}
    # trinity reads this file only as canonical JSON: sorted keys, no spaces, one final newline.
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def config(g: dict[str, Any]) -> str:
    graded = g["graded"]
    body = {"artifact": g["repository"]["workdir"], "package_src": g["repository"]["package_src"],
            "graded_files": [{"path": f["path"], **({"sealed": f["sealed"]} if f.get("sealed") else {"pristine": True})}
                             for f in graded["files"]],
            "collect": graded["collect"], "timeout_sec": graded["timeout_sec"]}
    if g["repository"].get("rebuild"):
        body["rebuild"] = g["repository"]["rebuild"]
    if graded.get("runner_guard"):
        body["runner_guard"] = {key: graded["runner_guard"][key] for key in ("runner", "helpers", "helper_file")}
    body["cheat_checks"] = cheat_checks(g)
    if graded.get("exclude"):
        body["deselect"] = [entry["node"] for entry in graded["exclude"]]
    probes = [item["judgment"]["probe"] for item in g.get("rubric", {}).get("items", []) if "probe" in item["judgment"]]
    if probes:
        body["probes"] = probes
    if _items(g, "judged"):
        judge = g["rubric"]["judge"]
        body["judged"] = {
            "compiled": {item["id"]: item["weight"] for item in _items(g, "compiled")},
            "items": [{"id": item["id"], "criterion": item["criterion"], "weight": item["weight"],
                       "negate": item["negate"]} for item in _items(g, "judged")],
            "controls": judge.get("controls", {}).get("items", {}),
            "pinned": {key: judge[key] for key in ("provider", "model", "temperature", "seed", "trials")}
            | {"passLabel": judge["pass_label"]}}
    return json.dumps(body, indent=1, sort_keys=True) + "\n"


class _Notices(yaml.SafeDumper):
    pass


_Notices.add_representer(str, lambda dumper, value: dumper.represent_scalar(
    "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None))


def provenance(g: dict[str, Any], canary: list[str], existing: str | None) -> str:
    # licence notices must read verbatim, so multi-line strings stay literal blocks
    payload = yaml.dump(g["provenance"], Dumper=_Notices, sort_keys=True, default_flow_style=False,
                        width=100, allow_unicode=True)
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
        if not entry.get("sealed"):
            continue
        actual = hashlib.sha256((ROOT / "tests" / "graded" / entry["sealed"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise SystemExit(f"sealed graded file {entry['sealed']} is {actual}, grounding binds {entry['sha256']}")
    controls = g.get("rubric", {}).get("judge", {}).get("controls", {})
    for case, entry in controls.get("cases", {}).items():
        actual = hashlib.sha256((ROOT / "tests" / "judge-controls" / f"{case}.diff").read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise SystemExit(f"judged control {case} is {actual}, grounding binds {entry['sha256']}")


CHEAT_CHECKS = {"steering": "cheat-check: the submission planted no test-steering file",
                "runner": "cheat-check: the test runner, its assertion helpers and its reports stayed unaltered"}


def cheat_checks(g: dict[str, Any]) -> dict[str, str]:
    """CTRF test name per cheat check: tampering with the run, never an unmet requirement."""
    kinds = ["steering", *(["runner"] if g["graded"].get("runner_guard") else [])]
    return {CHEAT_CHECKS[kind]: kind for kind in kinds}


def cheat_declaration(g: dict[str, Any]) -> str:
    return json.dumps({"schema": "trinity.cheat-checks/v1", "ids": sorted(cheat_checks(g))}, indent=1) + "\n"


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
        "tests/cheat-checks.json": cheat_declaration(g),
    }
    for name, alternate in g["reference"].get("alternates", {}).items():
        outputs[f"solution/alternates/{name}/solve.sh"] = solve(g, canary, alternate["files"])
    if _items(g, "judged"):
        outputs["tests/judge.toml"] = judge_toml(g)
        outputs["tests/judge/stages.json"] = stages(g)
        outputs["tests/judge/prompt.md"] = g["rubric"]["judge"]["prompt"]
    for relative, text in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    for relative in outputs:
        (ROOT / relative).chmod(0o755 if relative.endswith(".sh") else 0o644)


if __spec__ is None:
    main()
