"""A pytest plugin that holds one library option at its graded value and keeps the test runner honest.

run_graded.py loads it with ``-p option_guard`` when the config names an ``option_guard``, and hands
it the guard spec and a nonce through a pipe it closes after reading. The plugin's state, the nonce,
its record of what each test raised, and its check functions live only in closures, never in a
module attribute, so a submission that takes this module from ``sys.modules`` reaches nothing it
can clear, read, or replace. The hooks pytest registered are those closures; rebinding the module's
names afterwards changes nothing pytest calls.

Before the library or any conftest is imported, so before any submitted code runs, the plugin
records the identity (and, for functions, the code, defaults and keyword defaults) of every runner
internal and assertion helper the spec's ``runner`` names, the import machinery, and every builtin.
It then swaps the library's options object onto a subclass that logs every read and write of the
guarded option while a test runs, and records the bindings that decide which value the library
sees. Every phase report re-checks the runner record, and every teardown re-checks all of it and
the graded test modules' own references to the recorded helpers. Independently of the report pytest
prints, the plugin records whether each phase of each test raised, from the call pytest made; the
verdict carries that record so run_graded.py can refuse a test the log calls passed that raised.
A changed binding or a moved option fails the guard. The verdict, keyed by the nonce, is written at
session end.
"""

from __future__ import annotations

import builtins
import importlib
import inspect
import json
import os
import pkgutil
import sys
import types
from pathlib import Path

import pytest


