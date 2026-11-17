"""Shared support for test_forge_requirements.py: networks, model records, and API inventories.

Run as a script it writes the base-commit fixtures the requirement tests compare against, or
the facts one semantics run produces:

    python forge_support.py fixtures OUT_DIR
    python forge_support.py facts SEMANTICS OUT.json

The fixtures were written once from the unmodified base commit under the legacy semantics and
are sealed beside this module, so grading never solves the base again. The facts run in a child
process so a run under the legacy semantics never changes the linopy option of the graded test
process.
"""

from __future__ import annotations

import importlib
import inspect
import json
import math
import pkgutil
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES = Path(__file__).resolve().parent
SIGNIFICANT = 12
REL_TOL = 1e-6
AG_TOL = 1e-2
MULTI_PERIOD = ("storage_cyclic_per_period", "ramp_and_limits", "meshed_two_periods",
                "commitment_two_windows", "commitment_linear_periods", "commitment_modular_periods",
                "limits_periods", "losses_periods", "grid_periods")
SINGLE_PERIOD = ("storage_single_period", "ramp_single_period", "meshed_single_period",
                 "commitment_single_period", "commitment_linear_single", "commitment_modular_single",
                 "limits_single_period", "losses_single_period", "grid_single_period",
                 "commitment_rolling_horizon", "meshed_security_constrained")
OPTION = "optimization.model_snapshot_index"


def _semantics(value: str) -> None:
    import linopy

    linopy.options["semantics"] = value


# ---------------------------------------------------------------------------------------------
# Networks


def _periods(n, weights):
    n.investment_periods = [2020, 2030, 2040]
    n.investment_period_weightings.loc[:, "objective"] = list(weights)
    n.investment_period_weightings.loc[:, "years"] = [10, 10, 10]


def _storage(periods):
    import pypsa

    n = pypsa.Network(snapshots=range(6))
    if periods:
        _periods(n, (1.0, 2.0, 3.0))
    reps = 3 if periods else 1
    years = n.investment_periods if periods else [2020, 2030, 2040]
    n.add("Bus", ["a", "b"])
    for i, year in enumerate(years):
        n.add("Generator", f"g-{year}", bus="a", **({"build_year": year, "lifetime": 30} if periods else {}),
              p_nom_extendable=True, capital_cost=50 + 5 * i, marginal_cost=3 + i,
              p_max_pu=[1, 1, 0.2, 0.1, 1, 1] * reps)
    n.add("Generator", "peak", bus="b", p_nom=500, marginal_cost=40)
    n.add("Line", "ab", bus0="a", bus1="b", x=0.01, r=0.001, s_nom_extendable=True, capital_cost=7)
    n.add("StorageUnit", "su", bus="b", p_nom_extendable=True, capital_cost=0.5, max_hours=6,
          cyclic_state_of_charge=True, cyclic_state_of_charge_per_period=periods)
    n.add("Store", "st", bus="a", e_nom_extendable=True, capital_cost=2, e_cyclic=False, e_initial=5,
          e_initial_per_period=periods)
    la = [20, 30, 50, 60, 25, 5, 90, 30, 50, 60, 25, 5, 90, 30, 20, 60, 25, 20]
    lb = [40, 35, 60, 70, 45, 5, 95, 35, 60, 70, 45, 5, 95, 35, 60, 70, 45, 30]
    n.add("Load", "la", bus="a", p_set=la[: 6 * reps])
    n.add("Load", "lb", bus="b", p_set=lb[: 6 * reps])
    return n


def _ramp(periods):
    import pypsa

    n = pypsa.Network(snapshots=range(5))
    if periods:
        _periods(n, (1.0, 0.5, 0.25))
    reps = 3 if periods else 1
    n.add("Carrier", ["gas", "wind"], co2_emissions=[0.2, 0.0])
    n.add("Bus", "a")
    n.add("Generator", "gas", bus="a", carrier="gas", p_nom=200, marginal_cost=20,
          ramp_limit_up=0.3, ramp_limit_down=0.3)
    n.add("Generator", "wind", bus="a", carrier="wind", p_nom_extendable=True, capital_cost=30,
          p_max_pu=[0.9, 0.5, 0.1, 0.6, 0.8] * reps, **({"build_year": 2020, "lifetime": 50} if periods else {}))
    n.add("Load", "l", bus="a", p_set=[60, 80, 120, 90, 70] * reps)
    if periods:
        n.add("GlobalConstraint", "co2", type="primary_energy", carrier_attribute="co2_emissions",
              sense="<=", constant=40, investment_period=2030)
    return n


def _meshed(periods):
    import pypsa

    n = pypsa.examples.ac_dc_meshed()
    n.c.lines.static["carrier"] = n.c.lines.static.bus0.map(n.c.buses.static.carrier)
    if periods:
        n.snapshots = pd.MultiIndex.from_product([[2020, 2030], n.snapshots])
        n.investment_periods = [2020, 2030]
    return n


LOAD = [60, 120, 180, 210, 90, 40, 150, 200]


