"""Requirement checks for multi-period optimisation under linopy's v1 semantics.

Each test decides one stated requirement on behaviour, never on how a solution is written:
every network, single-period or multi-period, builds and solves under v1 with the base's legacy
results, the option selects and consistently applies a snapshot
representation, the expressions agree with the statistics at the solution, and what the
statement keeps unchanged stays unchanged. The base-commit models and API inventory they compare
against are sealed fixtures written from the base checkout before any submission existed; checks under the
legacy semantics run in a child process so the graded process keeps the v1 semantics.
"""

import json
import os
import subprocess
import sys
from functools import cache
from pathlib import Path

import pytest

import forge_support as fs

REPO = Path(fs.__file__).resolve().parent.parent
API = json.loads((fs.FIXTURES / "forge_api.json").read_text())
LEGACY = json.loads((fs.FIXTURES / "forge_legacy.json").read_text())
NETWORKS = [*fs.MULTI_PERIOD, *fs.SINGLE_PERIOD]
# The unmodified base already reaches the legacy result under v1 on these networks, so an M2 check
# there could not tell a fix from no change; U1 still holds each of them to the base model.
BASE_ALREADY_V1 = {"meshed_single_period", "losses_single_period", "meshed_security_constrained"}
M2_NETWORKS = [name for name in NETWORKS if name not in BASE_ALREADY_V1]

# Pairs, groupings, time aggregations, and filters the base statistics accept, the reference
# expressions reproduce at the solution, and the base expressions do not; forge_ag_dropped.json
# names every other case and why it is left out.
AG_CASES = json.loads((Path(__file__).with_name("forge_ag_cases.json")).read_text())

V1_VALUES = {"v1-default": None, "v1-auto": "auto", "v1-flat": "flat"}
LEGACY_VALUES = {"legacy-default": "None", "legacy-auto": "auto", "legacy-flat": "flat",
                 "legacy-multiindex": "multiindex"}
FLAT = {"v1-default", "v1-auto", "v1-flat", "legacy-flat"}


@cache
def solved(name):
    n = fs.network(name)
    fs.optimize(n, name)
    return n


@cache
def v1_facts(value):
    return fs.representation_facts(value)


@cache
def legacy_facts():
    out = Path(os.environ.get("TMPDIR", "/tmp")) / f"forge-legacy-facts-{os.getpid()}.json"
    env = {k: v for k, v in os.environ.items() if k != "OPTION_GUARD_FD"}
    env["LINOPY_SEMANTICS"] = "legacy"
    subprocess.run([sys.executable, fs.__file__, "facts", "legacy", str(out)], cwd=REPO, env=env,
                   capture_output=True, timeout=2400, check=True)
    return json.loads(out.read_text())


def facts_for(case):
    if case in V1_VALUES:
        return v1_facts(V1_VALUES[case])
    facts = legacy_facts()["representation"][LEGACY_VALUES[case]]
    assert "error" not in facts, facts["error"]
    return facts


@cache
def ag_network(kind):
    return fs.ag_network(kind)


@cache
def submitted_api():
    return fs.api_inventory()


@pytest.mark.parametrize("name", M2_NETWORKS)
def test_m2_objective_equals_legacy_optimum(name):
    n = solved(name)
    assert fs._close(float(n.objective), LEGACY[name]["objective"]), (
        f"objective {n.objective} differs from the legacy optimum {LEGACY[name]['objective']}")


@pytest.mark.parametrize("name", M2_NETWORKS)
def test_m2_solution_optimal_in_legacy_model(name):
    problems = fs.legacy_optimum_problems(LEGACY[name], solved(name))
    assert not problems, problems


@pytest.mark.parametrize("case", [*V1_VALUES, *LEGACY_VALUES])
def test_o1_option_selects_representation(case):
    facts = facts_for(case)
    if case.endswith("default"):
        assert facts["default"] == "auto", f"the default value is {facts['default']!r}"
    want_flat = case in FLAT
    assert facts["parameters"]["multiindex"] is not want_flat
    labels, built = facts["parameters"]["labels"], facts["build_snapshots"]
    assert labels == built


@pytest.mark.parametrize("case", [*V1_VALUES, *LEGACY_VALUES])
def test_cr_model_uses_one_representation(case):
    facts = facts_for(case)
    problems = fs.representation_problems(facts, case in FLAT)
    assert not problems, problems


@pytest.mark.parametrize("case", ["v1-default", "v1-flat", "legacy-flat"])
def test_o2_flat_layout_period_then_timestep(case):
    problems = fs.layout_problems(facts_for(case))
    assert not problems, problems


def test_b1_invalid_value_raises_on_single_period_build():
    import pypsa

    n = fs.network("storage_single_period")
    with pypsa.option_context(fs.OPTION, "bogus"):
        with pytest.raises(ValueError):
            n.optimize.create_model()


@pytest.mark.parametrize("case", AG_CASES)
def test_ag_expression_matches_statistics(case):
    problem = fs.ag_problem(ag_network(case.split("|")[0]), case)
    assert problem is None, problem


@pytest.mark.parametrize("name", fs.SINGLE_PERIOD)
def test_u1_single_period_v1_model_matches_legacy(name):
    n = fs.network(name)
    fs.optimize(n, name)
    record = fs.record(n.model)
    record.update(objective=float(n.objective))
    differences = fs.model_differences(LEGACY[name], record)
    assert not differences, differences


@pytest.mark.parametrize("name", NETWORKS)
def test_u1_legacy_model_unchanged(name):
    record = legacy_facts()["models"][name]
    assert "error" not in record, record["error"]
    differences = fs.model_differences(LEGACY[name], record)
    assert not differences, differences


@pytest.mark.parametrize("module", sorted(API))
def test_u2_public_api_compatible(module):
    problems = fs.api_problems(API[module], submitted_api().get(module))
    assert not problems, problems


# Instances on paths the networks above never reach: secant losses, the non-linear and iterative
# entry points, component data conversion, and installed capex.
INSTANCE_KINDS = ["secant", *fs.ENTRY_INSTANCES]
# Under v1 a two-period model is built flat by design, so only these records are held to the base
# legacy record in the graded process; the legacy child holds every record to it.
V1_INSTANCES = ["secant-single", "data-single", "data-periods", "capex-periods"]


@cache
def v1_instances(value):
    return fs.instance_representation(value)


@cache
def v1_instance_records():
    return fs.instance_records()


@pytest.mark.parametrize("case", [*V1_VALUES, *LEGACY_VALUES])
@pytest.mark.parametrize("kind", INSTANCE_KINDS)
def test_cr_instance_uses_one_representation(kind, case):
    if case in V1_VALUES:
        facts = v1_instances(V1_VALUES[case])[kind]
    else:
        facts = legacy_facts()["instance_representation"][LEGACY_VALUES[case]][kind]
    problems = fs.instance_problems(facts, case in FLAT)
    assert not problems, problems


@pytest.mark.parametrize("key", V1_INSTANCES)
def test_u1_v1_instance_matches_legacy(key):
    differences = fs.instance_differences(LEGACY["instances"][key], v1_instance_records()[key])
    assert not differences, differences


@pytest.mark.parametrize("key", sorted(LEGACY["instances"]))
def test_u1_legacy_instance_unchanged(key):
    differences = fs.instance_differences(LEGACY["instances"][key], legacy_facts()["instances"][key])
    assert not differences, differences
