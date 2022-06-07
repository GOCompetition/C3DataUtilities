# C3DataUtilities

* Read problem data
* Read problem solution
* Evaluate problem solution

🚧🚧 Under Construction 🚧🚧

Currently relies on https://github.com/Smart-DS/Bid-DS-data-model. Follow installation directions in that repository, primarily:

```
cd Bid-DS-data-model
pip install -e .
```

The validators branch (https://github.com/Smart-DS/Bid-DS-data-model/tree/validators) contains the most complete set of input data checking, but this will later be merged into main. Once Bid-DS-data-model is installed, one can do:

```
python read_problem_data_test.py <problem_data_file_name>
```

This will read a problem data file, check it against properties specified in the data format document and problem formulation document, and print out some information about the problem dimensions. If the data fails any of the required properties, an exception will be raised to report this. It is not guaranteed that all failed properties will be reported. If there is at least one failure, then at least one failure will be reported.

The operative part of read_problem_data_test.py for data checking is:

```
from datamodel.input.data import InputDataFile
problem_data = InputDataFile.load(problem_data_file_name)
```

If no errors are raised, then problem_data is a Pydantic model object containing the problem data.
