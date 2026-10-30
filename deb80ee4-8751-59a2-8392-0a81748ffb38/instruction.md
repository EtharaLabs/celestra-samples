# Run PyPSA's multi-period optimisation under linopy's v1 semantics

The repository at `/app/pypsa` is PyPSA, installed in editable mode with its dependencies, including linopy 0.10.0 and the HiGHS solver. There is no network access; the example networks that `pypsa.examples` loads are already in the local cache. The environment sets `LINOPY_SEMANTICS=v1`, and the test suite's `conftest.py` reads it to switch linopy to its v1 arithmetic semantics.

linopy's v1 semantics change two rules that PyPSA's model building relies on. A `pandas.MultiIndex` can no longer be a dimension coordinate, and arithmetic between objects that share a dimension requires their coordinates on that dimension to align exactly. A network with investment periods has a `(period, timestep)` MultiIndex as its snapshots. Under v1, building and optimising such a network fails, and so do the optimisation expressions (`n.optimize.expressions`), the statistics computed from a solved model, and links with transport delays across investment periods. Single-period networks and the legacy semantics keep working.

Make multi-period networks build, solve, and report under v1 with the same results as under the legacy semantics:
- Add the option `pypsa.options.optimization.model_snapshot_index`, settable with `pypsa.option_context("optimization.model_snapshot_index", value)`. Its value is `"auto"` (the default), `"flat"`, or `"multiindex"`, and any other value raises `ValueError` when a model is built. It decides how a newly built model labels the snapshots of a multi-period network. `"flat"` uses a flat `snapshot` dimension whose labels are the `(period, timestep)` tuples, equal to `n.snapshots.to_flat_index().rename("snapshot")`, with the period and timestep kept as auxiliary coordinates. `"multiindex"` keeps the MultiIndex. `"auto"` means `"flat"` while linopy's v1 semantics are active (`linopy.options["semantics"] == "v1"`) and `"multiindex"` otherwise.
- Use that representation consistently: for the model's snapshot parameters (`n.model.parameters.snapshots`), for the component data the model reads (for example `n.c.generators.da.p_max_pu` after `n.optimize.create_model()`), and for the snapshots passed to an `extra_functionality` callback.
- Keep everything that depends on investment periods per period, including cyclic and non-cyclic storage and stores, ramp limits, per-period primary-energy and operational limits, transport delays, and the weighting of each period in the objective.
- Keep `n.optimize.expressions` and `n.statistics` consistent with each other and with the objective under both representations.

The tests also exercise existing behaviour that must stay as it is:
- Solves still report the condition "optimal", and optimised capacities land in `p_nom_opt`.
- Components keep their names, such as "Generator", "StorageUnit", "Link", and "Process", and printed expressions keep their term labels, such as "Generator-p" and "Link-p_nom", with piecewise terms labelled "piecewise".
- Global constraints of type "expansion_limit" keep working.
- Statistics keep their names, such as "capacity" and "energy_balance", and keep grouping by "bus_carrier", "carrier", "country", and "scenario", including for carriers such as "rural heat".
- The piecewise helpers keep their naming. A piecewise output variable such as "y_static" is reported with its `_static` or dynamic suffix, which the tests read by stripping a `y_var_` prefix from their fixture names. A piecewise definition that cannot be applied still logs "Skipping piecewise constraint.".
- A transport delay that is not a whole number of snapshot durations still logs a warning containing "does not align".

Fix this in the library source under `/app/pypsa/pypsa`, keeping every other behaviour of PyPSA unchanged. Your work is graded from the final contents of `/app/pypsa/pypsa` only, against tests that are not in this environment. Changes elsewhere in the repository, including to its tests and configuration, are not graded.