def _commitment(periods, maintenance=True, energy=True):
    """Committable units with minimum up and down times, start-up and shut-down ramps, maintenance."""
    import pypsa

    n = pypsa.Network(snapshots=range(len(LOAD)))
    if periods:
        _periods(n, (1.0, 0.5, 0.25))
    reps = 3 if periods else 1
    n.add("Carrier", ["coal", "gas", "bio", "wind"], co2_emissions=[0.9, 0.4, 0.0, 0.0])
    n.add("Bus", "a")
    n.add("Generator", "coal", bus="a", carrier="coal", committable=True, p_nom=100, p_min_pu=0.4,
          min_up_time=3, min_down_time=2, up_time_before=1, start_up_cost=50, shut_down_cost=20,
          ramp_limit_up=0.6, ramp_limit_down=0.6, ramp_limit_start_up=0.5, ramp_limit_shut_down=0.5,
          marginal_cost=10)
    n.add("Generator", "ccgt", bus="a", carrier="gas", committable=True, p_nom_extendable=True,
          p_nom_max=150, capital_cost=20, p_min_pu=0.3, min_up_time=2, start_up_cost=10,
          ramp_limit_up=0.8, ramp_limit_down=0.8, marginal_cost=20)
    n.add("Generator", "modular", bus="a", carrier="gas", committable=True, p_nom_extendable=True,
          p_nom_mod=30, p_nom_max=90, capital_cost=25, min_down_time=2, marginal_cost=15)
    if maintenance:
        n.add("Generator", "maint-fix", bus="a", carrier="wind", maintainable=True, p_nom=80,
              maintenance_duration=2, maintenance_events=1, marginal_cost=5)
        n.add("Generator", "maint-ext", bus="a", carrier="wind", maintainable=True, p_nom_extendable=True,
              p_nom_max=60, capital_cost=15, maintenance_duration=2, maintenance_pu=0.5, marginal_cost=6)
        n.add("Generator", "maint-com", bus="a", carrier="coal", maintainable=True, committable=True,
              p_nom=50, p_min_pu=0.2, maintenance_duration=1, marginal_cost=12)
    if energy:
        n.add("Generator", "bio", bus="a", carrier="bio", p_nom=40, marginal_cost=30,
              e_sum_min=50 * reps, e_sum_max=150 * reps)
    n.add("Generator", "peak", bus="a", carrier="gas", p_nom=400, marginal_cost=100)
    n.add("Load", "l", bus="a", p_set=LOAD * reps)
    if periods:
        for gen in ("ccgt", "modular"):
            n.c.generators.static.loc[gen, ["build_year", "lifetime"]] = [2020, 50]
    return n


def _linear_commitment(periods, modular=False):
    """Equal start-up and shut-down costs, committable maintenance on extendable and modular units."""
    import pypsa

    n = pypsa.Network(snapshots=range(len(LOAD)))
    if periods:
        _periods(n, (1.0, 0.5, 0.25))
    reps = 3 if periods else 1
    n.add("Bus", "a")
    n.add("Generator", "coal", bus="a", committable=True, p_nom=100, p_min_pu=0.4, min_up_time=2,
          start_up_cost=30, shut_down_cost=30, ramp_limit_up=0.6, ramp_limit_down=0.6,
          ramp_limit_start_up=0.5, ramp_limit_shut_down=0.5, marginal_cost=10)
    n.add("Generator", "ccgt", bus="a", committable=True, maintainable=True, p_nom_extendable=True,
          p_nom_max=150, capital_cost=20, p_min_pu=0.3, maintenance_duration=1, maintenance_pu=0.5,
          start_up_cost=10, shut_down_cost=10, marginal_cost=20)
    if modular:
        n.add("Generator", "modm", bus="a", committable=True, maintainable=True, p_nom_extendable=True,
              p_nom_mod=30, p_nom_max=90, capital_cost=25, maintenance_duration=1, marginal_cost=15)
    n.add("Generator", "peak", bus="a", p_nom=400, marginal_cost=100)
    n.add("Load", "l", bus="a", p_set=LOAD * reps)
    if periods:
        for gen in ("ccgt", "modm") if modular else ("ccgt",):
            n.c.generators.static.loc[gen, ["build_year", "lifetime"]] = [2020, 50]
    return n


def _limits(periods):
    """Primary energy, operational, and transmission limits over the storage network."""
    n = _storage(periods)
    n.add("Carrier", ["fossil", "store"], co2_emissions=[0.5, 0.1])
    n.c.generators.static["carrier"] = "fossil"
    # The base cannot build per-period storage with an emitting carrier under a primary energy
    # limit even under legacy semantics, so only the single-period network gives storage a carrier.
    if not periods:
        n.c.storage_units.static.loc["su", "carrier"] = "store"
        n.c.storage_units.static.loc["su", ["cyclic_state_of_charge", "state_of_charge_initial"]] = [False, 10]
        n.c.stores.static.loc["st", "carrier"] = "store"
    n.c.lines.static["carrier"] = "AC"
    # Limits count energy with the generators weighting, the objective with its own; keeping
    # the two apart makes a model that reads the wrong column differ from the base.
    n.snapshot_weightings["generators"] = 0.5
    kw = {"investment_period": 2030} if periods else {}
    scale = 20 if periods else 1
    n.add("GlobalConstraint", "co2", type="primary_energy", carrier_attribute="co2_emissions",
          sense="<=", constant=2000 * scale, **kw)
    n.add("GlobalConstraint", "fossil-cap", type="operational_limit", carrier_attribute="fossil",
          sense="<=", constant=1500 * scale, **kw)
    n.add("GlobalConstraint", "store-cap", type="operational_limit", carrier_attribute="store",
          sense="<=", constant=400 * scale, **kw)
    n.add("GlobalConstraint", "volume", type="transmission_volume_expansion_limit",
          carrier_attribute="AC", sense="<=", constant=500 * scale, **kw)
    n.add("GlobalConstraint", "cost", type="transmission_expansion_cost_limit",
          carrier_attribute="AC", sense="<=", constant=5000 * scale, **kw)
    return n


def _losses(periods):
    n = _meshed(periods)
    n.c.lines.static["s_nom_max"] = n.c.lines.static.s_nom * 3 + 1000
    return n


