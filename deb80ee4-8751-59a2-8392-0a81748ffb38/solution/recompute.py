# FORGE-CANARY-BEGIN
# FORGE-CANARY-SLOT-1: 20f50ea7ae814af80f4e126cb26782f67e0cb3345895d75e222ffd87ff2acf6b
# FORGE-CANARY-SLOT-2: db54df695bc9a2189402fa1522ada837b1958562ce875bd746ee68be20c2f1c7
# FORGE-CANARY-SLOT-3: 0df5037eaa4af14096707e67553428aa400bdc58ee19e5f5549af2902d44ff85
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
            out += ["", f"Judged items are graded in one call by {judge['judge']} over {', '.join(judge['files'])}, "
                        f"against {judge['reference']} (sha256 {judge['reference_diff_sha256']}). The reward is the "
                        "compiled score times (compiled weight + judged weight x judged score) / total weight, so a "
                        "judged item only lowers it. No judge call runs when the compiled score is 0, and with no "
                        "judge credential the judged items are not run and the reward is the compiled score."]
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
    if data.get("refused") or _relation(GATE, data):
        return 0.0
    spec = ITEMS[item]
    value = _relation(spec, data)
    return 1.0 - value if spec["negate"] else value
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
    gate = {**specs[gates[0]["id"]], "negate": False}
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


def config(g: dict[str, Any]) -> str:
    graded = g["graded"]
    body = {"artifact": g["repository"]["workdir"], "package_src": g["repository"]["package_src"],
            "graded_files": [{"path": f["path"], "sealed": f["sealed"]} for f in graded["files"]], "timeout_sec": graded["timeout_sec"]}
    if g["repository"].get("rebuild"):
        body["rebuild"] = g["repository"]["rebuild"]
    if graded.get("exclude"):
        body["deselect"] = [entry["node"] for entry in graded["exclude"]]
    probes = [item["judgment"]["probe"] for item in g.get("rubric", {}).get("items", []) if "probe" in item["judgment"]]
    if probes:
        body["probes"] = probes
    if _items(g, "judged"):
        body["judged"] = {"compiled_weight": sum(item["weight"] for item in _items(g, "compiled")),
                          "judged_weight": sum(item["weight"] for item in _items(g, "judged"))}
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
    }
    if _items(g, "judged"):
        outputs["tests/judge.toml"] = judge_toml(g)
        outputs["tests/reference.diff"] = reference_diff(g)
    for relative, text in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (ROOT / "solution" / "solve.sh").chmod(0o755)


if __name__ == "__main__":
    main()