def _plugin():
    _json, _os, _sys, _importlib, _inspect, _pkgutil, _Path = json, os, sys, importlib, inspect, pkgutil, Path
    _builtins, _types = builtins, types
    _len, _isinstance, _getattr, _vars, _list, _type, _callable, _any, _all, _zip, _sorted, _str = (
        len, isinstance, getattr, vars, list, type, callable, any, all, zip, sorted, str)
    _id, _range, _int, _ImportError, _Exception = id, range, int, ImportError, Exception
    members = (types.FunctionType, staticmethod, classmethod, property)
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

    def runner_record():
        record = {path: fingerprint(resolve(path)) for path in state["spec"]["runner"]}
        record.update((f"builtins.{key}", (value,)) for key, value in _vars(_builtins).items() if _callable(value))
        return record

    def foreign(hook):
        # An import hook a library adds later (six registers one) is admitted; one whose code lives
        # in the submitted package could rewrite the graded test modules as they import.
        klass = hook if _isinstance(hook, _type) else _type(hook)
        codes = [getattr_code(v) for v in _vars(klass).values()] + [getattr_code(hook)]
        return _any(code is not None and _str(code.co_filename).startswith(state["package"]) for code in codes)

    def getattr_code(value):
        inner = value.__func__ if _isinstance(value, (staticmethod, classmethod)) else value
        return _getattr(inner, "__code__", None)

    def hooks_changed():
        changed = []
        for key, now in (("sys.meta_path", _sys.meta_path), ("sys.path_hooks", _sys.path_hooks)):
            old = state["hooks"][key]
            kept = [h for h in now if _any(h is o for o in old)]
            if _len(kept) != _len(old) or not _all(a is b for a, b in _zip(kept, old)):
                changed.append(key)
            elif _any(foreign(h) for h in now if not _any(h is o for o in old)):
                changed.append(f"{key} (a hook from the submitted package)")
        return changed

    def runner_changed():
        now = runner_record()
        changed = []
        for key, old in state["runner"].items():
            new = now.get(key)
            if new is None or not same_print(old, new):
                changed.append(key)
        return changed + hooks_changed()

    def library_inventory():
        spec, options = state["spec"], state["options"]
        found = {}
        prefix = spec["module"]
        for name, module in _list(_sys.modules.items()):
            if module is None or not (name == prefix or name.startswith(prefix + ".")):
                continue
            for attr, value in _list(_vars(module).items()):
                if value is options or _any(value is b for b in state["bound"]):
                    found[f"{name}.{attr}"] = value
        for klass in state["base"].__mro__:
            if klass.__module__.startswith(prefix):
                found.update((f"{klass.__module__}.{klass.__qualname__}.{key}", member)
                             for key, member in _list(_vars(klass).items()) if _isinstance(member, members))
        return found

    def same_value(old, new):
        # A bound value rebound to an equal one decides nothing; a function must stay the same object.
        return new is old or (not _callable(old) and _type(new) is _type(old) and new == old)

    def test_references():
        helpers = {_id(old[0]): key for key, old in state["runner"].items()}
        found = {}
        for name, module in _list(_sys.modules.items()):
            path = _getattr(module, "__file__", None)
            if not path or _str(_Path(path).resolve()) not in state["tests"]:
                continue
            for attr, value in _list(_vars(module).items()):
                if _id(value) in helpers:
                    found[f"{name}.{attr}"] = value
        return found

    def library_changed():
        spec = state["spec"]
        now = library_inventory()
        changed = [key for key, value in state["inventory"].items() if key not in now or not same_value(value, now[key])]
        if _getattr(state["library"], spec["options"]) is not state["options"]:
            changed.append(f"{spec['module']}.{spec['options']}")
        guarded = state["guarded"]
        if _type(state["options"]) is not guarded or not same_value(state["mro"], guarded.__mro__):
            changed.append(f"type({spec['module']}.{spec['options']})")
        refs = test_references()
        changed += [key for key, value in state.get("references", {}).items() if refs.get(key) is not value]
        return changed

    @pytest.hookimpl(tryfirst=True)
    def pytest_load_initial_conftests(early_config, parser, args):
        descriptor = _int(_os.environ.pop("OPTION_GUARD_FD"))
        with _os.fdopen(descriptor, "rb") as pipe:
            spec = _json.loads(pipe.read())
        state.update(spec=spec, tests={_str(_Path(p).resolve()) for p in spec["tests"]}, raised={},
                     events=[], tampered=[], runner_tampered=[], node=None, active=[False])
        # Recorded before the library, the conftest or the package is imported, so nothing a
        # submission patches at import time is taken as the original.
        state["runner"] = runner_record()
        state["hooks"] = {"sys.meta_path": _list(_sys.meta_path), "sys.path_hooks": _list(_sys.path_hooks)}
        state["package"] = _str(_Path(spec["package"]).resolve()) + _os.sep
        library = _importlib.import_module(spec["module"])
        # Every submodule is loaded now, so one the package would import later is inventoried too; a
        # submodule that cannot load here (an optional solver binding) is left out of the inventory.
        for found in _pkgutil.walk_packages(library.__path__, spec["module"] + "."):
            try:
                _importlib.import_module(found.name)
            except _Exception:
                continue
        options = _getattr(library, spec["options"])
        base = _type(options)
        option, value, events, active = spec["option"], spec["value"], state["events"], state["active"]

        class Guarded(base):
            def get_value(self, name):
                got = base.get_value(self, name)
                if active[0] and name == option and got != value:
                    events.append(f"{state['node']}: read {option}={got!r}")
                return got

            def set_value(self, **kwargs):
                if active[0] and option in kwargs and kwargs[option] != value:
                    events.append(f"{state['node']}: set {option}={kwargs[option]!r}")
                return base.set_value(self, **kwargs)

        options.__class__ = Guarded
        state.update(library=library, options=options, guarded=Guarded, mro=Guarded.__mro__, base=base,
                     bound=[resolve(path) for path in spec["bindings"]])
        state["inventory"] = library_inventory()

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(session):
        state["references"] = test_references()
        state["tampered"].extend(f"collection: {key}" for key in library_changed())
        state["runner_tampered"].extend(f"collection: {key}" for key in runner_changed())

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(item, call):
        node = state["raised"].setdefault(item.nodeid, [])
        node.append(call.excinfo is not None)
        state["runner_tampered"].extend(f"{item.nodeid} {call.when}: {key}" for key in runner_changed())
        yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(item, nextitem):
        state["node"] = item.nodeid
        state["active"][0] = True
        try:
            yield
        finally:
            state["active"][0] = False
            state["tampered"].extend(f"{item.nodeid}: {key}" for key in library_changed())
            state["runner_tampered"].extend(f"{item.nodeid}: {key}" for key in runner_changed())

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(session, exitstatus):
        events, tampered, runner = state["events"], state["tampered"], state["runner_tampered"]
        verdict = {"nonce": state["spec"]["nonce"], "holds": not events and not tampered and not runner,
                   "events": events[:20], "event_count": _len(events), "tampered": tampered[:20],
                   "tampered_count": _len(tampered), "runner_tampered": runner[:20],
                   "runner_tampered_count": _len(runner),
                   "raised": {node: _any(phases) for node, phases in _sorted(state["raised"].items())}}
        _Path(state["spec"]["verdict"]).write_text(_json.dumps(verdict, indent=1, sort_keys=True))

    return (pytest_load_initial_conftests, pytest_collection_finish, pytest_runtest_makereport,
            pytest_runtest_protocol, pytest_sessionfinish)


(pytest_load_initial_conftests, pytest_collection_finish, pytest_runtest_makereport,
 pytest_runtest_protocol, pytest_sessionfinish) = _plugin()
del _plugin