def _grid(periods):
    """A transformer cycle with a variable phase shift, fixed dispatch, non-extendable modular commitment."""
    import pypsa

    n = pypsa.Network(snapshots=range(4))
    if periods:
        _periods(n, (1.0, 0.5, 0.25))
    reps = 3 if periods else 1
    n.add("Bus", ["a", "b", "c"], v_nom=380)
    n.add("Line", "ab", bus0="a", bus1="b", x=0.1, r=0.01, s_nom=80, s_nom_extendable=True,
          s_nom_max=300, capital_cost=5)
    n.add("Line", "bc", bus0="b", bus1="c", x=0.1, r=0.01, s_nom=80, s_nom_extendable=True,
          s_nom_max=300, capital_cost=5)
    n.add("Transformer", "ca", bus0="c", bus1="a", x=0.1, r=0.01, s_nom=200,
          phase_shift_min=-10, phase_shift_max=10)
    n.add("Generator", "base", bus="a", p_nom=300, marginal_cost=5)
    n.add("Generator", "fixed", bus="b", p_nom=50, marginal_cost=1, p_set=[10, 20, 30, 40] * reps)
    n.add("Generator", "mod", bus="c", committable=True, p_nom=60, p_nom_mod=30, p_min_pu=0.5,
          marginal_cost=8)
    n.add("Load", "lb", bus="b", p_set=[90, 120, 150, 110] * reps)
    n.add("Load", "lc", bus="c", p_set=[50, 60, 70, 40] * reps)
    return n


def _extra(n, sns):
    """An extra_functionality hook that adds one constraint on the model it is handed."""
    n.model.add_constraints(n.model["Generator-p"].sel(name="base") <= 250, name="forge-extra")


NETWORKS = {
    "storage_cyclic_per_period": lambda: _storage(True),
    "ramp_and_limits": lambda: _ramp(True),
    "meshed_two_periods": lambda: _meshed(True),
    "storage_single_period": lambda: _storage(False),
    "ramp_single_period": lambda: _ramp(False),
    "meshed_single_period": lambda: _meshed(False),
    "commitment_two_windows": lambda: _commitment(True),
    "commitment_single_period": lambda: _commitment(False),
    "commitment_linear_periods": lambda: _linear_commitment(True),
    "commitment_linear_single": lambda: _linear_commitment(False),
    "commitment_modular_periods": lambda: _linear_commitment(True, modular=True),
    "commitment_modular_single": lambda: _linear_commitment(False, modular=True),
    "limits_periods": lambda: _limits(True),
    "limits_single_period": lambda: _limits(False),
    "losses_periods": lambda: _losses(True),
    "losses_single_period": lambda: _losses(False),
    "grid_periods": lambda: _grid(True),
    "grid_single_period": lambda: _grid(False),
    "commitment_rolling_horizon": lambda: _commitment(False, maintenance=False, energy=False),
    "meshed_security_constrained": lambda: _meshed(False),
}
# Options each network is solved with, beyond the solver and the investment-period switch.
OPTIONS = {
    "commitment_linear_periods": {"linearized_unit_commitment": True},
    "commitment_linear_single": {"linearized_unit_commitment": True},
    "losses_periods": {"transmission_losses": 2},
    "losses_single_period": {"transmission_losses": 2},
    "grid_periods": {"transmission_losses": 2, "extra_functionality": _extra},
    "grid_single_period": {"transmission_losses": 2, "extra_functionality": _extra},
}


def network(name):
    return NETWORKS[name]()


def optimize(n, name, **kwargs):
    """Build and solve; multi-period networks optimise over their investment periods.

    The rolling-horizon and security-constrained networks go through those entry points; their
    record is the model the last window, or the security-constrained run, built.
    """
    kwargs = {**OPTIONS.get(name, {}), **kwargs}
    if name in MULTI_PERIOD:
        kwargs.setdefault("multi_investment_periods", True)
    return ENTRY_POINTS.get(name, _plain)(n, **kwargs)


def _plain(n, **kwargs):
    return n.optimize(solver_name="highs", **kwargs)


def _rolling_horizon(n, **kwargs):
    return n.optimize.optimize_with_rolling_horizon(horizon=4, overlap=1, solver_name="highs", **kwargs)


def _security_constrained(n, **kwargs):
    return n.optimize.optimize_security_constrained(branch_outages=n.c.lines.static.index[:2],
                                                    solver_name="highs", **kwargs)


ENTRY_POINTS = {
    "commitment_rolling_horizon": _rolling_horizon,
    "meshed_security_constrained": _security_constrained,
}


# ---------------------------------------------------------------------------------------------
# Model records keyed by name and coordinate


def _round(value: float) -> float:
    if value == 0 or not math.isfinite(value):
        return float(value)
    return float(f"{value:.{SIGNIFICANT}g}")


def _scalar(value):
    if isinstance(value, tuple):
        return [str(v.item() if hasattr(v, "item") else v) for v in value]
    return str(value.item() if hasattr(value, "item") else value)


def _keys(labels):
    """The coordinate key of every cell; flat tuple labels and a MultiIndex key alike."""
    dims = list(labels.dims)
    values = [list(labels.indexes[d]) if d in labels.indexes else list(range(labels.sizes[d])) for d in dims]
    out = {}
    for idx in np.ndindex(labels.shape):
        key = {}
        for d, i in zip(dims, idx):
            v = _scalar(values[dims.index(d)][i])
            key[d] = v
        out[idx] = json.dumps(sorted(key.items()))
    return out


