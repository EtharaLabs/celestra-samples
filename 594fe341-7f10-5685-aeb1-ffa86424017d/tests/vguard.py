"""A pytest plugin that flags a graded run whose outcome reporting the submission tampered with.

run_graded.py loads it with ``-p vguard`` when the slot sets ``report_guard: true``. The submission's
code runs inside the pytest process it is graded by, so no isolation keeps it away from the
reporting machinery; this plugin detects instead. It is imported before any conftest or package,
records the callables that decide an outcome (the report factory, the call wrapper, the hook
caller), and wraps report making outermost: a phase whose call raised but whose final report says
passed, or any recorded callable replaced, is a finding. Every pytest process, xdist workers
included, writes its verdict keyed by the run's nonce to its own file at session end, and
run_graded.py refuses a run with a finding or with no verdict.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import _pytest.reports
import _pytest.runner
import pluggy
import pytest

FINDINGS: list[str] = []


def _callables() -> dict[str, object]:
    found = {
        "TestReport.from_item_and_call": _pytest.reports.TestReport.from_item_and_call,
        "CallInfo.from_call": _pytest.runner.CallInfo.from_call,
    }
    for name in ("call_and_report", "call_runtest_hook", "runtestprotocol"):
        if hasattr(_pytest.runner, name):
            found[f"runner.{name}"] = getattr(_pytest.runner, name)
    for module in ("_callers", "_manager"):
        holder = getattr(pluggy, module, None)
        if holder is not None and hasattr(holder, "_multicall"):
            found[f"pluggy.{module}._multicall"] = holder._multicall
    return {name: getattr(value, "__func__", value) for name, value in found.items()}


ORIGINAL = _callables()


def _replaced() -> list[str]:
    now = _callables()
    return [name for name, value in ORIGINAL.items() if now.get(name) is not value]


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is not None and report.passed:
        FINDINGS.append(f"{item.nodeid} ({call.when}) raised {call.excinfo.typename} but reports passed")
    for name in _replaced():
        finding = f"{name} was replaced during the graded run"
        if finding not in FINDINGS:
            FINDINGS.append(finding)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    for name in _replaced():
        finding = f"{name} was replaced during the graded run"
        if finding not in FINDINGS:
            FINDINGS.append(finding)
    verdicts = Path(os.environ["VGUARD_DIR"])
    verdicts.mkdir(parents=True, exist_ok=True)
    (verdicts / f"{os.getpid()}.json").write_text(
        json.dumps({"nonce": os.environ["VGUARD_NONCE"], "findings": FINDINGS}))
