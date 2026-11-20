# Solver restarts use the wrong state after discontinuities and model changes

The repository at `/app/pybamm` is the PyBaMM monorepo. The `pybamm` package under `packages/pybamm` is installed in editable mode with its dependencies, and the `pybammsolvers` extension (the IDAKLU solver) has been built from the repository's own source. There is no network access.

PyBaMM splits an integration into segments at discontinuities, such as `pybamm.t > pybamm.InputParameter("t_switch")` or the resets of `pybamm.Modulo(pybamm.t, period)`, and continues from an earlier solution when `step()` is called or when an experiment moves to a new model. Several of these restarts start from the wrong state or the wrong sensitivities, or do not happen at all.

## What goes wrong

1. After a discontinuity whose time depends on an input, `IDAKLUSolver.solve` starts each later segment from the initial conditions. A model with input-timed current steps ends at the wrong voltage, and a DAE model can fail with `IDA_BAD_K`. An integer `t_eval` raises "t_eval must have at least 2 entries". Two input sets whose discontinuity falls on a `t_eval` point raise "Discontinuity events occur at different times". `t_interp` or `store_first_last=True` raise errors about `t_interp` values.
2. With several input sets, if the first stops on an event before such a discontinuity, the others silently end at the discontinuity with termination "final time".
3. `step()` never stops at discontinuities. Stepping across an input-timed jump in an algebraic state fails with `IDA_ERR_FAIL`, and a `Modulo` reset inside a step is integrated across.
4. When an experiment changes model between steps, or a solve continues from a `starting_solution`, the sensitivities are wrong, and a voltage sensitivity can be off by orders of magnitude. With an input-dependent scale, such as an input maximum particle concentration, the solve raises `AttributeError`.
5. Continuing an `["a"]` solve with `step()` for `["b"]` on a new solver silently returns the sensitivities to `a` as those to `b`.
6. `step()` raises `RuntimeError` when `calculate_sensitivities` changes between calls, so an experiment `Simulation` cannot be re-solved without sensitivities after a solve with them.
7. Each set-up of the same model, such as after changing `calculate_sensitivities`, adds another copy of each discontinuity event to `model.events`.

## Expected behaviour

- Solving across discontinuities continues every input set from the state and sensitivities it reached at the discontinuity, algebraic states included, with or without consistent initialisation (the IDAKLU `calc_ic` option). An input set that stops on an event keeps its own solution and termination. Integer `t_eval`, discontinuities on `t_eval` points, `t_interp`, and `store_first_last=True` all work.
- `step()` stops at discontinuities, constant-time ones and `Modulo` resets included, as `solve()` does, and their times appear in the solution. `t_interp` and `store_first_last=True` work with it, including for a step that starts within a float of a discontinuity.
- `pybamm.Modulo(pybamm.t, period)` with an input period resets where the period puts it for each input set. An infinite period never resets, and a time-dependent period is rejected with an error.
- Sensitivities carried across a change of model are the derivatives of the new model's states, including with an input-dependent reference and scale, and for a state whose starting value depends on an input directly.
- A continued `step()` never reuses another input's sensitivities. If a continued solution from a solver without `output_variables` has no sensitivities for a requested input, it raises `pybamm.SolverError` naming those inputs.
- Changing `calculate_sensitivities` between `step()` calls works as it does for `solve()`. A `RuntimeError` for using a solver with a second model leaves `model.calculate_sensitivities` unchanged.
- However often a model is set up, `model.events` holds each discontinuity event once.

Existing behaviour must stay as it is:
- `Simulation` keeps both experiment model modes, `experiment_model_mode="legacy"` and `"unified"`, with the same results.
- The unified experiment's step inputs keep their names, such as "Experiment step index", "Experiment step value", and "start time", alongside the user's own inputs (for example "user input").
- Experiment steps keep their termination reasons, such as "experiment time limit reached", "experiment voltage limit reached", "experiment capacity limit reached", and "Event exceeded in initial conditions", and their messages, such as "Step time must be >0", "Nominal capacity changed", "Rest for padding", and "no experiment is attached to the simulation".
- Variables keep their names, such as "Minimum voltage [V]".
- Expression-tree objects still accept a domain name such as "domain".
- A solver's `on_extrapolation` still accepts settings such as "ignore".

Other code calls `BaseSolver._get_discontinuity_start_end_indices(model, y0, inputs, t_eval)`, which must keep its signature and keep returning `(start_indices, end_indices, t_eval)`. It must not modify the caller's `t_eval`, and it must accept an integer `t_eval`.

Fix this in the library source under `/app/pybamm/packages/pybamm/src/pybamm`, and keep every other behaviour of PyBaMM unchanged. Only your changes under `/app/pybamm/packages/pybamm/src/pybamm` are kept; changes elsewhere in the repository, including to `pybammsolvers` and the configuration, are discarded.