def record(model) -> dict:
    """Variables with bounds, constraints with terms, and objective terms, keyed by name and coordinate."""
    names: dict[int, str] = {}
    variables: dict[str, list[float]] = {}
    for name in model.variables:
        var = model.variables[name]
        lab = var.labels
        lo = np.broadcast_to(var.lower.values, lab.shape)
        up = np.broadcast_to(var.upper.values, lab.shape)
        for idx, key in _keys(lab).items():
            label = int(lab.values[idx])
            if label < 0:
                continue
            full = f"{name}|{key}"
            names[label] = full
            variables[full] = [_round(float(lo[idx])), _round(float(up[idx]))]
    rows: dict[str, list] = {}
    for name in model.constraints:
        con = model.constraints[name]
        lab = con.labels
        vars_, coeffs = con.vars.values, con.coeffs.values
        rhs = np.broadcast_to(con.rhs.values, lab.shape)
        sign = np.broadcast_to(con.sign.values, lab.shape)
        for idx, key in _keys(lab).items():
            if int(lab.values[idx]) < 0:
                continue
            terms: dict[str, float] = {}
            for v, c in zip(np.atleast_1d(vars_[idx]), np.atleast_1d(coeffs[idx])):
                if int(v) >= 0 and c != 0:
                    terms[names[int(v)]] = terms.get(names[int(v)], 0.0) + float(c)
            rows[f"{name}|{key}"] = [{k: _round(c) for k, c in sorted(terms.items())}, str(sign[idx]),
                                     _round(float(rhs[idx]))]
    expression = getattr(model.objective, "expression", model.objective)
    objective: dict[str, float] = {}
    for v, c in zip(np.ravel(expression.vars.values), np.ravel(expression.coeffs.values)):
        if int(v) >= 0 and c != 0:
            objective[names[int(v)]] = objective.get(names[int(v)], 0.0) + float(c)
    return {"variables": variables, "rows": rows, "objective_terms": {k: _round(c) for k, c in sorted(objective.items())},
            "_names": names}


def solution(model, names) -> dict[str, float]:
    out = {}
    for name in model.variables:
        var = model.variables[name]
        lab, sol = var.labels.values, np.broadcast_to(var.solution.values, var.labels.shape)
        for idx in np.ndindex(lab.shape):
            if int(lab[idx]) >= 0:
                out[names[int(lab[idx])]] = float(sol[idx])
    return out


def solved_record(name: str) -> dict:
    n = network(name)
    result = optimize(n, name)
    status, condition = result if isinstance(result, tuple) else ("ok", "optimal")
    rec = record(n.model)
    rec.pop("_names")
    rec.update(status=status, condition=condition, objective=_round(float(n.objective)),
               constant=_round(float(n.model.objective.expression.const.sum())))
    return rec


def _close(a: float, b: float, tol: float = REL_TOL) -> bool:
    if a == b:
        return True
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def _same_bounds(x, y) -> bool:
    return all(_close(p, q) for p, q in zip(x, y))


def _same_row(x, y) -> bool:
    return (x[1] == y[1] and _close(x[2], y[2]) and set(x[0]) == set(y[0])
            and all(_close(x[0][t], y[0][t]) for t in x[0]))


def model_differences(base: dict, sub: dict) -> list[str]:
    """How a model record differs from the base record, order ignored."""
    found = []
    for part, same_entry in (("variables", _same_bounds), ("rows", _same_row),
                             ("objective_terms", _close)):
        b, s = base[part], sub[part]
        if set(b) != set(s):
            lost, extra = sorted(set(b) - set(s)), sorted(set(s) - set(b))
            found.append(f"{part}: {len(lost)} lost {lost[:2]}, {len(extra)} extra {extra[:2]}")
            continue
        for key in b:
            x, y = b[key], s[key]
            if not same_entry(x, y):
                found.append(f"{part}: {key} is {y}, base {x}")
                break
    if not _close(base["objective"], sub["objective"]):
        found.append(f"objective {sub['objective']} differs from base {base['objective']}")
    return found


def legacy_optimum_problems(base: dict, n) -> list[str]:
    """Whether a solved model reaches the base legacy optimum with a solution feasible in the base model."""
    found = []
    if not _close(float(n.objective), base["objective"]):
        found.append(f"objective {n.objective} differs from the legacy optimum {base['objective']}")
    rec = record(n.model)
    x = solution(n.model, rec["_names"])
    missing = [k for k in base["variables"] if k not in x]
    if missing:
        return [*found, f"{len(missing)} base variables have no counterpart, e.g. {missing[:2]}"]
    for key, (lo, up) in base["variables"].items():
        if x[key] < lo - 1e-6 * max(1, abs(lo)) or x[key] > up + 1e-6 * max(1, abs(up)):
            found.append(f"{key}={x[key]} outside the base bounds [{lo}, {up}]")
            break
    for key, (terms, sign, rhs) in base["rows"].items():
        lhs = sum(c * x[v] for v, c in terms.items())
        scale = max(1.0, abs(rhs), *(abs(c * x[v]) for v, c in terms.items()))
        gap = {"<=": lhs - rhs, ">=": rhs - lhs, "=": abs(lhs - rhs)}[sign]
        if gap > 1e-6 * scale:
            found.append(f"base constraint {key} violated by {gap}")
            break
    attained = sum(c * x[v] for v, c in base["objective_terms"].items()) + base["constant"]
    if not _close(attained, base["objective"]):
        found.append(f"the solution attains {attained} in the base model, not its optimum {base['objective']}")
    return found


# ---------------------------------------------------------------------------------------------
# Snapshot representation facts


def _is_multi(index) -> bool:
    return isinstance(index, pd.MultiIndex)


