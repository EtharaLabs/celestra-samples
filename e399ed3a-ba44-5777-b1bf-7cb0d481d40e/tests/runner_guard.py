"""A pytest plugin that keeps the test runner and its assertion helpers honest during the graded run.

run_graded.py loads it with ``-p runner_guard`` and hands it the guard spec and a nonce through a
pipe it closes after reading. The plugin's state, the nonce, its record of what each test raised,
and its check functions live only in closures, never in a module attribute, so a submission that
takes this module from ``sys.modules`` reaches nothing it can clear, read, or replace. The hooks
pytest registered are those closures; rebinding the module's names afterwards changes nothing
pytest calls.

Before any conftest or graded test module is imported, so before any submitted code runs, the
plugin records the identity (and, for functions, the code, defaults and keyword defaults) of every
runner internal and assertion helper the spec's ``runner`` names, the import machinery, and every
builtin. It then imports the sealed test helpers the spec's ``helpers`` names, which imports the
submitted package, and records them only if their code lives in the sealed helper file. Every phase
report re-checks the record, and every teardown also re-checks the graded test modules' own
references to the recorded helpers. Independently of the report pytest prints, the plugin records
whether each phase of each test raised, from the call pytest made; the verdict carries that record
so run_graded.py can refuse a test the log calls passed that raised. The verdict, keyed by the
nonce, is written at session end.
"""

from __future__ import annotations

import builtins
import importlib
import inspect
import json
import os
import sys
import types
from pathlib import Path

import pytest


