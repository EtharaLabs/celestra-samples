"""GENERATED SECTION. DO NOT HAND-EDIT. Compiled from the bundle grounding."""

import json
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

GATE = {'negate': False,
 'nodes': ['packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_discharge_rest_charge',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_drive_cycle',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_drive_cycle_duration',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_gitt',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_infeasible',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperiments::test_rest_discharge_rest',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_all_empty_solution_errors',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_batch_cross_cycle_equivalent',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_build_experiment_step_inputs_uses_expected_step_index',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_build_for_experiment_legacy_processes_each_unique_step',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_built_models_and_state_mappers_independent_of_cycle_count',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_cycle_summary_variables',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_decode_combined_step_termination_handles_none_events_and_missing_t_event',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_decode_combined_step_termination_returns_original_when_no_events_match',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_distinct_control_types_with_same_value_yield_distinct_models',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_custom_steps',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_custom_termination',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_start_time_identical_steps',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_start_time_starting_solution',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_state_mapper_has_full_state_size_for_2d_current_collector',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_experiment_state_mappers_built',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_inputs',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_inputs_with_initial_soc',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_non_unified_model_jacobian_is_plain_casadi',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_padding_rest_model',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_processed_variable_sensitivities_ignore_experiment_input',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_repeated_solves_refresh_initial_soc[legacy]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_repeated_solves_refresh_initial_soc[unified]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_event_driven_experiment_unified_matches_legacy',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_breaks_early_error',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_breaks_early_infeasible',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_cccv_solvers',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_drive_cycle',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_drive_cycle_experiment',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_half_cell',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_infeasible_time',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_lead_acid',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_multiple_times',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_output_variable_time_integrals',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_output_variables_repeated_step',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_skip_steps',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_temperature_switching_unified',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_capacity',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_time_h',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_time_min',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_time_s',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_time_with_starting_solution_at_limit',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_termination_voltage',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_experiment_with_pbar',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_mixed_control_experiment_unified_matches_legacy',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_mixed_control_experiment_unified_single_model',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_multi_termination_step_unified_matches_legacy',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_start_time_experiment',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_start_time_experiment_forced_unified',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_start_time_experiment_legacy_builds_padding_rest_mappers',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_run_unified_resistance_branch_is_safe_when_inactive_at_zero_current',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_save_at_cycles',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_all_explicit_defaults_to_legacy_model',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_all_explicit_uses_unified_model_with_dae_solver',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_can_force_legacy_experiment_models',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_differential_custom_step_falls_back_to_legacy',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_unified_mode_rejects_all_explicit_ode_solver',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_unified_mode_rejects_differential_custom_step',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_set_up_unified_preserves_voltage_safety_events',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_setup_experiment_string_or_list',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_changing_capacity_crate_steps[legacy]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_changing_capacity_crate_steps[unified]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_logging_with_capacity_change[legacy]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_logging_with_capacity_change[unified]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_multiple_cycles_with_capacity_change[legacy]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_simulation_multiple_cycles_with_capacity_change[unified]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_skip_ok',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_skip_ok_with_multiple_infeasible_terminations_in_unified_model',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_skipped_step_continuous',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_solve_with_sensitivities_and_experiment[DFN]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_solve_with_sensitivities_and_experiment[SPM]',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_solve_with_sensitivities_true_excludes_all_internal_inputs',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_solve_with_sensitivity_list_ignores_internal_experiment_input',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_starting_solution',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_active_branch_independent_of_other_modes',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_allows_drive_cycle_and_algebraic_implicit',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_ambient_temperature_scalar_value',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_aot_compile_bounded_in_unique_steps',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_builds_exactly_one_model_and_solver',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_cc_per_step_current_parses',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_collapses_every_control_kind_by_value',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_constant_current_steps_collapse_to_one_branch',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_control_row_jacobian_is_sparse',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_drive_cycle_matches_legacy',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_model_mode_validation_and_blockers',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_model_switching_size_independent_of_cycle_count',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_records_switching_control_variable_not_voltage',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_switch_matches_legacy_voltage',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_switch_top_functions_flat_in_unique_steps',
           'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_unified_voltage_per_step_matches_legacy',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_addition',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_addition_numpy_array',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_advanced_binary_simplifications',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_binary_operator',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_binary_operator_domains',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_binary_simplifications',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_binary_simplifications_concatenations',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_diff',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_eq',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_equality',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_heaviside',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_hypot',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_inner',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_inner_simplifications',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_minimum_maximum',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_modulo',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_number_overloading',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_power',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_printing',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_sigmoid',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_smooth_minus_plus',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_softminus_softplus',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_source',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_source_error',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_sparse_divide',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_sparse_multiply',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_t_discon_error',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_to_equation',
           'packages/pybamm/tests/unit/test_expression_tree/test_binary_operators.py::TestBinaryOperators::test_to_json',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_additional_inputs_provided',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_base_solver_init',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_block_symbolic_inputs',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_convert_to_casadi_format',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_discontinuity_events_different_times_error',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_discretise_model',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_events_fail_on_initialisation_multiple_input_params[None]',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_events_fail_on_initialisation_multiple_input_params[casadi]',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_events_fail_on_initialisation_multiple_input_params[python]',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_extrapolation_warnings',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_fail_consistent_initialization',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_find_consistent_initialization',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_inputs_step',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_integrate_single_error',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_multiple_models_error',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_multiprocess_context',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_nonmonotonic_teval',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_ode_solver_fail_with_dae',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_on_extrapolation_and_on_failure_settings',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_one_process_solves_input_sets_without_a_pool',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_root_method_init',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_root_method_takes_the_tightest_entry_of_a_per_state_atol',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_sensitivities',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_single_input_set_uses_the_first_initial_state',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_solution_time_length_fail',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_step_or_solve_empty_model',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_step_restarts_sensitivities_from_output_variables',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolver::test_t_eval_none',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_next_to_t_eval_point[at]',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_with_infinite_period[constant]',
           'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_starting_just_before_input_dependent_discontinuity',
           'packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_a_differentially_controlled_step'],
 'relation': 'any_fail'}
