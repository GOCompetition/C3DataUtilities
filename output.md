# Output of check_data.py

The main script check_data.py produces the following outputs, among others.

* summary.json: contains a summary with various information about the problem file and the solution file being checked by check_data.py.
* summary.csv: a CSV-formatted version of summary.json where the column names are created by concatenating the corresponding keys in the JSON version.

The summary is a dictionary, and we give selected elements of the structure below, focusing on those that are most likely to be useful.
New fields may be added from time to time, but generally fields will not be removed. The units are those of the formulation document.

summary
* problem_data_file: problem filename passed as an argument to the script
* solution_data_file: solution filename passed as an argument to the script
* git_info: information on the repository containing the script, e.g. commit date
* problem: information about the problem, including formatting correctness and errors
* solution: information about the solution, including formatting correctness and errors
* evaluation: information about the solution evaluation, including feasibility of constraints, objective terms, and errors

problem
* general: General information about the problem
* "violation costs": Soft constraint violation penalty coefficients
* "num buses": Number of buses
* "num ac lines": Number of AC lines
* "num dc lines": Number of DC lines
* "num transformers": Number of transformers
* "num shunts": Number of shunts
* "num simple dispatchable devices": Number of simple dispatchable devcieces
* "num producing devices": Number of producing devices
* "num consuming devices": Number of consuming devices
* "num real power reserve zones": Number of real power reserve zones
* "num reactive power reserve zones": Number of reactive power reserve zones
* "num intervals": Number of time intervals
* "num contingencies": Number of contingencies
* "total duration": Total duration of the model time horizon
* "interval durations": List of time interval durations
* "error_diagnostics": Error messages if any errors were encountered in reading and checking the problem file
* "pass": 1 if no errors encountered in reading and checking the problem file

"violation costs"
* "p_bus_vio_cost": Penalty coefficient on bus real power imbalance
* "q_bus_vio_cost": Penalty coefficient on bus reactive power imbalance
* "s_vio_cost": Penalty coefficient on branch overload
* "e_vio_cost": Penalty coefficient on multi-interval energy constraints

solution
* "error_diagnostics": Error messages if any errors were encountered in reading and checking the solution file
* "pass": 1 if no errors encountered in reading and checking the solution file