def _plugin():
    _json, _os, _sys, _importlib, _inspect, _Path = json, os, sys, importlib, inspect, Path
    _builtins, _types = builtins, types
    _len, _isinstance, _getattr, _vars, _list, _type, _callable, _any, _all, _zip, _sorted, _str = (
        len, isinstance, getattr, vars, list, type, callable, any, all, zip, sorted, str)
    _id, _range, _int, _ImportError = id, range, int, ImportError
    state: dict = {}

    def resolve(path):
        parts = path.split(".")
        for cut in _range(_len(parts), 0, -1):
            try:
                found = _importlib.import_module(".".join(parts[:cut]))
            except _ImportError:
                continue
            for name in parts[cut:]:
                found = _inspect.getattr_static(found, name)
            return found
        raise ImportError(path)

    def fingerprint(value):
        inner = value.__func__ if _isinstance(value, (staticmethod, classmethod)) else value
        inner = inner.fget if _isinstance(inner, property) else inner
        if _isinstance(inner, _types.FunctionType):
            return (value, inner.__code__, inner.__defaults__, inner.__kwdefaults__)
        return (value,)

    def same_print(old, new):
        return _len(old) == _len(new) and _all(a is b for a, b in _zip(old, new))

    def code_of(value):
        inner = value.__func__ if _isinstance(value, (staticmethod, classmethod)) else value
        return _getattr(inner, "__code__", None)

    def runner_record():
        record = {path: fingerprint(resolve(path)) for path in state["spec"]["runner"]}
        record.update((f"builtins.{key}", (value,)) for key, value in _vars(_builtins).items() if _callable(value))
        return record

    def helper_record():
        record, foreign = {}, []
        for path in state["spec"]["helpers"]:
            value = resolve(path)
            code = code_of(value)
            if code is not None:
                origin = code.co_filename
            else:
                module = _sys.modules.get(_getattr(value, "__module__", None) or "")
                origin = _getattr(module, "__file__", None) if _isinstance(value, _type) else None
            if not origin or _str(_Path(origin).resolve()) != state["sealed_origin"]:
                foreign.append(path)
            record[path] = fingerprint(value)
        return record, foreign

    def foreign_hook(hook):
        # An import hook a library adds later is admitted; one whose code lives in the submitted
        # package could rewrite the graded test modules as they import.
        klass = hook if _isinstance(hook, _type) else _type(hook)
        codes = [code_of(v) for v in _vars(klass).values()] + [code_of(hook)]
        return _any(code is not None and _str(code.co_filename).startswith(state["package"]) for code in codes)

    def hooks_changed():
        changed = []
        for key, now in (("sys.meta_path", _sys.meta_path), ("sys.path_hooks", _sys.path_hooks)):
            old = state["hooks"][key]
            kept = [h for h in now if _any(h is o for o in old)]
            if _len(kept) != _len(old) or not _all(a is b for a, b in _zip(kept, old)):
                changed.append(key)
            elif _any(foreign_hook(h) for h in now if not _any(h is o for o in old)):
                changed.append(f"{key} (a hook from the submitted package)")
        return changed

    def runner_changed():
        changed = []
        for record, now in ((state["runner"], runner_record()), (state["helpers"], helper_record()[0])):
            for key, old in record.items():
                new = now.get(key)
                if new is None or not same_print(old, new):
                    changed.append(key)
        return changed + hooks_changed()

    def test_references():
        recorded = {**state["runner"], **state["helpers"]}
        helpers = {_id(old[0]): key for key, old in recorded.items()}
        found = {}
        for name, module in _list(_sys.modules.items()):
            path = _getattr(module, "__file__", None)
            if not path or _str(_Path(path).resolve()) not in state["tests"]:
                continue
            for attr, value in _list(_vars(module).items()):
                if _id(value) in helpers:
                    found[f"{name}.{attr}"] = value
        return found

    def references_changed():
        refs = test_references()
        return [key for key, value in state.get("references", {}).items() if refs.get(key) is not value]

    @pytest.hookimpl(tryfirst=True)
    def pytest_load_initial_conftests(early_config, parser, args):
        descriptor = _int(_os.environ.pop("RUNNER_GUARD_FD"))
        with _os.fdopen(descriptor, "rb") as pipe:
            spec = _json.loads(pipe.read())
        state.update(spec=spec, tests={_str(_Path(p).resolve()) for p in spec["tests"]}, raised={},
                     tampered=[], node=None)
        # Recorded before the conftest or the package is imported, so nothing a submission
        # patches at import time is taken as the original.
        state["runner"] = runner_record()
        state["hooks"] = {"sys.meta_path": _list(_sys.meta_path), "sys.path_hooks": _list(_sys.path_hooks)}
        state["package"] = _str(_Path(spec["package"]).resolve()) + _os.sep
        state["sealed_origin"] = _str(_Path(spec["helper_file"]).resolve())
        state["helpers"], foreign = helper_record()
        state["tampered"].extend(f"import: {path} is not the sealed helper" for path in foreign)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(session):
        state["references"] = test_references()
        state["tampered"].extend(f"collection: {key}" for key in runner_changed())

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(item, call):
        node = state["raised"].setdefault(item.nodeid, [])
        node.append(call.excinfo is not None)
        state["tampered"].extend(f"{item.nodeid} {call.when}: {key}" for key in runner_changed())
        yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(item, nextitem):
        state["node"] = item.nodeid
        try:
            yield
        finally:
            changed = runner_changed() + references_changed()
            state["tampered"].extend(f"{item.nodeid}: {key}" for key in changed)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(session, exitstatus):
        tampered = state["tampered"]
        verdict = {"nonce": state["spec"]["nonce"], "holds": not tampered, "tampered": tampered[:20],
                   "tampered_count": _len(tampered),
                   "raised": {node: _any(phases) for node, phases in _sorted(state["raised"].items())}}
        _Path(state["spec"]["verdict"]).write_text(_json.dumps(verdict, indent=1, sort_keys=True))

    return (pytest_load_initial_conftests, pytest_collection_finish, pytest_runtest_makereport,
            pytest_runtest_protocol, pytest_sessionfinish)


(pytest_load_initial_conftests, pytest_collection_finish, pytest_runtest_makereport,
 pytest_runtest_protocol, pytest_sessionfinish) = _plugin()
del _plugin
