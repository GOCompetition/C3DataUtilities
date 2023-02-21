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
* todo
