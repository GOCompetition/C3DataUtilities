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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "problem_opt", nargs="?",
        help="The problem file that we are checking - optional positional argument for backward compatibility, do not use with -p")
    group.add_argument("-p", "--problem", help="The problem file that we are checking")
    parser.add_argument("-s", "--solution", help="The solution file that we are checking")
    parser.add_argument(
        "-c", "--configuration",
        default=None,
        help="Configuration file to override default configuration parameter values")
    parser.add_argument("-m", "--summary_csv", default=summary_csv_file, help="Summary output file - CSV format", )
    parser.add_argument("-j", "--summary_json", default=summary_json_file, help="Summary output file - JSON format", )
    parser.add_argument("-d", "--data_errors", default=data_errors_file, help="Data errors output file")
    parser.add_argument("-i", "--ignored_errors", default=ignored_errors_file, help="Ignored errors output file")
    parser.add_argument("-u", "--solution_errors", default=solution_errors_file, help="Solution errors output file")
    parser.add_argument("-r", "--scrubbed_problem", default=None, help="File path name to write scrubbed problem file")

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
            validation.scrub_data(problem, default_config, args.configuration, args.scrubbed_problem)
        else:
            validation.check_data(problem, args.solution, default_config, args.configuration, args.summary_csv, args.summary_json, args.data_errors, args.ignored_errors, args.solution_errors)
