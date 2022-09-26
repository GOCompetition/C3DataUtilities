# C3DataUtilities

* Read problem data
* Check problem data formatting and properties
* Read solution data
* Check solution data formatting and properties
* Evaluate solution to problem, i.e. constraint feasibility, objective value, properties of interest

# Installation

Currently relies on https://github.com/Smart-DS/GO-3-data-model.git. You can obtain this by:

```
git clone https://github.com/Smart-DS/GO-3-data-model.git
```

Follow installation directions in the Bid-DS-data-model repository, primarily:

```
cd GO-3-data-model
pip install -e .
```

Next clone this repository:

```
git clone https://github.com/GOCompetition/C3DataUtilities.git
```

Then install with pip:

```
cd C3DataUtilities
pip install -e .
```

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
