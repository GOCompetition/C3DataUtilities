# Output of check_data.py

The main script check_data.py produces the following outputs, among others

* summary.json : contains a summary with various information about the problem file and the solution file being checked by check_data.py.
* summary.csv : is a CSV-formatted version of summary.json where the column names are created by concatenating the corresponding keys in the JSON version.

The summary is a dictionary, and we give selected elements of the structure below, focusing on those that are most likely to be useful.
New fields may be added from time to time, but generally fields will not be removed.

summary
* problem_data_file : problem filename passed as an argument to the script
* solution_data_file : solution filename passed as an argument to the script
* git_info : information on the repository containing the script, e.g. commit date
* problem : information about the problem, including formatting correctness and errors
* solution : information about the solution, including formatting correctness and errors
* evaluation : information about the solution evaluation, including feasibility of constraints, objective terms, and errors

problem
* general
* "violation costs"
* "num buses" :
* "num ac lines" :
* "num dc lines" :
* "num transformers" :
* "num shunts" :

"violation costs"
* "p_bus_vio_cost":
* "q_bus_vio_cost":
* "s_vio_cost":
* "e_vio_cost":

solution
*

evaluation
*
