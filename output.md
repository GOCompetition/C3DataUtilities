# Output of check_data.py

The main script check_data.py produces the following outputs, among others

| summary.json | summary |
| summary.csv | JSON version |

summary.json contains a summary with various information about the problem file and the solution file being checked by check_data.py. summary.csv is a CSV-formatted version of summary.json where the column names are created by concatenating the corresponding keys in the JSON version.

The summary is a dictionary structured as follows:

summary
* problem
* solution
* evaluation
