'''
check_data.py

python check_data.py [-h, --help]
* display help

python check_data.py <problem_file_name> # positional argument provided for backward compatibility
python check_data.py [-p, --problem] <problem_file_name>
python check_data.py [-p, --problem] <problem_file_name> [-s, --solution] <solution_file_name>
* check a problem file
* check a solution file
* write summary.json, data_errors.txt, ignored_errors.txt, solution_errors.txt
* solution check does not check feasibility of the solution or compute objective
* it is mainly about formatting
'''

import argparse, pathlib
from datautilities import validation, utils

default_config_file = 'config.json'
summary_csv_file = 'summary.csv'
summary_json_file = 'summary.json'
data_errors_file = 'data_errors.txt'
ignored_errors_file = 'ignored_errors.txt'
solution_errors_file = 'solution_errors.txt'

if __name__ == '__main__':

    msg = '\n'.join([
            'check a problem file.',
            'output files',
            '  summary csv',
            '  summary json',
            '  data errors',
            '  ignored errors',
            '  solution errors',
            ])
    parser = argparse.ArgumentParser(description=msg, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # short arguments
    problem_group = parser.add_mutually_exclusive_group()
    problem_group.add_argument(
        "problem_opt", nargs="?",
        help="The problem file that we are checking. This is an optional positional argument for backward compatibility and should not be used in combination with the keyword argument \"--problem\".")
    problem_group.add_argument("-p", "--problem", help="The problem file that we are checking.", default=None)
    parser.add_argument("-s", "--solution", help="The solution file that we are checking. If this argument is supplied, then the solution will be evaluated. Minimal validation will be performed on the problem data in the process of loading it, to save time, since this validation should have been done before considering solutions.", default=None)

    # long arguments - these all have defaults and will not be needed as often as the short parameters
    # and therefore do not have short names
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument("--configuration", default=None, help="Configuration file to override default parameter values. Do not use this argument in combination with \"--parameters\".")
    config_group.add_argument("--parameters", default="{}", help="JSON string containing configuration parameter values to override the defaults. E.g. adding \"--parameters \'{\"do_opt_solves\": false}\'\" to the Python command disables certain data checks that rely on Gurobi to solve an optimization problem. Do not use this argument in combination with \"--configuration\".")
    parser.add_argument("--summary_csv", default=summary_csv_file, help="Summary output file - CSV format", )
    parser.add_argument("--summary_json", default=summary_json_file, help="Summary output file - JSON format", )
    parser.add_argument("--data_errors", default=data_errors_file, help="Data errors output file")
    parser.add_argument("--ignored_errors", default=ignored_errors_file, help="Ignored errors output file")
    parser.add_argument("--solution_errors", default=solution_errors_file, help="Solution errors output file")
    parser.add_argument("--pop_solution", default=None, help="Prior Operating Point (POP) solution file. If this argument is supplied, then the problem data will be read and validated thoroughly, then a POP solution will be created and written to a solution file.")
    parser.add_argument("--scrubbed_problem", default=None, help="File path name to write scrubbed problem file. If this argument is supplied, then the problem data will be loaded, scrubbed, and rewritten. Scrubbing involves anonymizing the UIDs and removing optional data fields. Limited validation is performed on the original data in the process of reading the original data file.")

    args = parser.parse_args()

    print('args:')
    print(args)

    default_config=str(pathlib.Path(utils.get_C3DataUtilities_dir(), default_config_file))

    if args.problem is not None:
        problem = args.problem
    else:
        problem = args.problem_opt

    if problem is not None:
        if args.scrubbed_problem is not None: # if scrubbing, ignore other arguments
            validation.scrub_data(problem, default_config, args.configuration, args.parameters, args.scrubbed_problem)
        else:
            validation.check_data(problem, args.solution, default_config, args.configuration, args.parameters, args.summary_csv, args.summary_json, args.data_errors, args.ignored_errors, args.solution_errors, args.pop_solution)