def representation(n, snapshots, extra_seen, component_data=True) -> dict:
    """What every snapshot-indexed part of a built model carries, as plain facts; component_data
    False leaves out the generators' p_max_pu, for a network a failed power flow left behind."""
    m = n.model
    flat_labels = [list(map(_scalar, t)) if isinstance(t, tuple) else _scalar(t) for t in snapshots]
    parts = []
    for kind, container in (("variable", m.variables), ("constraint", m.constraints)):
        for name in list(container):
            lab = container[name].labels
            if "snapshot" not in lab.dims:
                continue
            ix = lab.indexes["snapshot"]
            coords = list(lab.coords)
            at = coords.index("snapshot")
            parts.append({
                "part": f"{kind} {name}",
                "multiindex": _is_multi(ix),
                "labels": [_scalar(t) for t in ix],
                "after_snapshot": coords[at + 1: at + 3],
                "period": [_scalar(v) for v in lab.coords["period"].values] if "period" in lab.coords else None,
                "timestep": [_scalar(v) for v in lab.coords["timestep"].values] if "timestep" in lab.coords else None,
            })
    params = m.parameters.snapshots.to_index()
    if not component_data:
        return {"build_snapshots": flat_labels,
                "parameters": {"multiindex": _is_multi(params), "labels": [_scalar(t) for t in params]},
                "extra_functionality": [], "parts": parts}
    da = n.c.generators.da.p_max_pu
    dix = da.indexes["snapshot"]
    dcoords = list(da.coords)
    at = dcoords.index("snapshot")
    parts.append({"part": "component data generators.p_max_pu", "multiindex": _is_multi(dix),
                  "labels": [_scalar(t) for t in dix], "after_snapshot": dcoords[at + 1: at + 3],
                  "period": [_scalar(v) for v in da.coords["period"].values] if "period" in da.coords else None,
                  "timestep": [_scalar(v) for v in da.coords["timestep"].values] if "timestep" in da.coords else None})
    return {"build_snapshots": flat_labels,
            "parameters": {"multiindex": _is_multi(params), "labels": [_scalar(t) for t in params]},
            "extra_functionality": [{"multiindex": _is_multi(s), "labels": [_scalar(t) for t in s]} for s in extra_seen],
            "parts": parts}


def _option_value(pypsa):
    value = pypsa.options
    for part in OPTION.split("."):
        value = getattr(value, part)
    return value


def representation_facts(value: str | None) -> dict:
    """Build and solve the storage network under one option value, or the default when None,
    once in two steps and once through n.optimize()."""
    import pypsa

    n = network("storage_cyclic_per_period")
    seen = []
    snapshots = n.snapshots[:12]
    if value is None:
        default = _option_value(pypsa)
        n.optimize.create_model(snapshots=snapshots, multi_investment_periods=True)
        n.optimize.solve_model(solver_name="highs", extra_functionality=lambda _, s: seen.append(s))
    else:
        default = None
        with pypsa.option_context(OPTION, value):
            n.optimize.create_model(snapshots=snapshots, multi_investment_periods=True)
            n.optimize.solve_model(solver_name="highs", extra_functionality=lambda _, s: seen.append(s))
    # The one-step n.optimize() call hands extra_functionality its snapshots on a path of its own.
    one_step = network("storage_cyclic_per_period")
    if value is None:
        one_step.optimize(snapshots=snapshots, multi_investment_periods=True, solver_name="highs",
                          extra_functionality=lambda _, s: seen.append(s))
    else:
        with pypsa.option_context(OPTION, value):
            one_step.optimize(snapshots=snapshots, multi_investment_periods=True, solver_name="highs",
                              extra_functionality=lambda _, s: seen.append(s))
    return {"default": default, **representation(n, snapshots, seen)}


def representation_problems(facts: dict, flat: bool) -> list[str]:
    """Whether every part of a model carries the selected representation of its build snapshots."""
    found = []
    want = facts["build_snapshots"]
    checks = [("model parameters snapshots", facts["parameters"])]
    checks += [(f"extra_functionality call {i}", s) for i, s in enumerate(facts["extra_functionality"])]
    checks += [(p["part"], p) for p in facts["parts"]]
    if not facts["extra_functionality"]:
        found.append("extra_functionality was never called")
    for where, fact in checks:
        if fact["multiindex"] == flat:
            found.append(f"{where} is {'a MultiIndex' if fact['multiindex'] else 'flat'}")
        elif fact["labels"] != want and where.startswith(("model", "extra")):
            found.append(f"{where} labels are not the build snapshots")
        elif where.startswith(("variable", "constraint")) and fact["labels"] != want:
            found.append(f"{where} labels are not the build snapshots")
    return found


def layout_problems(facts: dict) -> list[str]:
    """Whether every flat snapshot dimension is followed by period and timestep coordinates, in order."""
    found = []
    for p in facts["parts"]:
        if p["multiindex"]:
            found.append(f"{p['part']} keeps a MultiIndex")
            continue
        if p["after_snapshot"] != ["period", "timestep"]:
            found.append(f"{p['part']} coordinates after snapshot are {p['after_snapshot']}")
            continue
        if p["period"] != [t[0] for t in p["labels"]] or p["timestep"] != [t[1] for t in p["labels"]]:
            found.append(f"{p['part']} period or timestep values do not match its labels")
    return found


# ---------------------------------------------------------------------------------------------
# Instances on paths no network above reaches: secant losses, the iterative and non-linear
# entry points, component data conversion, and installed capex


def secant_model(periods: bool):
    """The meshed network with secant transmission losses, built and not solved."""
    n = _losses(periods)
    n.optimize.create_model(multi_investment_periods=periods, transmission_losses=True)
    return n


