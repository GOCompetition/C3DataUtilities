# Output of check_data.py

The main script check_data.py produces the following outputs, among others

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
* "sum_sd_t_su":
* "sum_sd_t_sd":
* "viol_sd_t_d_up_min":
* "viol_sd_t_d_dn_min":
* "viol_sd_max_startup_constr":
* "sum_sd_t_z_on":
* "sum_sd_t_z_su":
* "sum_sd_t_z_sd":
* "sum_sd_t_z_sus":
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
* "sum_acl_t_u_su":
* "sum_acl_t_u_sd":
* "sum_xfr_t_u_su":
* "sum_xfr_t_u_sd":
* "sum_acl_t_z_su":
* "sum_acl_t_z_sd":
* "sum_xfr_t_z_su":
* "sum_xfr_t_z_sd":
* "sum_acl_t_z_s":
* "viol_acl_t_s_max":
* "sum_xfr_t_z_s":
* "viol_xfr_t_s_max":
* "viol_bus_t_p_balance_max":
* "viol_bus_t_p_balance_min":
* "sum_bus_t_z_p":
* "viol_bus_t_q_balance_max":
* "viol_bus_t_q_balance_min":
* "sum_bus_t_z_q":
* "sum_pr_t_z_p":
* "sum_cs_t_z_p":
* "sum_sd_t_z_rgu":
* "sum_sd_t_z_rgd":
* "sum_sd_t_z_scr":
* "sum_sd_t_z_nsc":
* "sum_sd_t_z_rru_on":
* "sum_sd_t_z_rrd_on":
* "sum_sd_t_z_rru_off":
* "sum_sd_t_z_rrd_off":
* "sum_sd_t_z_qru":
* "sum_sd_t_z_qrd":
* "viol_prz_t_p_rgu_balance":
* "viol_prz_t_p_rgd_balance":
* "viol_prz_t_p_scr_balance":
* "viol_prz_t_p_nsc_balance":
* "viol_prz_t_p_rru_balance":
* "viol_prz_t_p_rrd_balance":
* "viol_qrz_t_q_qru_balance":
* "viol_qrz_t_q_qrd_balance":
* "sum_prz_t_z_rgu":
* "sum_prz_t_z_rgd":
* "sum_prz_t_z_scr":
* "sum_prz_t_z_nsc":
* "sum_prz_t_z_rru":
* "sum_prz_t_z_rrd":
* "sum_qrz_t_z_qru":
* "sum_qrz_t_z_qrd":
* "viol_t_connected_base":
* "viol_t_connected_ctg":
* "info_i_i_t_disconnected_base":
* "info_i_i_k_t_disconnected_ctg":
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
* "z":
* "z_max_energy":
* "z_min_energy":
* "z_base":
* "z_value":
* "total_switches":
* "z_cost":
* "z_penalty":
* "z_k_worst_case":
* "z_k_average_case":
* "feas":
* "infeas":
* "time_run":
* "time_connectedness":
* "time_post_contingency":
* "pass":
* "error_diagnostics":
* "infeas_diagnostics":