evaluation
* "viol_sd_t_u_on_max": 
* "viol_sd_t_u_on_min":
* "sum_sd_t_su": Total of u_su variables over all simple dispatchable (producing or consuming) devices.
* "sum_sd_t_sd": Total of u_sd variables over all simple dispatchable (producing or consuming) devices.
* "viol_sd_t_d_up_min":
* "viol_sd_t_d_dn_min":
* "viol_sd_max_startup_constr":
* "sum_sd_t_z_on": Total "on-cost" over all simple dispatchable (producing or consuming) devices.
* "sum_sd_t_z_su": Total startup cost over all simple dispatchable (producing or consuming) devices.
* "sum_sd_t_z_sd": Total shutdown cost over all simple dispatchable (producing or consuming) devices.
* "sum_sd_t_z_sus": Total downtime-dependent startup cost adjustment over all simple dispatchable (producing or consuming) devices.
* "viol_bus_t_v_max":
* "viol_bus_t_v_min":
* "viol_sh_t_u_st_max":
* "viol_sh_t_u_st_min":
* "viol_dcl_t_p_max":
* "viol_dcl_t_p_min":
* "viol_dcl_t_q_fr_max":
* "viol_dcl_t_q_fr_min":
* "viol_dcl_t_q_to_max":
* "viol_dcl_t_q_to_min":
* "viol_xfr_t_tau_max":
* "viol_xfr_t_tau_min":
* "viol_xfr_t_phi_max":
* "viol_xfr_t_phi_min":
* "viol_acl_t_u_su_max":
* "viol_acl_t_u_sd_max":
* "viol_xfr_t_u_su_max":
* "viol_xfr_t_u_sd_max":
* "sum_acl_t_u_su": Total of u_su (closing a circuit) variables over all AC lines.
* "sum_acl_t_u_sd": Total of u_sd (opening a circuit) variables over all AC lines.
* "sum_xfr_t_u_su": Total of u_su (closing a circuit) variables over all transformers.
* "sum_xfr_t_u_sd": Total of u_sd (opening a circuit) variables over all transformers.
* "sum_acl_t_z_su": Total startup (closing a circuit) cost over all AC lines.
* "sum_acl_t_z_sd": Total shutdown (opening a circuit) cost over all AC lines.
* "sum_xfr_t_z_su": Total startup (closing a circuit) cost over all Transformers.
* "sum_xfr_t_z_sd": Total shutdown (opening a circuit) cost over all transformers.
* "sum_acl_t_z_s": Total flow limit overload cost over all AC lines.
* "viol_acl_t_s_max":
* "sum_xfr_t_z_s": Total flow limit overload cost over all transformers.
* "viol_xfr_t_s_max":
* "viol_bus_t_p_balance_max":
* "viol_bus_t_p_balance_min":
* "sum_bus_t_z_p": Total real power imbalance cost over all buses.
* "viol_bus_t_q_balance_max":
* "viol_bus_t_q_balance_min":
* "sum_bus_t_z_q": Total reactive power imbalance cost over all buses.
* "sum_pr_t_z_p": Total energy cost over all producing devices.
* "sum_cs_t_z_p": Total energy value over all consuming devices.
* "sum_sd_t_z_rgu": Total reserve procurement cost from all simple dispatchable devices for regulation up.
* "sum_sd_t_z_rgd": Total reserve procurement cost from all simple dispatchable devices for regulation up.
* "sum_sd_t_z_scr": Total reserve procurement cost from all simple dispatchable devices for regulation up.
* "sum_sd_t_z_nsc": Total reserve procurement cost from all simple dispatchable devices for regulation up.
* "sum_sd_t_z_rru_on": Total reserve procurement cost from all simple dispatchable devices for ramp up reserve when online.
* "sum_sd_t_z_rrd_on": Total reserve procurement cost from all simple dispatchable devices for ramp down reserve when online.
* "sum_sd_t_z_rru_off": Total reserve procurement cost from all simple dispatchable devices for ramp up reserve when offline.
* "sum_sd_t_z_rrd_off": Total reserve procurement cost from all simple dispatchable devices for ramp down reserve when offline.
* "sum_sd_t_z_qru": Total reserve procurement cost from all simple dispatchable devices for reactive power reserve up.
* "sum_sd_t_z_qrd": Total reserve procurement cost from all simple dispatchable devices for reactive power reserve down.
* "viol_prz_t_p_rgu_balance":
* "viol_prz_t_p_rgd_balance":
* "viol_prz_t_p_scr_balance":
* "viol_prz_t_p_nsc_balance":
* "viol_prz_t_p_rru_balance":
* "viol_prz_t_p_rrd_balance":
* "viol_qrz_t_q_qru_balance":
* "viol_qrz_t_q_qrd_balance":
* "sum_prz_t_z_rgu": Total reserve shortfall penalty for regulation up.
* "sum_prz_t_z_rgd": Total reserve shortfall penalty for regulation down.
* "sum_prz_t_z_scr": Total reserve shortfall penalty for synchronized reserve.
* "sum_prz_t_z_nsc": Total reserve shortfall penalty for non-synchronized reserve.
* "sum_prz_t_z_rru": Total reserve shortfall penalty for ramping reserve up.
* "sum_prz_t_z_rrd": Total reserve shortfall penalty for ramping reserve down.
* "sum_qrz_t_z_qru": Total reserve shortfall penalty for reactive power reserve up.
* "sum_qrz_t_z_qrd": Total reserve shortfall penalty for reactive power reserve down.
* "viol_t_connected_base":
* "viol_t_connected_ctg":
* "info_i_i_t_disconnected_base": Information on checking that the base case online in-service bus-branch network is connected in every time interval.
* "info_i_i_k_t_disconnected_ctg": Information on checking that the post-contingency online in-service bus-branch network is connected in every time interval and every contingency.
* "viol_pr_t_p_on_max":
* "viol_cs_t_p_on_max":
* "viol_pr_t_p_off_max":
* "viol_cs_t_p_off_max":
* "viol_pr_t_p_on_min":
* "viol_cs_t_p_on_min":
* "viol_pr_t_p_off_min":
* "viol_cs_t_p_off_min":
* "viol_pr_t_q_max":
* "viol_pr_t_q_min":
* "viol_cs_t_q_max":
* "viol_cs_t_q_min":
* "viol_pr_t_q_p_max":
* "viol_pr_t_q_p_min":
* "viol_cs_t_q_p_max":
* "viol_cs_t_q_p_min":
* "viol_sd_t_p_ramp_dn_max":
* "viol_sd_t_p_ramp_up_max":
* "viol_sd_max_energy_constr":
* "viol_sd_min_energy_constr":
* "viol_sd_t_p_rgu_nonneg":
* "viol_sd_t_p_rgd_nonneg":
* "viol_sd_t_p_scr_nonneg":
* "viol_sd_t_p_nsc_nonneg":
* "viol_sd_t_p_rru_on_nonneg":
* "viol_sd_t_p_rru_off_nonneg":
* "viol_sd_t_p_rrd_on_nonneg":
* "viol_sd_t_p_rrd_off_nonneg":
* "viol_sd_t_q_qru_nonneg":
* "viol_sd_t_q_qrd_nonneg":
* "viol_sd_t_p_rgu_max":
* "viol_sd_t_p_rgd_max":
* "viol_sd_t_p_scr_max":
* "viol_sd_t_p_nsc_max":
* "viol_sd_t_p_rru_on_max":
* "viol_sd_t_p_rrd_on_max":
* "viol_sd_t_p_rru_off_max":
* "viol_sd_t_p_rrd_off_max":
* "viol_acl_acl_t_s_max_ctg":
* "viol_xfr_acl_t_s_max_ctg":
* "viol_acl_dcl_t_s_max_ctg":
* "viol_xfr_dcl_t_s_max_ctg":
* "viol_acl_xfr_t_s_max_ctg":
* "viol_xfr_xfr_t_s_max_ctg":
* "z": Total penalized market surplus objective value.
* "z_max_energy": Contribution to "z_penalty" from multi-interval maximum energy constraint violations.
* "z_min_energy": Contribution to "z_penalty" from multi-interval minimum energy constraint violations.
* "z_base": Contribution to "z" from variables and constraints corresponding to the base (i.e. pre-contingency or no contingency) case
* "z_value": Contribution to "z_base" from producing device energy value
* "total_switches": Total of u_su and u_sd variables over AC branch devices
* "z_cost": Contribution to "z_base" from consuming device energy cost
* "z_penalty": Contribution to "z_base" from soft constraint penalties, i.e. bus real and reactive power imbalance, real and reactive reserve zone shortfall, AC branch overload, and multi-interval energy constraint violations.
* "z_k_worst_case":
* "z_k_average_case":
* "feas": 1 if the solution is feasible.
* "infeas": 1 if the solution is infeasible.
* "time_run": Run time in solution evaluation.
* "time_connectedness": Run time in evaluating connectedness constraints.
* "time_post_contingency": Run time in evaluating post-contingency constraints.
* "pass": 1 if no errors were encountered in the solution evaluation procedure.
* "error_diagnostics": Error messages encountered by the solution evaluation procedure.
* "infeas_diagnostics": Information about constraint violations resulting in a determination that the solution is infeasible.

"infeas_diagnostics": A dictionary of constraint violations resulting in infeasibility. An empty dictionary if no such constraint violations are detected.
* "viol_\*": The value corresponding to a "viol_\*" entry of "evaluation" with "val" > 0.

"viol_\*": Information the constraint violation of a particular type of constraints. The type is indicated in the "\*" text, where possible referencing specific equations from the formulation.
* "val": The violation value of the most violated individual constraint of this type. Equal to max(0, f(x)) for a constraint of the form f(x) <= 0. Equal to None if the constraint array is empty.
* "idx": The multi-dimensional index of the most violated individual constraint of this type. Equal to None if the constraint array is empty.

"idx": A multi-dimensional index of an array of individual constraints indexed by multiple 1-dimensional index sets
* "0": The 0th entry in the multi-dimensional index
* "1": The 1th entry in the multi-dimensional index
* ...