GUARDS = [{'negate': False, 'relation': 'steering_present'}]
ITEMS = {'F01': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuities_with_python_format'],
         'relation': 'all_pass'},
 'F04': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_at_non_positive_time[negative]'],
         'relation': 'all_pass'},
 'F05': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_at_non_positive_time[zero]'],
         'relation': 'all_pass'},
 'F06': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_next_to_t_eval_point[above]'],
         'relation': 'all_pass'},
 'F07': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_next_to_t_eval_point[below]'],
         'relation': 'all_pass'},
 'F08': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_one_float_after_t_eval_start'],
         'relation': 'all_pass'},
 'F09': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_rejects_t_interp_outside_t_eval[t_interp0-greater '
                   'than the smallest]'],
         'relation': 'all_pass'},
 'F10': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_rejects_t_interp_outside_t_eval[t_interp1-less '
                   'than the greatest]'],
         'relation': 'all_pass'},
 'F19': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_running_input_sets[0]'],
         'relation': 'all_pass'},
 'F20': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_running_input_sets[1]'],
         'relation': 'all_pass'},
 'F21': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_times_match_casadi[modulo]'],
         'relation': 'all_pass'},
 'F22': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_times_match_casadi[switch]'],
         'relation': 'all_pass'},
 'F23': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_with_t_interp[False]'],
         'relation': 'all_pass'},
 'F24': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_with_t_interp[True]'],
         'relation': 'all_pass'},
 'F25': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_within_one_float_of_t_eval_end'],
         'relation': 'all_pass'},
 'F26': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_before_zero[constant]'],
         'relation': 'all_pass'},
 'F27': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_before_zero[input]'],
         'relation': 'all_pass'},
 'F31': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_with_infinite_period[input]'],
         'relation': 'all_pass'},
 'F32': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_with_input_period'],
         'relation': 'all_pass'},
 'F33': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_with_time_dependent_period_raises'],
         'relation': 'all_pass'},
 'F34': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_one_float_before_modulo_reset'],
         'relation': 'all_pass'},
 'F35': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_stops_at_every_modulo_reset[constant]'],
         'relation': 'all_pass'},
 'F36': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_stops_at_every_modulo_reset[input]'],
         'relation': 'all_pass'},
 'F37': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_after_event_keeps_sensitivities_continuous_at_discontinuity'],
         'relation': 'all_pass'},
 'F38': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_after_event_matches_unsplit_step'],
         'relation': 'all_pass'},
 'F39': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_restarts_at_input_dependent_discontinuity'],
         'relation': 'all_pass'},
 'F45': {'negate': False,
         'nodes': ['packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[reference-True]'],
         'relation': 'all_pass'},
 'F46': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_maps_sensitivities[constant-False]'],
         'relation': 'all_pass'},
 'F48': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_maps_sensitivities[input-False]'],
         'relation': 'all_pass'},
 'F49': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_maps_sensitivities[input-True]'],
         'relation': 'all_pass'},
 'F50': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_rejects_missing_sensitivities[fewer]'],
         'relation': 'all_pass'},
 'F51': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_rejects_missing_sensitivities[none]'],
         'relation': 'all_pass'},
 'F52': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_starting_solution_rejects_changed_sensitivities[fewer]'],
         'relation': 'all_pass'},
 'F53': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_starting_solution_rejects_changed_sensitivities[more]'],
         'relation': 'all_pass'},
 'F54': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_starting_solution_rejects_changed_sensitivities[none]'],
         'relation': 'all_pass'},
 'F55': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_saved_step_rejects_changed_sensitivities[fewer]'],
         'relation': 'all_pass'},
 'F56': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_saved_step_rejects_changed_sensitivities[none]'],
         'relation': 'all_pass'},
 'F57': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_rejects_restart_without_requested_sensitivities[False]'],
         'relation': 'all_pass'},
 'F58': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_rejects_restart_without_requested_sensitivities[True]'],
         'relation': 'all_pass'},
 'F59': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_seeds_sensitivities_by_name'],
         'relation': 'all_pass'},
 'F62': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_second_model_error_keeps_sensitivity_setting[solve]'],
         'relation': 'all_pass'},
 'F63': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_second_model_error_keeps_sensitivity_setting[step]'],
         'relation': 'all_pass'},
 'F65': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_set_up_adds_discontinuity_events_once'],
         'relation': 'all_pass'},
 'F66': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_algebraic_sensitivities_without_calc_ic'],
         'relation': 'all_pass'},
 'M01': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuities_within_one_float[1]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuities_within_one_float[2]'],
         'relation': 'pass_share'},
 'M02': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[array-False-False]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[array-False-True]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[integer_list-False-False]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[integer_list-False-True]'],
         'relation': 'pass_share'},
 'M03': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[array-True-False]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[array-True-True]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[integer_list-True-False]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_input_dependent_discontinuity_restarts_each_input_set[integer_list-True-True]'],
         'relation': 'pass_share'},
 'M04': {'negate': False,
         'nodes': ['packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[electrolyte_scale-False]',
                   'packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[particle_scale-False]'],
         'relation': 'pass_share'},
 'M05': {'negate': False,
         'nodes': ['packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[electrolyte_scale-True]',
                   'packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[particle_scale-True]'],
         'relation': 'pass_share'},
 'M06': {'negate': False,
         'nodes': ['packages/pybamm/tests/integration/test_experiments.py::TestExperimentSensitivities::test_sensitivities_across_model_changes[reference-False]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_to_new_model_maps_sensitivities[constant-True]'],
         'relation': 'pass_share'},
 'M07': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_restarts_where_fmod_resets[10]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_restarts_where_fmod_resets[5]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_modulo_restarts_where_fmod_resets[9]'],
         'relation': 'pass_share'},
 'M08': {'negate': False,
         'nodes': ['packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_resolve_with_changed_sensitivities[legacy]',
                   'packages/pybamm/tests/unit/test_experiments/test_simulation_with_experiment.py::TestSimulationExperiment::test_resolve_with_changed_sensitivities[unified]',
                   'packages/pybamm/tests/unit/test_solvers/test_base_solver.py::TestBaseSolverSensitivityRestarts::test_step_after_changing_sensitivities'],
         'relation': 'pass_share'}}

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
    if data.get("refused") or _relation(GATE, data) or any(_relation(guard, data) for guard in GUARDS):
        return 0.0
    spec = ITEMS[item]
    value = _relation(spec, data)
    return 1.0 - value if spec["negate"] else value