def secant_record(periods: bool) -> dict:
    rec = record(secant_model(periods).model)
    rec.pop("_names")
    rec.update(objective=0.0)
    return rec


def _nonlinear(n):
    n.optimize.optimize_and_run_non_linear_powerflow(multi_investment_periods=True, solver_name="highs")


def _iterative(n):
    lines = n.c.lines.static
    lines["s_nom_min"] = lines.s_nom
    lines["s_nom_max"] = lines.s_nom * 4
    lines["s_nom_opt"] = lines.s_nom
    n.optimize.optimize_transmission_expansion_iteratively(min_iterations=1, max_iterations=2,
                                                           multi_investment_periods=True, solver_name="highs")


ENTRY_INSTANCES = {"nonlinear": _nonlinear, "iterative": _iterative}


def _entry_parts(kind: str) -> dict:
    """The model an entry point builds and solves on the two-period meshed network; the power flow
    that follows the non-linear entry may fail, which leaves its solved model to inspect."""
    n = _meshed(True)
    raised = None
    try:
        ENTRY_INSTANCES[kind](n)
    except Exception as error:
        raised = f"{type(error).__name__}: {error}"[:300]
    try:
        objective = float(n.objective)
    except (AttributeError, TypeError, ValueError):
        objective = math.nan
    if not math.isfinite(objective):
        return {"error": f"no solved model ({raised})"}
    return representation(n, n.snapshots, [], component_data=False)


def instance_representation(value: str | None) -> dict:
    import pypsa

    out = {}
    for kind, build in (("secant", lambda: representation(secant_model(True), _meshed(True).snapshots, [])),
                        *((k, lambda k=k: _entry_parts(k)) for k in ENTRY_INSTANCES)):
        try:
            if value is None:
                out[kind] = build()
            else:
                with pypsa.option_context(OPTION, value):
                    out[kind] = build()
        except Exception as error:
            out[kind] = {"error": f"{type(error).__name__}: {error}"[:300]}
    return out


def instance_problems(facts: dict, flat: bool) -> list[str]:
    """Whether every snapshot-indexed part of an instance's model carries the selected representation."""
    if "error" in facts:
        return [facts["error"]]
    found = []
    params, want = facts["parameters"], facts["build_snapshots"]
    if params["multiindex"] == flat:
        found.append("model parameters snapshots carry the other representation")
    for part in facts["parts"]:
        if part["multiindex"] == flat:
            found.append(f"{part['part']} is {'a MultiIndex' if part['multiindex'] else 'flat'}")
        elif part["labels"] != want:
            found.append(f"{part['part']} labels are not the build snapshots")
    return found


def _frame(obj) -> dict:
    frame = obj.to_frame() if isinstance(obj, pd.Series) else obj
    values = [[None if pd.isna(v) else _round(float(v)) for v in row] for row in frame.to_numpy()]
    return {"index": [_scalar(i) for i in frame.index], "index_names": [str(x) for x in frame.index.names],
            "columns": [_scalar(c) for c in frame.columns], "columns_name": str(frame.columns.name),
            "values": values}


def data_instances(periods: bool) -> dict:
    """Component data conversions on the meshed network: a snapshot subset, static-only and empty
    attributes, and an array with a missing value converted back to a frame."""
    from pypsa.components.array import _from_xarray

    n = _meshed(periods)
    gens = n.c.generators
    array = gens.da.p_max_pu.copy()
    array[0, 0] = np.nan
    return {
        "subset": _frame(gens._as_dynamic("p_max_pu", n.snapshots[3:9])),
        "static": _frame(gens._as_dynamic("marginal_cost", n.snapshots[2:5])),
        "empty": _frame(n.c.transformers._as_dynamic("s_max_pu")),
        "missing": _frame(_from_xarray(array, gens)),
    }


def capex_instance() -> dict:
    """Installed capex per investment period on the solved two-period meshed network."""
    n = _meshed(True)
    n.c.generators.static["build_year"] = 2020
    n.c.generators.static["lifetime"] = 40
    n.investment_period_weightings.loc[:, "objective"] = [1.0, 0.5]
    n.optimize(multi_investment_periods=True, solver_name="highs")
    return _frame(n.statistics.installed_capex())


def instance_records() -> dict:
    """Every instance a base comparison holds a submission to, or why it cannot be produced."""
    jobs = {"secant-single": lambda: secant_record(False),
            "secant-periods": lambda: secant_record(True),
            "data-single": lambda: data_instances(False),
            "data-periods": lambda: data_instances(True),
            "capex-periods": capex_instance}
    out = {}
    for key, job in jobs.items():
        try:
            out[key] = job()
        except Exception as error:
            out[key] = {"error": f"{type(error).__name__}: {error}"[:300]}
    return out


def frame_differences(base: dict, sub: dict) -> list[str]:
    if "error" in sub:
        return [sub["error"]]
    found = [f"{key} {sub[key]} differs from base {base[key]}"[:300]
             for key in ("index", "index_names", "columns", "columns_name") if sub[key] != base[key]]
    if found:
        return found
    for row, (b, s) in enumerate(zip(base["values"], sub["values"])):
        for x, y in zip(b, s):
            if (x is None) != (y is None) or (x is not None and not _close(x, y)):
                return [f"row {row} is {s}, base {b}"[:300]]
    return []


def instance_differences(base: dict, sub: dict) -> list[str]:
    """How an instance record differs from the base record."""
    if "error" in base:
        return [f"the base produced no record: {base['error']}"]
    if "error" in sub:
        return [sub["error"]]
    if base.get("rows") is not None:
        return model_differences(base, sub)
    if base.get("values") is not None:
        return frame_differences(base, sub)
    return [f"{key}: {problem}" for key in base for problem in frame_differences(base[key], sub.get(key, {"error": "missing"}))]


