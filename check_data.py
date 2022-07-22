import sys, traceback
from datamodel.input.data import InputDataFile
from datautilities import utils, validation

# run this either as:
#
#   python check_data.py
#
# or as:
#
#   python check_data.py <problem_data_file_name>
#

# this file is OK
data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707.json'
summary_file = 'summary.txt'
data_errors_file = 'data_errors.txt'
ignored_errors_file = 'ignored_errors.txt'

# these files have multiple errors. The data reader should find and report all (maybe only some?)
# of them by raising an exception.
#data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707_read_errors.json'
#data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707_model_errors.json'

# error message starts with, e.g.:
# pydantic.error_wrappers.ValidationError: 9 validation errors for InputDataFile

    
if __name__ == '__main__':

    if len(sys.argv) > 1:
        problem_data_file_name = sys.argv[1]
    else:
        problem_data_file_name = data_file
    validation.check(problem_data_file_name, summary_file, data_errors_file, ignored_errors_file)