rk.rubric_item('F01', weight=1.0, name='F01')
rk.rubric_item('M01', weight=1.0, name='M01')
rk.rubric_item('F04', weight=1.0, name='F04')
rk.rubric_item('F05', weight=1.0, name='F05')
rk.rubric_item('F06', weight=1.0, name='F06')
rk.rubric_item('F07', weight=1.0, name='F07')
rk.rubric_item('F08', weight=1.0, name='F08')
rk.rubric_item('F09', weight=1.0, name='F09')
rk.rubric_item('F10', weight=1.0, name='F10')
rk.rubric_item('M02', weight=1.0, name='M02')
rk.rubric_item('M03', weight=1.0, name='M03')
rk.rubric_item('F19', weight=1.0, name='F19')
rk.rubric_item('F20', weight=1.0, name='F20')
rk.rubric_item('F21', weight=1.0, name='F21')
rk.rubric_item('F22', weight=1.0, name='F22')
rk.rubric_item('F23', weight=1.0, name='F23')
rk.rubric_item('F24', weight=1.0, name='F24')
rk.rubric_item('F25', weight=1.0, name='F25')
rk.rubric_item('F26', weight=1.0, name='F26')
rk.rubric_item('F27', weight=1.0, name='F27')
rk.rubric_item('M07', weight=1.0, name='M07')
rk.rubric_item('F31', weight=1.0, name='F31')
rk.rubric_item('F32', weight=1.0, name='F32')
rk.rubric_item('F33', weight=1.0, name='F33')
rk.rubric_item('F34', weight=1.0, name='F34')
rk.rubric_item('F35', weight=1.0, name='F35')
rk.rubric_item('F36', weight=1.0, name='F36')
rk.rubric_item('F37', weight=1.0, name='F37')
rk.rubric_item('F38', weight=1.0, name='F38')
rk.rubric_item('F39', weight=1.0, name='F39')
rk.rubric_item('M04', weight=1.0, name='M04')
rk.rubric_item('M05', weight=1.0, name='M05')
rk.rubric_item('M06', weight=1.0, name='M06')
rk.rubric_item('F45', weight=1.0, name='F45')
rk.rubric_item('F46', weight=1.0, name='F46')
rk.rubric_item('F48', weight=1.0, name='F48')
rk.rubric_item('F49', weight=1.0, name='F49')
rk.rubric_item('F50', weight=1.0, name='F50')
rk.rubric_item('F51', weight=1.0, name='F51')
rk.rubric_item('F52', weight=1.0, name='F52')
rk.rubric_item('F53', weight=1.0, name='F53')
rk.rubric_item('F54', weight=1.0, name='F54')
rk.rubric_item('F55', weight=1.0, name='F55')
rk.rubric_item('F56', weight=1.0, name='F56')
rk.rubric_item('F57', weight=1.0, name='F57')
rk.rubric_item('F58', weight=1.0, name='F58')
rk.rubric_item('F59', weight=1.0, name='F59')
rk.rubric_item('M08', weight=1.0, name='M08')
rk.rubric_item('F62', weight=1.0, name='F62')
rk.rubric_item('F63', weight=1.0, name='F63')
rk.rubric_item('F65', weight=1.0, name='F65')
rk.rubric_item('F66', weight=1.0, name='F66')