# ---------------------------------------------------------------------------------------------
# Expressions against statistics at the solution

BUS_CARRIER = {"groupby": ["carrier", "bus_carrier"]}
# (expression, statistic, shared arguments, expression sign): supply and withdrawal clip
# coefficients, which reproduces the statistics' clip only for components that cannot reverse,
# and the transmission expression reports the bus-side contribution of the branch flow.
AG_PAIRS = {
    "capex": ("capex", "capex", {}, 1),
    "capacity": ("capacity", "optimal_capacity", {}, 1),
    "opex": ("opex", "opex", {}, 1),
    "curtailment": ("curtailment", "curtailment", {}, 1),
    "supply": ("supply", "supply", {"components": ["Generator"], **BUS_CARRIER}, 1),
    "withdrawal": ("withdrawal", "withdrawal", {"components": ["Load"], **BUS_CARRIER}, 1),
    "energy_balance": ("energy_balance", "energy_balance", BUS_CARRIER, 1),
    "transmission": ("transmission", "transmission", {}, -1),
}
AG_STATIC = ("capex", "capacity")
AG_GROUPBY = {"carrier": "carrier", "bus+carrier": ["bus", "carrier"], "name+bus+carrier": ["name", "bus", "carrier"],
              "carrier+bus_carrier": ["carrier", "bus_carrier"], "none": False}
AG_TIME = {"sum": "sum", "mean": "mean", "none": False}
AG_FILTERS = {"bus_carrier=AC": {"bus_carrier": "AC"}, "carrier=AC": {"carrier": "AC"}, "nice_names": {"nice_names": True}}
AG_KINDS = ("single", "multi", "subset")
# Links whose efficiency varies by snapshot, on the two-period network, for the transmission pair.
AG_DYNAMIC_EFFICIENCY = ("dynamic",)
AG_PERIODIC = ("multi", *AG_DYNAMIC_EFFICIENCY)
# Statistics cover every snapshot, the curtailment expression only the optimised ones.
AG_SKIPPED = {("subset", "curtailment")}


def ag_cases() -> list[str]:
    """Every pair under every grouping, time aggregation, and filter, on each solved network."""
    cases = []
    for kind in AG_KINDS:
        for pair in AG_PAIRS:
            if (kind, pair) in AG_SKIPPED:
                continue
            times = ["default"] if pair in AG_STATIC else ["default", *AG_TIME]
            for groupby in ["default", *AG_GROUPBY]:
                cases += [f"{kind}|{pair}|groupby={groupby}|time={t}" for t in times]
            cases += [f"{kind}|{pair}|filter={f}" for f in AG_FILTERS]
    for kind in AG_DYNAMIC_EFFICIENCY:
        cases += [f"{kind}|transmission|groupby={g}|time={t}" for g in ["default", *AG_GROUPBY]
                  for t in ["default", *AG_TIME]]
    return cases


def ag_network(kind: str):
    n = _meshed(kind in AG_PERIODIC)
    if kind in AG_DYNAMIC_EFFICIENCY:
        links = n.c.links.static.index
        steps = np.arange(len(n.snapshots))[:, None]
        n.c.links.dynamic["efficiency"] = pd.DataFrame(0.8 + 0.15 * np.cos(steps + np.arange(len(links))),
                                                       index=n.snapshots, columns=links)
    if kind in AG_PERIODIC:
        n.optimize(multi_investment_periods=True, include_objective_constant=False, solver_name="highs")
    elif kind == "subset":
        n.optimize(snapshots=n.snapshots[:3], include_objective_constant=False, solver_name="highs")
    else:
        n.optimize(include_objective_constant=False, solver_name="highs")
    return n


def _as_series(obj) -> pd.Series:
    if isinstance(obj, pd.DataFrame):
        series = obj.stack()
    elif isinstance(obj, pd.Series):
        series = obj
    elif not obj.solution.dims:
        series = pd.Series(dtype=float)
    else:
        series = obj.solution.to_series()
    if isinstance(series.index, pd.MultiIndex):
        series = series.reorder_levels(sorted(series.index.names))
    return series.sort_index()


AG_FILTER_KEYS = {"filter"}


def ag_arguments(case: str) -> tuple[str, str, dict, int]:
    kind, pair, *rest = case.split("|")
    expr, stat, shared, sign = AG_PAIRS[pair]
    call = dict(shared)
    for part in rest:
        key, value = part.split("=", 1)
        if key == "groupby" and value != "default":
            call["groupby"] = AG_GROUPBY[value]
        elif key == "time" and value != "default":
            call["groupby_time"] = AG_TIME[value]
        elif key in AG_FILTER_KEYS:
            call.update(AG_FILTERS[value])
    return expr, stat, call, sign


def ag_statistic(n, case: str):
    _, stat, call, _ = ag_arguments(case)
    return getattr(n.statistics, stat)(**call)


def ag_problem(n, case: str) -> str | None:
    """Why the expression, evaluated at the solution, disagrees with the statistic, or None."""
    expr_name, _, call, sign = ag_arguments(case)
    expr = getattr(n.optimize.expressions, expr_name)(**call)
    stat = ag_statistic(n, case)
    if call.get("groupby") is False and isinstance(stat.index, pd.MultiIndex) and "component" in stat.index.names:
        stat = stat.droplevel("component")  # ungrouped expressions are indexed by name alone
    left, right = sign * _as_series(expr), _as_series(stat)
    if left.empty and right.empty:
        return None
    index = left.index.union(right.index)
    left, right = left.reindex(index).fillna(0.0), right.reindex(index).fillna(0.0)
    if np.allclose(left, right, atol=AG_TOL):
        return None
    return f"largest difference {float(np.max(np.abs(left - right))):.6g}"

