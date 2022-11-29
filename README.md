# C3DataUtilities

* Read problem data
* Check problem data formatting and properties
* Read solution data
* Check solution data formatting and properties
* Evaluate solution to problem, i.e. constraint feasibility, objective value, properties of interest

# Installation

Clone this repository:

```
git clone https://github.com/GOCompetition/C3DataUtilities.git
```

Then install with pip:

```
cd C3DataUtilities
pip install -e .
```

The pip command uses setup.py, which ensures other needed Python packages are installed.
C3DataUtilities uses GO-3-data-model, which is another package that was developed for the GO Competition
and can be obtained from PyPI (https://pypi.org/project/GO-3-data-model/) or GitHub (https://github.com/Smart-DS/GO-3-data-model).
The C3DataUtilities pip command obtains GO-3-data-model from PyPI.

# Checking problem data formatting and properties

Once Bid-DS-data-model is installed, one can do:

```
cd C3DataUtilities
python check_data.py <problem_data_file_name>
```

This will read a problem data file, check it against properties specified in the data format document and problem formulation document, and print out some information about the problem dimensions. If the data fails any of the required properties, an exception will be raised to report this. It is not guaranteed that all failed properties will be reported. If there is at least one failure, then it is guaranteed that at least one failure will be reported. Data errors, other kinds of errors, and summary output are written to files. A complete description of the outputs and other ways of calling ```check_data.py``` can be found in the help:

```
python check_data.py --help
```

# Branches

This repository will have at least the following two branches:
* main
* dev

```main``` will include only those checks that the publicly available problem instances pass.
```dev``` may include checks that publicly available instances are failing.
In general the competition platform will use ```dev```.