# ---------------------------------------------------------------------------------------------
# Public API inventory


ADDRESS = re.compile(r" at 0x[0-9a-fA-F]+")


def _parameters(obj):
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return None
    return [[p.name, p.kind.name, None if p.default is inspect.Parameter.empty else ADDRESS.sub("", repr(p.default))]
            for p in signature.parameters.values()]


def _public(name: str) -> bool:
    return not name.startswith("_")


def api_inventory() -> dict[str, dict]:
    """Every public function and public method of every public class, per pypsa module."""
    import pypsa

    warnings.simplefilter("ignore")
    modules = {"pypsa": pypsa}
    for info in pkgutil.walk_packages(pypsa.__path__, "pypsa."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        try:
            modules[info.name] = importlib.import_module(info.name)
        except Exception:  # a module the base cannot import has no inventory to keep
            continue
    out: dict[str, dict] = {}
    for modname, module in sorted(modules.items()):
        entries: dict[str, list] = {}
        for name, obj in vars(module).items():
            if not _public(name) or getattr(obj, "__module__", None) != modname:
                continue
            if inspect.isfunction(obj):
                entries[name] = _parameters(obj)
            elif inspect.isclass(obj):
                for attr, member in vars(obj).items():
                    if not _public(attr):
                        continue
                    if isinstance(member, (staticmethod, classmethod)):
                        member = member.__func__
                    if inspect.isfunction(member):
                        entries[f"{name}.{attr}"] = _parameters(member)
        out[modname] = entries
    return out


def api_problems(base: dict, sub: dict | None) -> list[str]:
    """Breaks of the base public API: removed callables or incompatible parameter lists."""
    if sub is None:
        return ["the module no longer imports"]
    found = []
    for name, params in base.items():
        if name not in sub:
            found.append(f"{name} was removed")
            continue
        now = sub[name]
        if params is None or now is None:
            continue
        old_names = [p[0] for p in params]
        kept = [p for p in now if p[0] in old_names]
        if kept != params:
            found.append(f"{name} parameters changed from {params} to {now}")
            continue
        positional = ("POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD")
        for i, p in enumerate(params):
            if p[1] in positional and now.index(p) != i:
                found.append(f"{name} moved parameter {p[0]}")
                break
        for p in now:
            if p[0] not in old_names and p[2] is None and p[1] not in ("VAR_POSITIONAL", "VAR_KEYWORD"):
                found.append(f"{name} gained the required parameter {p[0]}")
    return found


def module_inventory(modname: str) -> dict | None:
    try:
        importlib.import_module(modname)
    except Exception:
        return None
    return api_inventory().get(modname)


# ---------------------------------------------------------------------------------------------
# Command line


def _attempt(name: str) -> dict:
    """A solved record, or why the base cannot build it, which leaves that network unchecked."""
    try:
        return solved_record(name)
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"[:500]}


def _facts(semantics: str) -> dict:
    """Everything the legacy-semantics requirement checks read, from one child process."""
    _semantics(semantics)
    out: dict = {"semantics": semantics, "models": {}, "representation": {}, "instance_representation": {}}
    for name in (*MULTI_PERIOD, *SINGLE_PERIOD):
        out["models"][name] = _attempt(name)
    for value in (None, "auto", "flat", "multiindex"):
        try:
            out["representation"][str(value)] = representation_facts(value)
        except Exception as error:
            out["representation"][str(value)] = {"error": f"{type(error).__name__}: {error}"}
        out["instance_representation"][str(value)] = instance_representation(value)
    out["instances"] = instance_records()
    return out


def main(argv: list[str]) -> None:
    warnings.simplefilter("ignore")
    import logging

    logging.disable(logging.WARNING)
    command = COMMANDS.get(argv[0]) if argv else None
    if command is None:
        raise SystemExit(__doc__)
    command(*argv[1:])


def _fixtures_command(directory: str) -> None:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    _semantics("legacy")
    legacy = {name: _attempt(name) for name in (*MULTI_PERIOD, *SINGLE_PERIOD)}
    legacy["instances"] = instance_records()
    api = api_inventory()
    for stem, body in (("forge_legacy", legacy), ("forge_api", api)):
        (target / f"{stem}.json").write_text(json.dumps(body, sort_keys=True, indent=0) + "\n")


def _survey_command(semantics: str, output: str) -> None:
    _semantics(semantics)
    out = {}
    nets = {}
    for case in ag_cases():
        kind = case.split("|")[0]
        try:
            n = nets.setdefault(kind, ag_network(kind))
        except Exception as error:
            out[case] = f"network {type(error).__name__}: {error}"[:200]
            continue
        try:
            ag_statistic(n, case)
        except Exception as error:
            out[case] = f"statistic {type(error).__name__}: {error}"[:200]
            continue
        try:
            problem = ag_problem(n, case)
            out[case] = "agree" if problem is None else f"differ {problem}"
        except Exception as error:
            out[case] = f"expression {type(error).__name__}: {error}"[:200]
    Path(output).write_text(json.dumps(out, indent=0, sort_keys=True))


def _facts_command(semantics: str, output: str) -> None:
    Path(output).write_text(json.dumps(_facts(semantics), sort_keys=True))


COMMANDS = {"fixtures": _fixtures_command, "ag-survey": _survey_command, "facts": _facts_command}


if __spec__ is None:
    main(sys.argv[1:])
